import discord
from discord.ext import commands
import logging
from utils import parse_emoji, get_role_by_name_or_id

async def setup_commands(bot):
    """Set up all bot commands"""
    
    @bot.command(name='setup_reaction_role', aliases=['srr'])
    @commands.has_permissions(administrator=True)
    async def setup_reaction_role(ctx, message_id: int, emoji: str, role: str):
        """
        Set up a reaction role for a specific message.
        
        Usage: !setup_reaction_role <message_id> <emoji> <role>
        Example: !setup_reaction_role 123456789 🎮 Gamer
        """
        try:
            # Get the message
            message = await ctx.channel.fetch_message(message_id)
            if not message:
                await ctx.send("❌ Message not found in this channel!")
                return
                
        except discord.NotFound:
            await ctx.send("❌ Message not found!")
            return
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to access that message!")
            return
            
        # Parse emoji
        parsed_emoji = parse_emoji(emoji)
        if not parsed_emoji:
            await ctx.send("❌ Invalid emoji format!")
            return
            
        # Get role
        target_role = get_role_by_name_or_id(ctx.guild, role)
        if not target_role:
            await ctx.send(f"❌ Role '{role}' not found!")
            return
            
        # Check bot permissions
        if target_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot assign this role - it's higher than my highest role!")
            return
            
        # Add the reaction role configuration
        config_added = await bot.config_manager.add_reaction_role(
            ctx.guild.id,
            ctx.channel.id,
            message_id,
            parsed_emoji,
            target_role.id
        )
        
        if config_added:
            # Add the reaction to the message
            try:
                await message.add_reaction(parsed_emoji)
                await ctx.send(f"✅ Reaction role set up successfully!\n"
                             f"Users can now react with {emoji} to get the **{target_role.name}** role.")
            except discord.Forbidden:
                await ctx.send("❌ I don't have permission to add reactions to that message!")
            except discord.HTTPException:
                await ctx.send("❌ Failed to add reaction to the message!")
        else:
            await ctx.send("❌ This emoji-role combination already exists for this message!")
    
    @bot.command(name='remove_reaction_role', aliases=['rrr'])
    @commands.has_permissions(administrator=True)
    async def remove_reaction_role(ctx, message_id: int, emoji: str):
        """
        Remove a reaction role setup from a message.
        
        Usage: !remove_reaction_role <message_id> <emoji>
        Example: !remove_reaction_role 123456789 🎮
        """
        parsed_emoji = parse_emoji(emoji)
        if not parsed_emoji:
            await ctx.send("❌ Invalid emoji format!")
            return
            
        removed = await bot.config_manager.remove_reaction_role(
            ctx.guild.id,
            ctx.channel.id,
            message_id,
            parsed_emoji
        )
        
        if removed:
            # Try to remove the reaction from the message
            try:
                message = await ctx.channel.fetch_message(message_id)
                await message.clear_reaction(parsed_emoji)
            except:
                pass  # Ignore errors when removing reactions
                
            await ctx.send(f"✅ Reaction role removed for {emoji}")
        else:
            await ctx.send("❌ No reaction role found for that emoji on that message!")
    
    @bot.command(name='list_reaction_roles', aliases=['lrr'])
    @commands.has_permissions(administrator=True)
    async def list_reaction_roles(ctx):
        """List all reaction role setups in this server."""
        configs = await bot.config_manager.get_guild_configs(ctx.guild.id)
        
        if not configs:
            await ctx.send("📝 No reaction roles configured in this server.")
            return
            
        embed = discord.Embed(
            title="Reaction Roles Configuration",
            color=discord.Color.blue()
        )
        
        for config in configs:
            channel = bot.get_channel(config['channel_id'])
            channel_name = channel.name if channel else f"Unknown Channel ({config['channel_id']})"
            
            role = ctx.guild.get_role(config['role_id'])
            role_name = role.name if role else f"Unknown Role ({config['role_id']})"
            
            embed.add_field(
                name=f"Message {config['message_id']}",
                value=f"**Channel:** #{channel_name}\n"
                      f"**Emoji:** {config['emoji']}\n"
                      f"**Role:** {role_name}",
                inline=False
            )
            
        await ctx.send(embed=embed)
    
    @bot.command(name='test_permissions')
    @commands.has_permissions(administrator=True)
    async def test_permissions(ctx):
        """Test bot permissions for reaction role functionality."""
        permissions = ctx.guild.me.guild_permissions
        
        embed = discord.Embed(
            title="Bot Permissions Check",
            color=discord.Color.green() if all([
                permissions.manage_roles,
                permissions.add_reactions,
                permissions.read_message_history
            ]) else discord.Color.red()
        )
        
        embed.add_field(
            name="Manage Roles",
            value="✅ Yes" if permissions.manage_roles else "❌ No",
            inline=True
        )
        embed.add_field(
            name="Add Reactions",
            value="✅ Yes" if permissions.add_reactions else "❌ No",
            inline=True
        )
        embed.add_field(
            name="Read Message History",
            value="✅ Yes" if permissions.read_message_history else "❌ No",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @bot.command(name='set_youtube_channel', aliases=['syc'])
    @commands.has_permissions(administrator=True)
    async def set_youtube_channel(ctx, *, channel_url_or_id: str):
        """
        Set the YouTube channel to monitor for new videos.
        
        Usage: !set_youtube_channel <channel_url_or_id>
        Example: !set_youtube_channel https://www.youtube.com/@username
        Example: !set_youtube_channel UC1234567890
        """
        success = await bot.youtube_monitor.set_youtube_channel(channel_url_or_id)
        if success:
            await ctx.send(f"✅ YouTube channel set successfully! Now monitoring for new videos.")
        else:
            await ctx.send("❌ Failed to set YouTube channel. Please check the URL or channel ID.")
    
    @bot.command(name='youtube_status', aliases=['ys'])
    @commands.has_permissions(administrator=True)
    async def youtube_status(ctx):
        """Check YouTube monitoring status."""
        channel_id = bot.youtube_monitor.channel_id
        api_key_set = bool(bot.youtube_monitor.api_key)
        
        embed = discord.Embed(title="YouTube Monitoring Status", color=discord.Color.blue())
        embed.add_field(name="API Key", value="✅ Set" if api_key_set else "❌ Not Set", inline=True)
        embed.add_field(name="Channel ID", value=channel_id if channel_id else "❌ Not Set", inline=True)
        embed.add_field(name="Monitoring", value="✅ Active" if (api_key_set and channel_id) else "❌ Inactive", inline=True)
        
        if not api_key_set:
            embed.add_field(name="Setup Required", 
                          value="Please set YOUTUBE_API_KEY environment variable", 
                          inline=False)
        
        await ctx.send(embed=embed)
    
    @bot.command(name='welcome_message', aliases=['wm'])
    @commands.has_permissions(administrator=True)
    async def welcome_message(ctx):
        """Send or refresh the welcome message with an entry button."""
        welcome_text = "歡迎來到澪夜聯邦！"
        
        # Check if we have a stored welcome message
        stored_welcome = await bot.config_manager.get_welcome_message(ctx.guild.id)
        if stored_welcome:
            try:
                # Try to delete the existing message
                channel = ctx.guild.get_channel(stored_welcome['channel_id'])
                if channel:
                    message = await channel.fetch_message(stored_welcome['message_id'])
                    await message.delete()
                    await ctx.send("🗑️ Deleted old welcome message.")
            except (discord.NotFound, discord.Forbidden):
                pass  # Message already deleted or can't delete
            
            # Remove from config
            await bot.config_manager.remove_welcome_message(ctx.guild.id)
        
        # Also check for any other welcome messages in current channel
        async for message in ctx.channel.history(limit=50):
            if (message.author == ctx.guild.me and 
                message.content == welcome_text and 
                message.components):  # Has button components
                try:
                    await message.delete()
                except:
                    pass
        
        # Send new welcome message
        view = WelcomeView(bot)
        message = await ctx.send(welcome_text, view=view)
        
        # Store the new message reference
        await bot.config_manager.set_welcome_message(ctx.guild.id, ctx.channel.id, message.id)
        
        await ctx.send("✅ Welcome message sent!")
        
        # Delete the command message after a short delay
        try:
            await ctx.message.delete()
        except:
            pass
    
    # Error handlers for specific commands
    @setup_reaction_role.error
    @remove_reaction_role.error
    @list_reaction_roles.error
    @test_permissions.error
    @set_youtube_channel.error
    @youtube_status.error
    @welcome_message.error
    async def command_error_handler(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need 'Administrator' permission to use this command!")
        else:
            logging.error(f"Command error: {error}")

class WelcomeView(discord.ui.View):
    def __init__(self, bot=None):
        super().__init__(timeout=None)  # No timeout for persistent view
        
        # Use custom emoji if available, otherwise fallback to unicorn
        emoji = '🦄'  # Default fallback
        if bot and hasattr(bot, 'custom_emoji') and bot.custom_emoji:
            emoji = bot.custom_emoji
        
        # Add the button dynamically
        self.add_item(WelcomeButton(emoji))

class WelcomeButton(discord.ui.Button):
    def __init__(self, emoji):
        super().__init__(label='同意入境', style=discord.ButtonStyle.primary, emoji=emoji)
    
    async def callback(self, interaction: discord.Interaction):
        """Handle the agree entry button click"""
        logging.info(f"Button clicked by {interaction.user} in guild {interaction.guild.name} (ID: {interaction.guild.id})")
        
        # Check if this is the correct server (澪夜聯邦)
        if interaction.guild.id == 1288838226362105868:
            # Use specific role ID for 澪夜聯邦 server
            role = interaction.guild.get_role(1392004567524446218)
            logging.info(f"Using specific role ID for 澪夜聯邦 server. Role found: {role}")
        else:
            # Fallback: search by name for other servers
            role = None
            for guild_role in interaction.guild.roles:
                if guild_role.name == '聯邦住民':
                    role = guild_role
                    break
            logging.info(f"Searching by name in other server. Role found: {role}")
        
        if not role:
            await interaction.response.send_message(
                "❌ 找不到'聯邦住民'角色。請聯繫管理員。", 
                ephemeral=True
            )
            return
        
        # Check if user already has the role
        if role in interaction.user.roles:
            await interaction.response.send_message(
                f"您已經是聯邦住民了，{interaction.user.mention}！", 
                ephemeral=True
            )
            return
        
        # Check bot permissions
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "❌ 機器人沒有管理角色的權限。", 
                ephemeral=True
            )
            return
        
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "❌ 機器人無法分配此角色（角色等級過高）。", 
                ephemeral=True
            )
            return
        
        # Assign the role
        try:
            await interaction.user.add_roles(role, reason="Welcome button - 同意入境")
            logging.info(f"Successfully assigned role {role.name} to {interaction.user}")
            await interaction.response.send_message(
                f"歡迎，{interaction.user.mention}！您已成功入境澪夜聯邦並獲得'聯邦住民'身分！", 
                ephemeral=True
            )
        except discord.Forbidden:
            logging.error(f"Forbidden: Cannot assign role {role.name} to {interaction.user}")
            await interaction.response.send_message(
                "❌ 無法分配角色。請檢查機器人權限。", 
                ephemeral=True
            )
        except discord.HTTPException as e:
            logging.error(f"HTTP error assigning role: {e}")
            await interaction.response.send_message(
                f"❌ 分配角色時發生錯誤：{str(e)}", 
                ephemeral=True
            )
