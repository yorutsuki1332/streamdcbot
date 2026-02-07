import discord
import asyncio
import logging
from typing import Optional, List, Dict
from urllib.parse import urlparse, parse_qs
import yt_dlp
import aiohttp
from datetime import datetime, timedelta

class YouTubeAudio(discord.PCMVolumeTransformer):
    """Audio source for YouTube videos"""
    
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('webpage_url')
        self.duration = data.get('duration', 0)
        
    @classmethod
    async def from_url(cls, url: str, *, loop=None):
        """Create audio source from YouTube URL"""
        loop = loop or asyncio.get_event_loop()
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                data = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(url, download=False)
                )
                
            filename = data['url']
            return cls(
                discord.FFmpegPCMAudio(filename, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn"),
                data=data
            )
        except Exception as e:
            raise Exception(f"Failed to load audio: {str(e)}")

class MusicPlayer:
    """Manages music playback in Discord voice channels"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.queue: Dict[int, List[Dict]] = {}  # guild_id -> list of songs
        self.current_playing: Dict[int, Optional[Dict]] = {}  # guild_id -> current song
        self.voice_clients: Dict[int, discord.VoiceClient] = {}  # guild_id -> voice client
        self.is_looping: Dict[int, bool] = {}  # guild_id -> loop status
        self.volume: Dict[int, float] = {}  # guild_id -> volume level (0.0-1.0)
        self.start_time: Dict[int, datetime] = {}  # guild_id -> when current song started
        
    async def get_queue(self, guild_id: int) -> List[Dict]:
        """Get the queue for a guild"""
        return self.queue.get(guild_id, [])
    
    async def add_to_queue(self, guild_id: int, url: str) -> Dict:
        """Add video/playlist to queue"""
        if guild_id not in self.queue:
            self.queue[guild_id] = []
        
        # Check if it's a playlist
        if self._is_playlist(url):
            songs = await self._extract_playlist(url)
        else:
            songs = await self._extract_video(url)
        
        if songs:
            self.queue[guild_id].extend(songs)
            return {'success': True, 'count': len(songs), 'songs': songs}
        
        return {'success': False, 'error': 'No videos found'}
    
    async def play_next(self, guild_id: int, voice_client: discord.VoiceClient):
        """Play next song in queue"""
        if guild_id not in self.queue or not self.queue[guild_id]:
            # Queue empty
            if guild_id in self.current_playing:
                self.current_playing[guild_id] = None
            return None
        
        # If looping and current song exists, play it again
        if self.is_looping.get(guild_id, False) and self.current_playing.get(guild_id):
            song = self.current_playing[guild_id]
        else:
            song = self.queue[guild_id].pop(0)
        
        self.current_playing[guild_id] = song
        self.start_time[guild_id] = datetime.now()
        
        try:
            audio = await YouTubeAudio.from_url(song['url'])
            volume = self.volume.get(guild_id, 0.5)
            audio.volume = volume
            
            voice_client.play(
                audio,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next(guild_id, voice_client),
                    self.bot.loop
                )
            )
            return song
        except Exception as e:
            self.logger.error(f"Error playing {song['title']}: {e}")
            # Try next song
            return await self.play_next(guild_id, voice_client)
    
    async def stop(self, guild_id: int):
        """Stop playback and disconnect"""
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            del self.voice_clients[guild_id]
        
        self.queue[guild_id] = []
        self.current_playing[guild_id] = None
    
    async def pause(self, guild_id: int):
        """Pause playback"""
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if voice_client.is_playing():
                voice_client.pause()
                return True
        return False
    
    async def resume(self, guild_id: int):
        """Resume playback"""
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if voice_client.is_paused():
                voice_client.resume()
                return True
        return False
    
    async def skip(self, guild_id: int):
        """Skip to next song"""
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if voice_client.is_playing():
                voice_client.stop()
                return True
        return False
    
    async def toggle_loop(self, guild_id: int) -> bool:
        """Toggle loop mode"""
        self.is_looping[guild_id] = not self.is_looping.get(guild_id, False)
        return self.is_looping[guild_id]
    
    def _is_playlist(self, url: str) -> bool:
        """Check if URL is a YouTube playlist"""
        parsed = urlparse(url)
        if 'youtube.com' in parsed.netloc:
            query = parse_qs(parsed.query)
            return 'list' in query
        elif 'youtu.be' in parsed.netloc:
            return False
        return False
    
    async def _extract_video(self, url: str) -> List[Dict]:
        """Extract single video info"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
        }
        
        try:
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(url, download=False)
                )
            
            return [{
                'title': info.get('title'),
                'url': info.get('webpage_url'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail')
            }]
        except Exception as e:
            self.logger.error(f"Error extracting video: {e}")
            return []
    
    async def _extract_playlist(self, url: str) -> List[Dict]:
        """Extract playlist videos"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        try:
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(url, download=False)
                )
            
            songs = []
            if 'entries' in info:
                for entry in info['entries'][:50]:  # Limit to 50 songs
                    songs.append({
                        'title': entry.get('title'),
                        'url': f"https://www.youtube.com/watch?v={entry['id']}",
                        'duration': 0,
                        'thumbnail': None
                    })
            
            return songs
        except Exception as e:
            self.logger.error(f"Error extracting playlist: {e}")
            return []
    
    def format_duration(self, seconds: int) -> str:
        """Format duration in MM:SS or HH:MM:SS"""
        if seconds == 0:
            return "0:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
    
    async def set_volume(self, guild_id: int, volume: float) -> bool:
        """Set playback volume (0.0-1.0)"""
        if not 0.0 <= volume <= 1.0:
            return False
        
        self.volume[guild_id] = volume
        
        # Update current playing audio if exists
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if voice_client.is_playing():
                if hasattr(voice_client.source, 'volume'):
                    voice_client.source.volume = volume
        
        return True
    
    def get_volume(self, guild_id: int) -> float:
        """Get current volume (0-100)"""
        return self.volume.get(guild_id, 0.5) * 100
    
    def get_now_playing_progress(self, guild_id: int) -> Optional[Dict]:
        """Get current song progress info"""
        song = self.current_playing.get(guild_id)
        if not song or guild_id not in self.start_time:
            return None
        
        elapsed = (datetime.now() - self.start_time[guild_id]).total_seconds()
        duration = song.get('duration', 0)
        
        return {
            'title': song['title'],
            'elapsed': int(elapsed),
            'duration': duration,
            'progress': min(100, int((elapsed / duration * 100)) if duration > 0 else 0)
        }
    
    async def search_and_play(self, guild_id: int, query: str, voice_client: discord.VoiceClient) -> Optional[Dict]:
        """Search YouTube and play first result"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch1',
            'noplaylist': True,
        }
        
        try:
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(query, download=False)
                )
            
            song = {
                'title': info.get('title'),
                'url': info.get('webpage_url'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail')
            }
            
            self.current_playing[guild_id] = song
            self.start_time[guild_id] = datetime.now()
            
            audio = await YouTubeAudio.from_url(song['url'])
            volume = self.volume.get(guild_id, 0.5)
            audio.volume = volume
            
            voice_client.play(
                audio,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next(guild_id, voice_client),
                    self.bot.loop
                )
            )
            
            return song
        except Exception as e:
            self.logger.error(f"Error searching: {e}")
            return None
    
    async def get_lyrics(self, song_title: str) -> Optional[str]:
        """Fetch lyrics from Genius API (basic implementation)"""
        try:
            # This is a simplified version - in production you'd want to use Genius API
            # For now we'll return a placeholder
            search_url = f"https://www.genius.com/api/search?q={song_title.replace(' ', '+')}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        # Basic implementation - in production use proper Genius API key
                        return f"Lyrics for '{song_title}' would be fetched from Genius API (requires API key)"
            return None
        except Exception as e:
            self.logger.error(f"Error fetching lyrics: {e}")
            return None
