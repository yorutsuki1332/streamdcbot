import discord
from discord.ext import commands
import logging
import asyncio
from utils import parse_emoji, get_role_by_name_or_id

async def setup_commands(bot):
    """Set up all bot commands"""
    
    @bot.command(name='setup_reaction_role', aliases=['srr'])
    @commands.has_permissions(administrator=True)
    async def setup_reaction_role(ctx, message_id: int, emoji: str, role: str):
        """Set up a reaction role."""
        try:
            message = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("❌ Message not found!")
            return
        except discord.Forbidden:
            await ctx.send("❌ No permission to access that message!")
            return
        
        parsed_emoji = parse_emoji(emoji)
        if not parsed_emoji:
            await ctx.send("❌ Invalid emoji!")
            return
        
        target_role = get_role_by_name_or_id(ctx.guild, role)
        if not target_role or target_role >= ctx.guild.me.top_role:
            await ctx.send("❌ Role not found or too high!")
            return
        
        config_added = await bot.config_manager.add_reaction_role(
            ctx.guild.id, ctx.channel.id, message_id, parsed_emoji, target_role.id
        )
        
        if config_added:
            try:
                await message.add_reaction(parsed_emoji)
                await ctx.send(f"✅ Reaction role set up!")
            except discord.Forbidden:
                await ctx.send("❌ Can't add reactions!")
        else:
            await ctx.send("❌ Already exists!")
    
    @bot.command(name='remove_reaction_role', aliases=['rrr'])
    @commands.has_permissions(administrator=True)
    async def remove_reaction_role(ctx, message_id: int, emoji: str):
        """Remove a reaction role."""
        parsed_emoji = parse_emoji(emoji)
        if not parsed_emoji:
            await ctx.send("❌ Invalid emoji!")
            return
        
        removed = await bot.config_manager.remove_reaction_role(
            ctx.guild.id, ctx.channel.id, message_id, parsed_emoji
        )
        
        if removed:
            try:
                message = await ctx.channel.fetch_message(message_id)
                await message.clear_reaction(parsed_emoji)
            except:
                pass
            await ctx.send(f"✅ Removed!")
        else:
            await ctx.send("❌ Not found!")
    
    @bot.command(name='list_reaction_roles', aliases=['lrr'])
    @commands.has_permissions(administrator=True)
    async def list_reaction_roles(ctx):
        """List all reaction roles."""
        configs = await bot.config_manager.get_guild_configs(ctx.guild.id)
        if not configs:
            await ctx.send("📝 No reaction roles configured.")
            return
        
        embed = discord.Embed(title="Reaction Roles", color=discord.Color.blue())
        for config in configs:
            channel = bot.get_channel(config['channel_id'])
            channel_name = channel.name if channel else f"Unknown"
            role = ctx.guild.get_role(config['role_id'])
            role_name = role.name if role else f"Unknown"
            embed.add_field(
                name=f"Message {config['message_id']}",
                value=f"#{channel_name} | {config['emoji']} → {role_name}",
                inline=False
            )
        await ctx.send(embed=embed)
    
    @bot.command(name='test_permissions')
    @commands.has_permissions(administrator=True)
    async def test_permissions(ctx):
        """Test bot permissions."""
        perms = ctx.guild.me.guild_permissions
        embed = discord.Embed(title="Bot Permissions", color=discord.Color.green())
        embed.add_field(name="Manage Roles", value="✅" if perms.manage_roles else "❌")
        embed.add_field(name="Add Reactions", value="✅" if perms.add_reactions else "❌")
        embed.add_field(name="Read Message History", value="✅" if perms.read_message_history else "❌")
        await ctx.send(embed=embed)
    
    @bot.command(name='set_youtube_channel', aliases=['syc'])
    @commands.has_permissions(administrator=True)
    async def set_youtube_channel(ctx, *, channel_url_or_id: str):
        """Set YouTube channel to monitor."""
        success = await bot.youtube_monitor.set_youtube_channel(channel_url_or_id)
        if success:
            await ctx.send("✅ YouTube channel set!")
        else:
            await ctx.send("❌ Failed to set YouTube channel!")
    
    @bot.command(name='youtube_status', aliases=['ys'])
    @commands.has_permissions(administrator=True)
    async def youtube_status(ctx):
        """Check YouTube monitoring status."""
        channel_id = bot.youtube_monitor.channel_id
        api_key_set = bool(bot.youtube_monitor.api_key)
        embed = discord.Embed(title="YouTube Status", color=discord.Color.blue())
        embed.add_field(name="API Key", value="✅" if api_key_set else "❌")
        embed.add_field(name="Channel", value=channel_id if channel_id else "❌ Not Set")
        await ctx.send(embed=embed)
    
    @bot.command(name='join', aliases=['j'])
    async def join(ctx):
        """Join your voice channel (diagnostic command)."""
        if not ctx.author.voice:
            await ctx.send("❌ You must be in a voice channel!")
            return
        
        channel = ctx.author.voice.channel
        
        try:
            voice_client = await channel.connect(timeout=10.0, reconnect=True)
            bot.music_player.voice_clients[ctx.guild.id] = voice_client
            await ctx.send(f"✅ Joined {channel.mention}")
        except Exception as e:
            await ctx.send(f"❌ Failed to join: {type(e).__name__}: {str(e)}")
    
    @bot.command(name='leave', aliases=['l'])
    async def leave(ctx):
        """Leave voice channel."""
        if ctx.guild.id in bot.music_player.voice_clients:
            voice_client = bot.music_player.voice_clients[ctx.guild.id]
            await voice_client.disconnect()
            del bot.music_player.voice_clients[ctx.guild.id]
            await ctx.send("✅ Left voice channel")
        else:
            await ctx.send("❌ Not in a voice channel")
    @commands.has_permissions(administrator=True)
    async def fix_voice_permissions(ctx, channel: discord.VoiceChannel = None):
        """Fix bot voice channel permissions."""
        if not channel:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
            else:
                await ctx.send("❌ Please specify a voice channel or join one!")
                return
        
        try:
            # Get bot role
            bot_role = ctx.guild.me.top_role
            
            # Set permissions for bot
            perms = discord.PermissionOverwrite(
                connect=True,
                speak=True,
                stream=True,
                use_voice_activation=True
            )
            
            await channel.set_permissions(ctx.guild.me, overwrite=perms)
            await ctx.send(f"✅ Fixed permissions for {channel.mention}!\n"
                          "Bot now has: Connect, Speak, Stream, Voice Activity permissions")
        except Exception as e:
            await ctx.send(f"❌ Failed to fix permissions: {str(e)}")
    
    @bot.command(name='welcome_message', aliases=['wm'])
    @commands.has_permissions(administrator=True)
    async def welcome_message(ctx):
        """Send welcome message."""
        from constants import WELCOME_TEXT
        stored = await bot.config_manager.get_welcome_message(ctx.guild.id)
        if stored:
            try:
                ch = ctx.guild.get_channel(stored['channel_id'])
                msg = await ch.fetch_message(stored['message_id'])
                await msg.delete()
            except:
                pass
            await bot.config_manager.remove_welcome_message(ctx.guild.id)
        
        async for msg in ctx.channel.history(limit=50):
            if msg.author == ctx.guild.me and msg.content == WELCOME_TEXT and msg.components:
                try:
                    await msg.delete()
                except:
                    pass
        
        view = WelcomeView(bot)
        msg = await ctx.send(WELCOME_TEXT, view=view)
        await bot.config_manager.set_welcome_message(ctx.guild.id, ctx.channel.id, msg.id)
        await ctx.send("✅ Welcome message sent!")
        try:
            await ctx.message.delete()
        except:
            pass
    
    # ===== MUSIC COMMANDS =====
    @bot.command(name='play', aliases=['p'])
    async def play(ctx, *, url: str):
        """Play YouTube video or playlist."""
        if not ctx.author.voice:
            await ctx.send("❌ Join a voice channel first!")
            return
        
        channel = ctx.author.voice.channel
        
        # Try to connect
        voice_client = bot.music_player.voice_clients.get(ctx.guild.id)
        if not voice_client:
            try:
                voice_client = await channel.connect()
                bot.music_player.voice_clients[ctx.guild.id] = voice_client
            except Exception as e:
                await ctx.send(f"❌ Cannot join voice channel: {str(e)}\n"
                               f"Please try `!join` first")
                return
        
        # Add to queue and play
        async with ctx.typing():
            result = await bot.music_player.add_to_queue(ctx.guild.id, url)
        
        if not result['success']:
            await ctx.send(f"❌ {result.get('error')}")
            return
        
        if not voice_client.is_playing():
            song = await bot.music_player.play_next(ctx.guild.id, voice_client)
            if song:
                embed = discord.Embed(
                    title="🎵 Now Playing",
                    description=f"[{song['title']}]({song['url']})",
                    color=discord.Color.purple()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to load song")
        else:
            await ctx.send(f"✅ Added {result['count']} song(s) to queue")
    
    @bot.command(name='queue', aliases=['q'])
    async def queue(ctx):
        """Show music queue."""
        queue = await bot.music_player.get_queue(ctx.guild.id)
        current = bot.music_player.current_playing.get(ctx.guild.id)
        embed = discord.Embed(title="🎵 Queue", color=discord.Color.purple())
        
        if current:
            embed.add_field(name="Now Playing", value=f"[{current['title']}]({current['url']})", inline=False)
        
        if queue:
            text = "\n".join([f"{i+1}. {s['title']}" for i, s in enumerate(queue[:10])])
            if len(queue) > 10:
                text += f"\n+{len(queue)-10} more"
            embed.add_field(name=f"Queue ({len(queue)})", value=text, inline=False)
        else:
            embed.add_field(name="Queue", value="Empty", inline=False)
        
        await ctx.send(embed=embed)
    
    @bot.command(name='skip')
    async def skip(ctx):
        """Skip song."""
        if await bot.music_player.skip(ctx.guild.id):
            await ctx.send("⏭️ Skipped!")
        else:
            await ctx.send("❌ Nothing playing!")
    
    @bot.command(name='pause')
    async def pause(ctx):
        """Pause music."""
        if await bot.music_player.pause(ctx.guild.id):
            await ctx.send("⏸️ Paused!")
        else:
            await ctx.send("❌ Nothing playing!")
    
    @bot.command(name='resume', aliases=['r'])
    async def resume(ctx):
        """Resume music."""
        if await bot.music_player.resume(ctx.guild.id):
            await ctx.send("▶️ Resumed!")
        else:
            await ctx.send("❌ Nothing paused!")
    
    @bot.command(name='stop')
    async def stop(ctx):
        """Stop music."""
        await bot.music_player.stop(ctx.guild.id)
        await ctx.send("⏹️ Stopped!")
    
    @bot.command(name='loop', aliases=['l'])
    async def loop(ctx):
        """Toggle loop."""
        is_looping = await bot.music_player.toggle_loop(ctx.guild.id)
        await ctx.send("✅ Loop ON" if is_looping else "❌ Loop OFF")
    
    @bot.command(name='volume', aliases=['vol', 'v'])
    async def volume(ctx, level: int = None):
        """Set volume (0-100)."""
        if level is None:
            vol = bot.music_player.get_volume(ctx.guild.id)
            await ctx.send(f"🔊 {vol:.0f}%")
            return
        
        if not 0 <= level <= 100:
            await ctx.send("❌ Volume must be 0-100!")
            return
        
        await bot.music_player.set_volume(ctx.guild.id, level / 100)
        await ctx.send(f"🔊 {level}%")
    
    @bot.command(name='now', aliases=['np', 'nowplaying'])
    async def now_playing(ctx):
        """Show song progress."""
        progress = bot.music_player.get_now_playing_progress(ctx.guild.id)
        if not progress:
            await ctx.send("❌ Nothing playing!")
            return
        
        bar_length = 20
        filled = int((progress['progress'] / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        elapsed = bot.music_player.format_duration(progress['elapsed'])
        duration = bot.music_player.format_duration(progress['duration'])
        
        embed = discord.Embed(title="🎵 Now Playing", description=progress['title'], color=discord.Color.purple())
        embed.add_field(name="Progress", value=f"{bar}\n{elapsed} / {duration}", inline=False)
        await ctx.send(embed=embed)
    
    @bot.command(name='lyrics', aliases=['ly'])
    async def lyrics(ctx, *, song_title: str = None):
        """Get song lyrics."""
        if not song_title:
            current = bot.music_player.current_playing.get(ctx.guild.id)
            if not current:
                await ctx.send("❌ Specify a song or play one!")
                return
            song_title = current['title']
        
        async with ctx.typing():
            result = await bot.music_player.get_lyrics(song_title)
        
        if result:
            if len(result) > 2000:
                for chunk in [result[i:i+2000] for i in range(0, len(result), 2000)]:
                    await ctx.send(chunk)
            else:
                await ctx.send(result)
        else:
            await ctx.send(f"❌ No lyrics found!")
    
    @bot.command(name='search', aliases=['find', 'searchmusic'])
    async def search(ctx, *, query: str):
        """Search and play song."""
        if not ctx.author.voice:
            await ctx.send("❌ Join a voice channel!")
            return
        
        voice_client = bot.music_player.voice_clients.get(ctx.guild.id)
        if not voice_client:
            try:
                voice_client = await ctx.author.voice.channel.connect()
                bot.music_player.voice_clients[ctx.guild.id] = voice_client
            except Exception as e:
                await ctx.send(f"❌ Failed to connect: {str(e)}")
                return
        
        async with ctx.typing():
            song = await bot.music_player.search_and_play(ctx.guild.id, query, voice_client)
        
        if song:
            embed = discord.Embed(title="🔍 Found & Playing", description=f"[{song['title']}]({song['url']})", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ No song found!")
    
    @setup_reaction_role.error
    @remove_reaction_role.error
    @list_reaction_roles.error
    @test_permissions.error
    @set_youtube_channel.error
    @youtube_status.error
    @welcome_message.error
    async def command_error_handler(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Need Administrator permission!")
        else:
            logging.error(f"Error: {error}")


class WelcomeView(discord.ui.View):
    def __init__(self, bot=None):
        super().__init__(timeout=None)
        emoji = '🦄'
        if bot and hasattr(bot, 'custom_emoji') and bot.custom_emoji:
            emoji = bot.custom_emoji
        self.add_item(WelcomeButton(emoji))


class WelcomeButton(discord.ui.Button):
    def __init__(self, emoji):
        super().__init__(label='同意入境', style=discord.ButtonStyle.primary, emoji=emoji)
    
    async def callback(self, interaction: discord.Interaction):
        """Handle button click."""
        if interaction.guild.id == 1288838226362105868:
            role = interaction.guild.get_role(1392004567524446218)
        else:
            role = discord.utils.get(interaction.guild.roles, name='聯邦住民')
        
        if not role:
            await interaction.response.send_message("❌ Role not found!", ephemeral=True)
            return
        
        if role in interaction.user.roles:
            await interaction.response.send_message("You already have this role!", ephemeral=True)
            return
        
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ No permission!", ephemeral=True)
            return
        
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ Role too high!", ephemeral=True)
            return
        
        try:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✅ Welcome!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
