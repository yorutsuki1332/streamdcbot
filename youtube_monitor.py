import asyncio
import logging
import os
from datetime import datetime, timedelta
import aiohttp
import json
from typing import Optional, Dict, Any

class YouTubeMonitor:
    """Monitors YouTube channel for new videos and sends Discord notifications"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        self.channel_id = None  # Will be set by user
        self.last_video_id = None
        self.check_interval = 300  # Check every 5 minutes
        self.guild_id = 1288838226362105868  # 澪夜聯邦 server ID
        self.notification_channel_id = 1392034508747837520  # Specific channel for notifications
        # Auto-set the Violette channel only if API key exists
        if self.api_key:
            asyncio.create_task(self._auto_setup_violette_channel())
        
    async def set_youtube_channel(self, channel_url_or_id: str) -> bool:
        """Set the YouTube channel to monitor"""
        try:
            # Extract channel ID from URL or use direct ID
            if 'youtube.com' in channel_url_or_id:
                if '/channel/' in channel_url_or_id:
                    self.channel_id = channel_url_or_id.split('/channel/')[-1].split('?')[0]
                elif '/@' in channel_url_or_id:
                    # Handle @username format - need to resolve to channel ID
                    username = channel_url_or_id.split('/@')[-1].split('?')[0]
                    self.channel_id = await self._resolve_username_to_channel_id(username)
                else:
                    return False
            else:
                self.channel_id = channel_url_or_id
                
            if self.channel_id:
                self.logger.info(f"YouTube channel set to: {self.channel_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error setting YouTube channel: {e}")
            return False
    
    async def _auto_setup_violette_channel(self):
        """Automatically set up Violette's YouTube channel"""
        await asyncio.sleep(2)  # Wait for bot to be ready
        if self.api_key:
            await self.set_youtube_channel("https://www.youtube.com/@violetteyaaa")
            self.logger.info("Auto-configured Violette's YouTube channel")
    
    async def _resolve_username_to_channel_id(self, username: str) -> Optional[str]:
        """Resolve @username to channel ID using YouTube API"""
        if not self.api_key:
            return None
            
        url = f"https://www.googleapis.com/youtube/v3/channels"
        params = {
            'part': 'id',
            'forUsername': username,
            'key': self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    if 'items' in data and data['items']:
                        return data['items'][0]['id']
        except Exception as e:
            self.logger.error(f"Error resolving username: {e}")
        return None
    
    async def check_for_new_videos(self):
        """Check for new videos on the monitored channel"""
        if not self.api_key or not self.channel_id:
            return
            
        url = f"https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'channelId': self.channel_id,
            'order': 'date',
            'maxResults': 1,
            'type': 'video',
            'key': self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if 'items' in data and data['items']:
                        latest_video = data['items'][0]
                        video_id = latest_video['id']['videoId']
                        
                        # Check if this is a new video
                        if video_id != self.last_video_id:
                            self.last_video_id = video_id
                            await self._send_notification(latest_video)
                            
        except Exception as e:
            self.logger.error(f"Error checking for new videos: {e}")
    
    async def _send_notification(self, video_data: Dict[str, Any]):
        """Send Discord notification for new video"""
        try:
            guild = self.bot.get_guild(self.guild_id)
            if not guild:
                return
                
            # Get the specific notification channel
            notification_channel = guild.get_channel(self.notification_channel_id)
            if not notification_channel:
                self.logger.error(f"Notification channel {self.notification_channel_id} not found")
                return
                
            if not notification_channel.permissions_for(guild.me).send_messages:
                self.logger.error(f"No permission to send messages in channel {notification_channel.name}")
                return
                
            video_title = video_data['snippet']['title']
            video_url = f"https://www.youtube.com/watch?v={video_data['id']['videoId']}"
            
            message = (
                "@everyone\n"
                "Violette's new video highlight has just been released!!! Let's watch\n"
                "澪夜的新片發布了！快來看看吧！\n\n"
                f"**{video_title}**\n"
                f"{video_url}"
            )
            
            await notification_channel.send(message)
            self.logger.info(f"Sent notification for new video: {video_title}")
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
    
    async def start_monitoring(self):
        """Start the YouTube monitoring loop"""
        if not self.api_key:
            self.logger.error("YouTube API key not found. Please set YOUTUBE_API_KEY environment variable.")
            return
            
        if not self.channel_id:
            self.logger.warning("YouTube channel not set. Use !set_youtube_channel command first.")
            return
            
        self.logger.info("Starting YouTube monitoring...")
        
        while True:
            try:
                await self.check_for_new_videos()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying