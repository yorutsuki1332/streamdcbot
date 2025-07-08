import discord
import logging
from utils import format_emoji

class ReactionHandler:
    """Handles Discord reaction events for role assignment"""
    
    def __init__(self, bot, config_manager):
        self.bot = bot
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
    async def handle_reaction_add(self, payload):
        """Handle when a user adds a reaction"""
        # Ignore bot reactions
        if payload.user_id == self.bot.user.id:
            return
            
        # Get configuration for this reaction
        config = await self.config_manager.get_reaction_config(
            payload.guild_id,
            payload.channel_id,
            payload.message_id,
            format_emoji(payload.emoji)
        )
        
        if not config:
            return  # No configuration found for this reaction
            
        # Get guild and member
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            self.logger.error(f"Guild {payload.guild_id} not found")
            return
            
        member = guild.get_member(payload.user_id)
        if not member:
            try:
                member = await guild.fetch_member(payload.user_id)
            except discord.NotFound:
                self.logger.error(f"Member {payload.user_id} not found in guild {payload.guild_id}")
                return
                
        # Get role
        role = guild.get_role(config['role_id'])
        if not role:
            self.logger.error(f"Role {config['role_id']} not found in guild {payload.guild_id}")
            # Clean up invalid configuration
            await self.config_manager.remove_reaction_role(
                payload.guild_id,
                payload.channel_id,
                payload.message_id,
                format_emoji(payload.emoji)
            )
            return
            
        # Check if member already has the role
        if role in member.roles:
            return
            
        # Check bot permissions
        if not guild.me.guild_permissions.manage_roles:
            self.logger.error(f"Bot lacks manage_roles permission in guild {payload.guild_id}")
            return
            
        if role >= guild.me.top_role:
            self.logger.error(f"Role {role.name} is higher than bot's highest role in guild {payload.guild_id}")
            return
            
        # Assign the role
        try:
            await member.add_roles(role, reason="Reaction role assignment")
            self.logger.info(f"Assigned role {role.name} to {member.display_name} in guild {guild.name}")
        except discord.Forbidden:
            self.logger.error(f"Forbidden: Cannot assign role {role.name} to {member.display_name}")
        except discord.HTTPException as e:
            self.logger.error(f"HTTP error assigning role: {e}")
            
    async def handle_reaction_remove(self, payload):
        """Handle when a user removes a reaction"""
        # Ignore bot reactions
        if payload.user_id == self.bot.user.id:
            return
            
        # Get configuration for this reaction
        config = await self.config_manager.get_reaction_config(
            payload.guild_id,
            payload.channel_id,
            payload.message_id,
            format_emoji(payload.emoji)
        )
        
        if not config:
            return  # No configuration found for this reaction
            
        # Get guild and member
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            self.logger.error(f"Guild {payload.guild_id} not found")
            return
            
        member = guild.get_member(payload.user_id)
        if not member:
            try:
                member = await guild.fetch_member(payload.user_id)
            except discord.NotFound:
                self.logger.error(f"Member {payload.user_id} not found in guild {payload.guild_id}")
                return
                
        # Get role
        role = guild.get_role(config['role_id'])
        if not role:
            self.logger.error(f"Role {config['role_id']} not found in guild {payload.guild_id}")
            # Clean up invalid configuration
            await self.config_manager.remove_reaction_role(
                payload.guild_id,
                payload.channel_id,
                payload.message_id,
                format_emoji(payload.emoji)
            )
            return
            
        # Check if member has the role
        if role not in member.roles:
            return
            
        # Check bot permissions
        if not guild.me.guild_permissions.manage_roles:
            self.logger.error(f"Bot lacks manage_roles permission in guild {payload.guild_id}")
            return
            
        if role >= guild.me.top_role:
            self.logger.error(f"Role {role.name} is higher than bot's highest role in guild {payload.guild_id}")
            return
            
        # Remove the role
        try:
            await member.remove_roles(role, reason="Reaction role removal")
            self.logger.info(f"Removed role {role.name} from {member.display_name} in guild {guild.name}")
        except discord.Forbidden:
            self.logger.error(f"Forbidden: Cannot remove role {role.name} from {member.display_name}")
        except discord.HTTPException as e:
            self.logger.error(f"HTTP error removing role: {e}")
