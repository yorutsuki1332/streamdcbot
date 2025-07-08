# Discord Reaction Role Bot

## Overview

This is a Discord bot that provides reaction role functionality, allowing users to automatically receive roles when they react to specific messages with designated emojis. The bot is built using the discord.py library and features a modular architecture with persistent configuration storage.

## System Architecture

The bot follows a modular, event-driven architecture with clear separation of concerns:

- **Main Bot Class**: Central orchestrator that manages Discord connections and coordinates between components
- **Command System**: Handles administrative commands for setting up reaction roles
- **Reaction Handler**: Processes Discord reaction events and manages role assignments
- **Configuration Manager**: Provides persistent storage for reaction role configurations
- **Utility Functions**: Shared helper functions for emoji parsing and role management

## Key Components

### 1. Bot Core (`bot.py`)
- **Purpose**: Main bot class extending discord.py's commands.Bot
- **Key Features**: 
  - Manages Discord intents (message content, reactions, guilds, members)
  - Initializes and coordinates all bot components
  - Sets up logging and bot activity status
- **Design Decision**: Uses commands.Bot for built-in command framework support

### 2. Command System (`commands.py`)
- **Purpose**: Administrative commands for configuring reaction roles
- **Key Features**:
  - `!setup_reaction_role` command for linking emojis to roles on specific messages
  - Permission checks (requires manage_roles permission)
  - Input validation for messages, emojis, and roles
- **Design Decision**: Uses decorator-based command registration for simplicity

### 3. Reaction Handler (`reaction_handler.py`)
- **Purpose**: Processes Discord reaction events for role assignment/removal
- **Key Features**:
  - Handles reaction_add and reaction_remove events
  - Validates configurations before role assignments
  - Error handling for missing guilds, members, or roles
- **Design Decision**: Separate handler class for clean event processing logic

### 4. Configuration Manager (`config_manager.py`)
- **Purpose**: Persistent storage of reaction role configurations
- **Key Features**:
  - JSON file-based storage (`config.json`)
  - Async file operations with aiofiles
  - Thread-safe operations with asyncio locks
  - Automatic cleanup of invalid configurations
- **Design Decision**: JSON storage chosen for simplicity and human readability

### 5. Utilities (`utils.py`)
- **Purpose**: Shared helper functions
- **Key Features**:
  - Emoji parsing (Unicode and custom Discord emojis)
  - Role lookup by name or ID
  - Emoji formatting for storage consistency

## Data Flow

1. **Setup Flow**:
   - Admin runs `!setup_reaction_role` command
   - Bot validates message, emoji, and role
   - Configuration stored in JSON file
   - Bot adds reaction to target message

2. **Role Assignment Flow**:
   - User adds/removes reaction to configured message
   - Reaction handler receives Discord event
   - Handler looks up configuration for specific message+emoji combination
   - Role assigned/removed from user if configuration exists

3. **Configuration Management**:
   - Configurations loaded on bot startup
   - Changes saved immediately to persistent storage
   - Invalid configurations automatically cleaned up

## External Dependencies

- **discord.py**: Core Discord API wrapper
- **aiofiles**: Async file I/O operations
- **Python standard library**: json, logging, asyncio, os, re, typing

## Deployment Strategy

- **Environment Variables**: Bot token stored in `DISCORD_BOT_TOKEN` environment variable
- **Logging**: Dual output to both file (`bot.log`) and console
- **Error Handling**: Comprehensive error handling with graceful degradation
- **Persistence**: Local JSON file storage for configurations

**Rationale**: Simple deployment approach suitable for single-instance bots, with file-based storage eliminating database dependencies.

## User Preferences

Preferred communication style: Simple, everyday language.
Bot name preference: "大賢者" (Great Sage in Japanese)

## Changelog

Changelog:
- July 08, 2025. Initial setup
- July 08, 2025. Updated bot to use name "大賢者" - bot will attempt to set this as nickname in servers
- July 08, 2025. Added keepAlive.py for continuous operation
- July 08, 2025. Added welcome message with "同意入境" button that assigns '聯邦住民' role
- July 08, 2025. Updated all admin commands to require Administrator permission (integer 8)
- July 08, 2025. Optimized role assignment using specific role ID 1392004567524446218 for '澪夜聯邦' server (ID: 1288838226362105868)
- July 08, 2025. Added YouTube video monitoring system with automatic notifications (@everyone tags)