# Music player commands
async def setup_music_commands(bot):
    """Set up music player commands"""
    
    @bot.command(name='play', aliases=['p'])
    async def play(ctx, *, url: str):
        """
        Play a YouTube video or playlist.
        
        Usage: !play <YouTube URL or search query>
        Example: !play https://www.youtube.com/watch?v=dQw4w9WgXcQ
        Example: !play lofi hip hop beats
        """
        if not ctx.author.voice:
            await ctx.send("❌ You must be in a voice channel to play music!")
            return
        
        # Connect to voice channel if not already connected
        voice_client = None
        if ctx.guild.id in bot.music_player.voice_clients:
            voice_client = bot.music_player.voice_clients[ctx.guild.id]
        else:
            try:
                voice_client = await ctx.author.voice.channel.connect()
                bot.music_player.voice_clients[ctx.guild.id] = voice_client
            except Exception as e:
                await ctx.send(f"❌ Failed to connect to voice channel: {str(e)}")
                return
        
        # Add to queue
        async with ctx.typing():
            result = await bot.music_player.add_to_queue(ctx.guild.id, url)
        
        if not result['success']:
            await ctx.send(f"❌ {result.get('error', 'Failed to add to queue')}")
            return
        
        # If nothing is playing, start playback
        if not voice_client.is_playing() and not voice_client.is_paused():
            song = await bot.music_player.play_next(ctx.guild.id, voice_client)
            if song:
                embed = discord.Embed(
                    title="🎵 Now Playing",
                    description=f"[{song['title']}]({song['url']})",
                    color=discord.Color.purple()
                )
                if song['duration']:
                    embed.add_field(name="Duration", value=bot.music_player.format_duration(song['duration']))
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="📝 Added to Queue",
                description=f"**{result['count']}** song(s) added",
                color=discord.Color.blue()
            )
            if result['songs']:
                song_list = "\n".join([f"• {s['title']}" for s in result['songs'][:5]])
                if result['count'] > 5:
                    song_list += f"\n... and {result['count'] - 5} more"
                embed.add_field(name="Songs", value=song_list)
            await ctx.send(embed=embed)
    
    @bot.command(name='queue', aliases=['q'])
    async def queue(ctx):
        """Display the current music queue."""
        queue = await bot.music_player.get_queue(ctx.guild.id)
        current = bot.music_player.current_playing.get(ctx.guild.id)
        
        embed = discord.Embed(
            title="🎵 Music Queue",
            color=discord.Color.purple()
        )
        
        if current:
            embed.add_field(
                name="Currently Playing",
                value=f"[{current['title']}]({current['url']})",
                inline=False
            )
        
        if not queue:
            embed.add_field(
                name="Queue",
                value="Queue is empty",
                inline=False
            )
        else:
            queue_text = "\n".join([f"{i+1}. {s['title']}" for i, s in enumerate(queue[:10])])
            if len(queue) > 10:
                queue_text += f"\n... and {len(queue) - 10} more"
            embed.add_field(
                name=f"Queue ({len(queue)} songs)",
                value=queue_text,
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @bot.command(name='skip', aliases=['s'])
    async def skip(ctx):
        """Skip to the next song."""
        if await bot.music_player.skip(ctx.guild.id):
            await ctx.send("⏭️ Skipped to next song!")
        else:
            await ctx.send("❌ No song is currently playing!")
    
    @bot.command(name='pause')
    async def pause(ctx):
        """Pause the current song."""
        if await bot.music_player.pause(ctx.guild.id):
            await ctx.send("⏸️ Music paused!")
        else:
            await ctx.send("❌ No song is currently playing!")
    
    @bot.command(name='resume', aliases=['r'])
    async def resume(ctx):
        """Resume the paused music."""
        if await bot.music_player.resume(ctx.guild.id):
            await ctx.send("▶️ Music resumed!")
        else:
            await ctx.send("❌ No paused music to resume!")
    
    @bot.command(name='stop')
    async def stop(ctx):
        """Stop music and disconnect from voice channel."""
        await bot.music_player.stop(ctx.guild.id)
        await ctx.send("⏹️ Music stopped and disconnected!")
    
    @bot.command(name='loop', aliases=['l'])
    async def loop(ctx):
        """Toggle loop mode."""
        is_looping = await bot.music_player.toggle_loop(ctx.guild.id)
        status = "✅ Loop enabled" if is_looping else "❌ Loop disabled"
        await ctx.send(status)
    
    @bot.command(name='volume', aliases=['vol', 'v'])
    async def volume(ctx, level: int = None):
        """
        Set or view the volume.
        
        Usage: !volume <0-100>
        Example: !volume 50 (sets volume to 50%)
        Example: !volume (shows current volume)
        """
        if level is None:
            current_vol = bot.music_player.get_volume(ctx.guild.id)
            await ctx.send(f"🔊 Current volume: {current_vol:.0f}%")
            return
        
        if not 0 <= level <= 100:
            await ctx.send("❌ Volume must be between 0 and 100!")
            return
        
        if await bot.music_player.set_volume(ctx.guild.id, level / 100):
            await ctx.send(f"🔊 Volume set to {level}%")
        else:
            await ctx.send("❌ Failed to set volume!")
    
    @bot.command(name='now', aliases=['np', 'nowplaying'])
    async def now_playing(ctx):
        """Show current song with progress bar."""
        progress = bot.music_player.get_now_playing_progress(ctx.guild.id)
        
        if not progress:
            await ctx.send("❌ Nothing is currently playing!")
            return
        
        # Create progress bar
        bar_length = 20
        filled = int((progress['progress'] / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        elapsed_str = bot.music_player.format_duration(progress['elapsed'])
        duration_str = bot.music_player.format_duration(progress['duration'])
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[{progress['title']}]",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="Progress",
            value=f"{bar}\n{elapsed_str} / {duration_str}",
            inline=False
        )
        embed.add_field(
            name="Progress %",
            value=f"{progress['progress']}%",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @bot.command(name='lyrics', aliases=['ly'])
    async def lyrics(ctx, *, song_title: str = None):
        """
        Get lyrics for a song.
        
        Usage: !lyrics <song title>
        Example: !lyrics Imagine John Lennon
        Note: Uses Genius API (requires API key for full functionality)
        """
        if song_title is None:
            current = bot.music_player.current_playing.get(ctx.guild.id)
            if not current:
                await ctx.send("❌ Please specify a song title or play a song first!")
                return
            song_title = current['title']
        
        async with ctx.typing():
            lyrics = await bot.music_player.get_lyrics(song_title)
        
        if lyrics:
            # Split into chunks if too long
            if len(lyrics) > 2000:
                chunks = [lyrics[i:i+2000] for i in range(0, len(lyrics), 2000)]
                for chunk in chunks:
                    await ctx.send(chunk)
            else:
                await ctx.send(lyrics)
        else:
            await ctx.send(f"❌ Could not find lyrics for '{song_title}'")
    
    @bot.command(name='search', aliases=['s'])
    async def search(ctx, *, query: str):
        """
        Search and play a song from YouTube.
        
        Usage: !search <song name or artist>
        Example: !search Bohemian Rhapsody Queen
        """
        if not ctx.author.voice:
            await ctx.send("❌ You must be in a voice channel to play music!")
            return
        
        # Connect to voice channel if not already connected
        voice_client = None
        if ctx.guild.id in bot.music_player.voice_clients:
            voice_client = bot.music_player.voice_clients[ctx.guild.id]
        else:
            try:
                voice_client = await ctx.author.voice.channel.connect()
                bot.music_player.voice_clients[ctx.guild.id] = voice_client
            except Exception as e:
                await ctx.send(f"❌ Failed to connect to voice channel: {str(e)}")
                return
        
        async with ctx.typing():
            song = await bot.music_player.search_and_play(ctx.guild.id, query, voice_client)
        
        if song:
            embed = discord.Embed(
                title="🔍 Found and Playing",
                description=f"[{song['title']}]({song['url']})",
                color=discord.Color.green()
            )
            if song['duration']:
                embed.add_field(name="Duration", value=bot.music_player.format_duration(song['duration']))
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Could not find a song matching '{query}'")
