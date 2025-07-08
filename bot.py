import discord
from discord.ext import commands
import logging
from commands import setup_commands
from reaction_handler import ReactionHandler
from config_manager import ConfigManager

class ReactionRoleBot(commands.Bot):
    """Main Discord bot class for reaction role functionality"""
    
    def __init__(self):
        # Set up bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=commands.DefaultHelpCommand()
        )
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.reaction_handler = ReactionHandler(self, self.config_manager)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        # Load existing configurations
        await self.config_manager.load_config()
        
        # Set up commands
        await setup_commands(self)
        
        self.logger.info("Bot setup completed")
        
    async def on_ready(self):
        """Called when the bot has successfully connected to Discord"""
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot activity
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for reactions | !help"
        )
        await self.change_presence(activity=activity)
        
        # Set bot nickname to 大賢者 if possible
        for guild in self.guilds:
            try:
                await guild.me.edit(nick="大賢者")
            except (discord.Forbidden, discord.HTTPException):
                # Ignore if we can't set nickname
                pass
        
    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild"""
        self.logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
        
    async def on_guild_remove(self, guild):
        """Called when the bot leaves a guild"""
        self.logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
        # Clean up configurations for this guild
        await self.config_manager.cleanup_guild(guild.id)
        
    async def on_raw_reaction_add(self, payload):
        """Handle reaction additions"""
        await self.reaction_handler.handle_reaction_add(payload)
        
    async def on_raw_reaction_remove(self, payload):
        """Handle reaction removals"""
        await self.reaction_handler.handle_reaction_remove(payload)
        
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
            
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command!")
            
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
            
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument provided: {error}")
            
        else:
            self.logger.error(f"Unhandled command error: {error}")
            await ctx.send("❌ An unexpected error occurred. Please try again later.")
