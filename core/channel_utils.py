"""
Shared utilities for Discord bot cogs.

This module contains common functionality used across multiple cogs.
"""

import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


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

    assert ctx.guild is not None  # This function is only called in guild contexts
    existing = discord.utils.get(ctx.guild.channels, name=name)
    if existing and isinstance(existing, discord.TextChannel):
        return existing

    try:
        return await ctx.guild.create_text_channel(
            name,
            topic="Configured to receive specific link types",
            reason=f"Created by {ctx.author} via bot command",
        )
    except discord.Forbidden:
        await ctx.send(
            "❌ I don't have permission to create channels!",
            ephemeral=True,
        )
        return None
    except discord.HTTPException as e:
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
    return {
        "youtube": youtube,
        "twitch": twitch,
        "twitter": twitter,
        "instagram": instagram,
        "tiktok": tiktok,
        "reddit": reddit,
        "github": github,
        "discord": discord_links,
        "other": other,
    }