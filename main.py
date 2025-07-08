import asyncio
import logging
import os
from bot import ReactionRoleBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

async def main():
    """Main function to start the Discord bot"""
    # Get bot token from environment variables
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        logging.error("DISCORD_BOT_TOKEN environment variable not set!")
        print("Please set the DISCORD_BOT_TOKEN environment variable with your bot token.")
        return
    
    # Create and start the bot
    bot = ReactionRoleBot()
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logging.info("Bot shutdown requested by user")
    except Exception as e:
        logging.error(f"Bot encountered an error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
