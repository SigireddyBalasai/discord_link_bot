"""
Discord bot setup module.

Defines the DiscordBot class with custom setup, error handling, and integration
for database and enhanced help command.
"""

import logging
from logging import Logger

import discord
from discord import Intents
from discord.ext import commands
from pretty_help import PrettyHelp
from .db.db_manager import Database


class DiscordBot(commands.Bot):
    """Custom Discord bot with database integration and enhanced help command."""

    def __init__(self) -> None:
        """Initialize the DiscordBot with intents and a pretty help command."""
        intents: Intents = Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=PrettyHelp(color=discord.Color.blue()),
        )
        self.db: Database | None = None

    async def setup_hook(self) -> None:
        """Load extensions and sync slash commands on startup."""
        logger: Logger = logging.getLogger(__name__)
        logger.info("Loading cogs...")
        await self.load_extension("cogs.link_monitor")
        logger.info("LinkMonitor cog loaded successfully")
        await self.load_extension("cogs.link_manager")
        logger.info("LinkManager cog loaded successfully")
        await self.load_extension("cogs.general")
        logger.info("General cog loaded successfully")
        logger.info("Syncing slash commands...")
        await self.tree.sync()
        logger.info("Slash commands synced!")

    async def on_ready(self) -> None:
        """Log bot readiness and registered slash commands."""
        logger: Logger = logging.getLogger(__name__)
        if self.user:
            logger.info("Logged in as %s (ID: %s)", self.user, self.user.id)
        logger.info("Connected to %d guilds", len(self.guilds))
        logger.info("Slash commands: %d registered", len(self.tree.get_commands()))
        logger.info("------")

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Log when the bot joins a new guild."""
        logger: Logger = logging.getLogger(__name__)
        logger.info("Joined guild: %s (ID: %s)", guild.name, guild.id)

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Log when the bot leaves a guild."""
        logger = logging.getLogger(__name__)
        logger.info("Left guild: %s (ID: %s)", guild.name, guild.id)

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError, /
    ) -> None:
        """Handle errors for commands and provide user feedback.

        Args:
            ctx: The command context where the error occurred.
            error: The exception that was raised.
        """
        logger: Logger = logging.getLogger(__name__)
        try:
            if isinstance(error, commands.CommandNotFound):
                await ctx.send(
                    "Command not found. Use `!help` to see available commands."
                )
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f"Missing required argument: {error.param.name}")
            elif isinstance(error, commands.BadArgument):
                await ctx.send("Invalid argument provided.")
            elif isinstance(error, commands.MissingPermissions):
                logger.warning("Permission denied: %s", error)
                await ctx.send("❌ You don't have permission to use this command.")
            elif isinstance(error, commands.NoPrivateMessage):
                await ctx.send("❌ This command cannot be used in private messages.")
            elif isinstance(error, commands.CheckFailure):
                logger.warning("Check failed: %s", error)
                await ctx.send("❌ Command requirements not met.")
            else:
                logger.error("Unexpected error: %s", error, exc_info=True)
                await ctx.send("❌ An unexpected error occurred.")
        except discord.NotFound:
            logger.warning("Could not send error message - interaction expired")
