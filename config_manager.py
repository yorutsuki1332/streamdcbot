import json
import asyncio
import logging
from typing import Optional, List, Dict
import aiofiles

class ConfigManager:
    """Manages persistent storage of reaction role configurations"""
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.configs = {}
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()
        
    async def load_config(self):
        """Load configurations from file"""
        try:
            async with aiofiles.open(self.config_file, 'r') as f:
                content = await f.read()
                self.configs = json.loads(content)
                self.logger.info(f"Loaded {len(self.configs)} guild configurations")
        except FileNotFoundError:
            self.logger.info("Config file not found, starting with empty configuration")
            self.configs = {}
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON in config file, starting with empty configuration")
            self.configs = {}
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self.configs = {}
            
    async def save_config(self):
        """Save configurations to file"""
        async with self._lock:
            try:
                async with aiofiles.open(self.config_file, 'w') as f:
                    await f.write(json.dumps(self.configs, indent=2))
                    self.logger.debug("Configuration saved to file")
            except Exception as e:
                self.logger.error(f"Error saving config: {e}")
                
    async def add_reaction_role(self, guild_id: int, channel_id: int, message_id: int, emoji: str, role_id: int) -> bool:
        """
        Add a reaction role configuration.
        Returns True if added, False if already exists.
        """
        guild_key = str(guild_id)
        config_key = f"{channel_id}_{message_id}_{emoji}"
        
        if guild_key not in self.configs:
            self.configs[guild_key] = {}
            
        if config_key in self.configs[guild_key]:
            return False  # Already exists
            
        self.configs[guild_key][config_key] = {
            'guild_id': guild_id,
            'channel_id': channel_id,
            'message_id': message_id,
            'emoji': emoji,
            'role_id': role_id
        }
        
        await self.save_config()
        self.logger.info(f"Added reaction role config: {config_key} -> role {role_id}")
        return True
        
    async def remove_reaction_role(self, guild_id: int, channel_id: int, message_id: int, emoji: str) -> bool:
        """
        Remove a reaction role configuration.
        Returns True if removed, False if not found.
        """
        guild_key = str(guild_id)
        config_key = f"{channel_id}_{message_id}_{emoji}"
        
        if guild_key not in self.configs:
            return False
            
        if config_key not in self.configs[guild_key]:
            return False
            
        del self.configs[guild_key][config_key]
        
        # Clean up empty guild configs
        if not self.configs[guild_key]:
            del self.configs[guild_key]
            
        await self.save_config()
        self.logger.info(f"Removed reaction role config: {config_key}")
        return True
        
    async def get_reaction_config(self, guild_id: int, channel_id: int, message_id: int, emoji: str) -> Optional[Dict]:
        """Get a specific reaction role configuration"""
        guild_key = str(guild_id)
        config_key = f"{channel_id}_{message_id}_{emoji}"
        
        if guild_key not in self.configs:
            return None
            
        return self.configs[guild_key].get(config_key)
        
    async def get_guild_configs(self, guild_id: int) -> List[Dict]:
        """Get all reaction role configurations for a guild"""
        guild_key = str(guild_id)
        
        if guild_key not in self.configs:
            return []
            
        return list(self.configs[guild_key].values())
        
    async def cleanup_guild(self, guild_id: int):
        """Remove all configurations for a guild (when bot leaves)"""
        guild_key = str(guild_id)
        
        if guild_key in self.configs:
            del self.configs[guild_key]
            await self.save_config()
            self.logger.info(f"Cleaned up configurations for guild {guild_id}")
            
    async def cleanup_invalid_configs(self, bot):
        """Remove configurations for guilds/channels/roles that no longer exist"""
        cleaned = 0
        
        for guild_key in list(self.configs.keys()):
            guild_id = int(guild_key)
            guild = bot.get_guild(guild_id)
            
            if not guild:
                # Guild no longer exists
                del self.configs[guild_key]
                cleaned += 1
                continue
                
            # Check individual configs
            for config_key in list(self.configs[guild_key].keys()):
                config = self.configs[guild_key][config_key]
                
                # Check if channel exists
                channel = guild.get_channel(config['channel_id'])
                if not channel:
                    del self.configs[guild_key][config_key]
                    cleaned += 1
                    continue
                    
                # Check if role exists
                role = guild.get_role(config['role_id'])
                if not role:
                    del self.configs[guild_key][config_key]
                    cleaned += 1
                    continue
                    
            # Clean up empty guild configs
            if not self.configs[guild_key]:
                del self.configs[guild_key]
                
        if cleaned > 0:
            await self.save_config()
            self.logger.info(f"Cleaned up {cleaned} invalid configurations")
    
    async def set_welcome_message(self, guild_id: int, channel_id: int, message_id: int) -> bool:
        """Store welcome message reference"""
        async with self._lock:
            guild_key = str(guild_id)
            if guild_key not in self.configs:
                self.configs[guild_key] = {}
            
            self.configs[guild_key]['welcome_message'] = {
                'channel_id': channel_id,
                'message_id': message_id
            }
            
            await self.save_config()
            return True
    
    async def get_welcome_message(self, guild_id: int) -> Optional[Dict]:
        """Get welcome message reference"""
        guild_key = str(guild_id)
        if guild_key in self.configs:
            return self.configs[guild_key].get('welcome_message')
        return None
    
    async def remove_welcome_message(self, guild_id: int) -> bool:
        """Remove welcome message reference"""
        async with self._lock:
            guild_key = str(guild_id)
            if guild_key in self.configs and 'welcome_message' in self.configs[guild_key]:
                del self.configs[guild_key]['welcome_message']
                await self.save_config()
                return True
        return False
