import discord
import re
from typing import Optional, Union

def parse_emoji(emoji_str: str) -> Optional[str]:
    """
    Parse emoji string and return a standardized format.
    Handles both Unicode emojis and custom Discord emojis.
    """
    if not emoji_str:
        return None
        
    # Check if it's a custom Discord emoji (<:name:id> or <a:name:id>)
    custom_emoji_match = re.match(r'<(a?):([^:]+):(\d+)>', emoji_str)
    if custom_emoji_match:
        animated, name, emoji_id = custom_emoji_match.groups()
        return f"<{'a' if animated else ''}:{name}:{emoji_id}>"
        
    # For Unicode emojis, return as-is
    return emoji_str.strip()

def format_emoji(emoji: Union[discord.Emoji, discord.PartialEmoji, str]) -> str:
    """
    Format emoji object to string representation.
    """
    if isinstance(emoji, (discord.Emoji, discord.PartialEmoji)):
        if emoji.animated:
            return f"<a:{emoji.name}:{emoji.id}>"
        else:
            return f"<:{emoji.name}:{emoji.id}>"
    else:
        return str(emoji)

def get_role_by_name_or_id(guild: discord.Guild, role_identifier: str) -> Optional[discord.Role]:
    """
    Get a role by name or ID from a guild.
    """
    # Try to get by ID first
    if role_identifier.isdigit():
        role = guild.get_role(int(role_identifier))
        if role:
            return role
            
    # Try to get by mention
    if role_identifier.startswith('<@&') and role_identifier.endswith('>'):
        role_id = role_identifier[3:-1]
        if role_id.isdigit():
            role = guild.get_role(int(role_id))
            if role:
                return role
                
    # Try to get by name (case-insensitive)
    for role in guild.roles:
        if role.name.lower() == role_identifier.lower():
            return role
            
    return None

def is_emoji_equal(emoji1: str, emoji2: str) -> bool:
    """
    Compare two emoji strings for equality.
    """
    return parse_emoji(emoji1) == parse_emoji(emoji2)

def validate_bot_permissions(guild: discord.Guild, role: discord.Role) -> tuple[bool, str]:
    """
    Validate if the bot can manage a specific role.
    Returns (is_valid, error_message)
    """
    bot_member = guild.me
    
    if not bot_member.guild_permissions.manage_roles:
        return False, "Bot doesn't have 'Manage Roles' permission"
        
    if role >= bot_member.top_role:
        return False, f"Role '{role.name}' is higher than or equal to bot's highest role"
        
    if role.managed:
        return False, f"Role '{role.name}' is managed by an integration and cannot be assigned manually"
        
    return True, ""

def format_permission_error(permission_name: str) -> str:
    """Format a permission error message"""
    return f"❌ Missing permission: {permission_name}. Please ensure the bot has the necessary permissions."

def truncate_string(text: str, max_length: int = 100) -> str:
    """Truncate a string to a maximum length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
