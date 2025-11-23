"""Pydantic models for Discord bot database."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class GuildSettings(BaseModel):
    """Guild-specific settings."""

    guild_id: int
    links_channel_id: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OutputChannel(BaseModel):
    """Output channel configuration with ACLs for link types."""

    guild_id: int
    channel_id: int
    webhook_url: Optional[str] = None
    youtube: bool = False
    twitch: bool = False
    twitter: bool = False
    instagram: bool = False
    tiktok: bool = False
    reddit: bool = False
    github: bool = False
    discord: bool = False
    other: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
