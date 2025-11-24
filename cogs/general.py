"""
General utility commands for Discord bot.

This module contains general-purpose commands that don't fit into specific cogs.
"""

import logging
import discord
from discord.ext import commands
from core.bot_setup import DiscordBot
from core.version import get_version_string

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
    async def ping(self, ctx: commands.Context[DiscordBot]) -> None:
        """Check the bot's latency.

        Args:
            ctx: The command context.
        """
        latency = round(ctx.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms", ephemeral=True)

    @commands.hybrid_command(
        name="stats",
        description="Show bot statistics.",
    )
    async def stats(self, ctx: commands.Context[DiscordBot]) -> None:
        """Show bot statistics.

        Args:
            ctx: The command context.
        """
        guild_count = len(self.bot.guilds)
        user_count = sum(guild.member_count or 0 for guild in self.bot.guilds)

        embed = discord.Embed(
            title="🤖 Bot Statistics",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Servers", value=guild_count, inline=True)
        embed.add_field(name="Users", value=user_count, inline=True)
        embed.add_field(
            name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True
        )
        embed.set_footer(text=f"Discord Link Bot {get_version_string()}")

        await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="invite",
        description="Get the bot invite link.",
    )
    async def invite(self, ctx: commands.Context[DiscordBot]) -> None:
        """Get the bot invite link.

        Args:
            ctx: The command context.
        """
        invite_url = "https://discord.com/oauth2/authorize?client_id=1437822477609730102&scope=bot+applications.commands&permissions=536964112"
        embed = discord.Embed(
            title="🤖 Invite Link Bot",
            description=f"Click [here]({invite_url}) to invite the bot to your server!",
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Discord Link Bot {get_version_string()}")
        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Load the General cog into the bot.

    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(General(bot))
