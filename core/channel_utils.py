"""
Shared utilities for Discord bot cogs.

This module contains common functionality used across multiple cogs.
"""

import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

# Mapping of parameter names to ACL keys
PARAM_TO_KEY = {
    "youtube": "youtube",
    "twitch": "twitch",
    "twitter": "twitter",
    "instagram": "instagram",
    "tiktok": "tiktok",
    "reddit": "reddit",
    "github": "github",
    "discord_links": "discord",
    "other": "other",
}

# List of ACL keys
LINK_TYPES = list(PARAM_TO_KEY.values())


async def get_or_create_channel(
    ctx: commands.Context, name: str
) -> discord.TextChannel | None:
    """Get existing channel or create new one with default settings.

    Args:
        ctx: The command context.
        name: The channel name.

    Returns:
        The text channel or None if creation failed.
    """

    assert ctx.guild is not None
    existing: discord.abc.GuildChannel | None = discord.utils.get(
        ctx.guild.channels, name=name
    )
    if existing and isinstance(existing, discord.TextChannel):
        return existing

    try:
        return await ctx.guild.create_text_channel(
            name,
            topic="Configured to receive specific link types",
            reason=f"Created by {ctx.author} via bot command",
        )
    except discord.Forbidden:
        logger.warning(
            "Missing permissions to create channel '%s' in guild %s",
            name,
            ctx.guild.name if ctx.guild else "unknown",
        )
        await ctx.send(
            "❌ I don't have permission to create channels!",
            ephemeral=True,
        )
        return None
    except discord.HTTPException as e:
        logger.error("Error creating channel '%s': %s", name, e)
        await ctx.send(
            f"❌ Error creating channel: {e}",
            ephemeral=True,
        )
        return None


def validate_acls(acls: dict[str, bool]) -> bool:
    """Validate that at least one ACL is enabled.

    Args:
        acls: Dictionary of ACL settings.

    Returns:
        True if at least one ACL is enabled, False otherwise.
    """
    return any(acls.values())


def create_acls(
    youtube: bool = False,
    twitch: bool = False,
    twitter: bool = False,
    instagram: bool = False,
    tiktok: bool = False,
    reddit: bool = False,
    github: bool = False,
    discord_links: bool = False,
    other: bool = False,
) -> dict[str, bool]:
    """Create ACLs dictionary from individual boolean parameters.

    Args:
        youtube: Enable YouTube links.
        twitch: Enable Twitch links.
        twitter: Enable Twitter/X links.
        instagram: Enable Instagram links.
        tiktok: Enable TikTok links.
        reddit: Enable Reddit links.
        github: Enable GitHub links.
        discord_links: Enable Discord invite links.
        other: Enable all other links.

    Returns:
        Dictionary of ACL settings.
    """
    return {PARAM_TO_KEY[param]: locals()[param] for param in PARAM_TO_KEY}
