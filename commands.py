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
        super().__init__(label='同意入境', style=discord.ButtonStyle.green, emoji=emoji)
    
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
