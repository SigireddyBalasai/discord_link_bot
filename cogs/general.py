"""
General utility commands for Discord bot.

This module contains general-purpose commands that don't fit into specific cogs.
"""

import logging
from discord.ext import commands

logger: logging.Logger = logging.getLogger(name=__name__)


class General(commands.Cog):
    """General utility commands."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the General cog.

        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot

    @commands.hybrid_command(
        name="ping",
        description="Check bot latency.",
    )
    async def ping(self, ctx: commands.Context) -> None:
        """Check the bot's latency.

        Args:
            ctx: The command context.
        """
        latency = round(ctx.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Load the General cog into the bot.

    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(General(bot))