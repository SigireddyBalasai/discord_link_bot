"""
Main entry point for the Discord link bot.

Initializes logging, loads environment variables, sets up the bot and database, and starts the bot.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from core.bot_setup import DiscordBot
from core.db.db_manager import Database
from core.logging_setup import setup_logging


async def main() -> None:
    """
    Main asynchronous entry point for the Discord bot.

    Sets up logging, loads environment variables, initializes the bot and database,
    and starts the bot using the provided Discord token.
    """
    setup_logging()
    logger: logging.Logger = logging.getLogger(__name__)
    logger.info("Starting Discord Link Bot...")

    logger.info("Loading environment variables...")
    load_dotenv()
    logger.info("Environment variables loaded")

    logger.info("Initializing bot...")
    bot: DiscordBot = DiscordBot()
    db: Database = Database()
    bot.db = db
    await db.initialize()
    logger.info("Database initialized")

    token: str | None = os.getenv("DISCORD_TOKEN")
    if token is None:
        logger.error("DISCORD_TOKEN environment variable not found")
        return
    logger.info("Discord token found, starting bot...")

    try:
        async with bot:
            await bot.start(token=token)
    finally:
        logger.info("Bot shutting down, closing database connections...")
        await db.close()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
