import discord
from discord.ext import commands
import logging
from utils import parse_emoji, get_role_by_name_or_id

async def setup_commands(bot):
    """Set up all bot commands"""
    
    @bot.command(name='setup_reaction_role', aliases=['srr'])
    @commands.has_permissions(manage_roles=True)
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
    @commands.has_permissions(manage_roles=True)
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
    @commands.has_permissions(manage_roles=True)
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
    @commands.has_permissions(manage_roles=True)
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
    
    @bot.command(name='welcome_message', aliases=['wm'])
    @commands.has_permissions(manage_messages=True)
    async def welcome_message(ctx):
        """Send a welcome message with an entry button."""
        # Create the button view
        view = WelcomeView()
        
        # Send the welcome message with the button
        await ctx.send("歡迎來到澪夜聯邦！", view=view)
    
    # Error handlers for specific commands
    @setup_reaction_role.error
    @remove_reaction_role.error
    @list_reaction_roles.error
    @test_permissions.error
    @welcome_message.error
    async def command_error_handler(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need the 'Manage Roles' permission to use this command!")
        else:
            logging.error(f"Command error: {error}")

class WelcomeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # No timeout for persistent view
    
    @discord.ui.button(label='同意入境', style=discord.ButtonStyle.green, emoji='✅')
    async def agree_entry(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle the agree entry button click"""
        # You can add role assignment or other logic here
        await interaction.response.send_message(
            f"歡迎，{interaction.user.mention}！您已成功入境澪夜聯邦！", 
            ephemeral=True
        )
