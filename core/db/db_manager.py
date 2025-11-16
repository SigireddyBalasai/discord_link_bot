"""Database manager for Discord bot using Tortoise ORM."""

import logging
from contextlib import asynccontextmanager
from types import ModuleType
from typing import AsyncGenerator, Iterable, List, Optional
from tortoise import Tortoise, queryset
from tortoise.exceptions import OperationalError
from core.db.models import GuildSettings, OutputChannel

logger: logging.Logger = logging.getLogger(name=__name__)


class Database:
    """Database manager using Tortoise ORM for persistent bot state."""

    def __init__(self, db_path: str = "core/data/bot_data.db") -> None:
        """Initialize the Database manager with the given database path."""
        self.db_path: str = db_path
        self._initialized: bool = False

    async def initialize(self) -> None:
        """Initialize the Tortoise ORM database and create tables."""
        if self._initialized:
            logger.warning("Database already initialized")
            return

        db_url: str = f"sqlite://{self.db_path}"
        modules: dict[str, Iterable[str | ModuleType]] = {"models": ["core.db.models"]}

        try:
            await Tortoise.init(db_url=db_url, modules=modules)
            await Tortoise.generate_schemas()
            self._initialized: bool = True
            logger.info("Database initialized successfully (Tortoise ORM)")
        except OperationalError as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def close(self) -> None:
        """Close all database connections."""
        if not self._initialized:
            return
        await Tortoise.close_connections()
        self._initialized: bool = False
        logger.info("Database connections closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[None, None]:
        """Provide an async context manager for database operations."""
        if not self._initialized:
            await self.initialize()
        try:
            yield
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise

    async def get_links_channel(self, guild_id: int) -> Optional[int]:
        """Return the links channel ID for a guild, or None if not set."""
        async with self.session():
            guild: GuildSettings | None = await GuildSettings.get_or_none(
                guild_id=guild_id
            )
            if guild:
                logger.debug(
                    "Retrieved links channel %s for guild %s",
                    guild.links_channel_id,
                    guild_id,
                )
                return guild.links_channel_id
            logger.debug("No links channel set for guild %s", guild_id)
            return None

    async def set_links_channel(self, guild_id: int, channel_id: int) -> None:
        """Set or update the links channel for a guild."""
        async with self.session():
            result: tuple[GuildSettings, bool] = await GuildSettings.get_or_create(
                guild_id=guild_id, defaults={"links_channel_id": channel_id}
            )
            guild: GuildSettings = result[0]
            created: bool = result[1]
            if not created:
                guild.links_channel_id = channel_id
                await guild.save()
            action = "created" if created else "updated"
            logger.info(
                "Links channel %s for guild %s (%s)", action, guild_id, channel_id
            )
            action = "created" if created else "updated"
            logger.info(
                "Links channel %s %s for guild %s", action, channel_id, guild_id
            )

    async def remove_links_channel(self, guild_id: int) -> None:
        """Remove the links channel setting for a guild."""
        async with self.session():
            deleted_count: int = await GuildSettings.filter(guild_id=guild_id).delete()
            if deleted_count > 0:
                logger.info("Removed links channel setting for guild %s", guild_id)
            else:
                logger.debug(
                    "No links channel setting found to remove for guild %s", guild_id
                )

    async def add_output_channel(
        self, guild_id: int, channel_id: int, **acls: bool
    ) -> OutputChannel:
        """Add or update an output channel with ACL configuration for a guild."""
        async with self.session():
            result: tuple[OutputChannel, bool] = await OutputChannel.get_or_create(
                guild_id=guild_id, channel_id=channel_id, defaults=acls
            )
            channel: OutputChannel = result[0]
            created: bool = result[1]
            if not created:
                for key, value in acls.items():
                    setattr(channel, key, value)
                await channel.save()
            action = "created" if created else "updated"
            enabled_types = [k for k, v in acls.items() if v]
            logger.info(
                "Output channel %s %s for guild %s with types: %s",
                action,
                channel_id,
                guild_id,
                enabled_types,
            )
            return channel

    async def get_output_channels(
        self, guild_id: int, link_type: Optional[str] = None
    ) -> List[OutputChannel]:
        """Return all output channels for a guild, optionally filtered by link type."""
        async with self.session():
            query: queryset.QuerySet[OutputChannel] = OutputChannel.filter(
                guild_id=guild_id
            )
            if link_type:
                query: queryset.QuerySet[OutputChannel] = query.filter(
                    **{link_type: True}
                )
            channels = await query.all()
            filter_desc = f" filtered by {link_type}" if link_type else ""
            logger.debug(
                "Retrieved %d output channels for guild %s%s",
                len(channels),
                guild_id,
                filter_desc,
            )
            return channels

    async def get_all_output_channels(self) -> List[OutputChannel]:
        """Return all output channels across all guilds."""
        async with self.session():
            channels = await OutputChannel.all()
            logger.debug("Retrieved %d output channels from all guilds", len(channels))
            return channels

    async def get_output_channel(
        self, guild_id: int, channel_id: int
    ) -> Optional[OutputChannel]:
        """Return a specific output channel configuration for a guild and channel."""
        async with self.session():
            channel = await OutputChannel.get_or_none(
                guild_id=guild_id, channel_id=channel_id
            )
            if channel:
                logger.debug(
                    "Retrieved output channel config for guild %s channel %s",
                    guild_id,
                    channel_id,
                )
            else:
                logger.debug(
                    "No output channel config found for guild %s channel %s",
                    guild_id,
                    channel_id,
                )
            return channel

    async def remove_output_channel(self, guild_id: int, channel_id: int) -> bool:
        """Remove an output channel configuration for a guild and channel."""
        async with self.session():
            deleted_count: int = await OutputChannel.filter(
                guild_id=guild_id, channel_id=channel_id
            ).delete()
            if deleted_count > 0:
                logger.info(
                    "Removed output channel %s for guild %s", channel_id, guild_id
                )
            else:
                logger.debug(
                    "No output channel %s found to remove for guild %s",
                    channel_id,
                    guild_id,
                )
            return deleted_count > 0

    async def update_output_channel_acl(
        self, guild_id: int, channel_id: int, link_type: str, enabled: bool
    ) -> Optional[OutputChannel]:
        """Update the ACL for a specific output channel and link type."""
        async with self.session():
            channel: OutputChannel | None = await OutputChannel.get_or_none(
                guild_id=guild_id, channel_id=channel_id
            )
            if channel:
                setattr(channel, link_type, enabled)
                await channel.save()
                logger.info(
                    "Updated ACL for channel %s in guild %s: %s=%s",
                    channel_id,
                    guild_id,
                    link_type,
                    enabled,
                )
            else:
                logger.warning(
                    "Attempted to update ACL for non-existent channel %s in guild %s",
                    channel_id,
                    guild_id,
                )
            return channel

    async def set_webhook_url(
        self, guild_id: int, channel_id: int, webhook_url: str | None
    ) -> None:
        """Store the webhook URL for an output channel."""
        async with self.session():
            channel: OutputChannel | None = await OutputChannel.get_or_none(
                guild_id=guild_id, channel_id=channel_id
            )
            if channel:
                channel.webhook_url = webhook_url  # type: ignore[assignment]
                await channel.save()
                if webhook_url:
                    logger.debug(
                        "Stored webhook URL for channel %s in guild %s",
                        channel_id,
                        guild_id,
                    )
                else:
                    logger.debug(
                        "Cleared webhook URL for channel %s in guild %s",
                        channel_id,
                        guild_id,
                    )
            else:
                logger.warning(
                    "Attempted to set webhook URL for non-existent channel %s in guild %s",
                    channel_id,
                    guild_id,
                )

    async def get_webhook_url(self, guild_id: int, channel_id: int) -> str | None:
        """Retrieve the webhook URL for an output channel."""
        async with self.session():
            channel: OutputChannel | None = await OutputChannel.get_or_none(
                guild_id=guild_id, channel_id=channel_id
            )
            if channel and channel.webhook_url:
                logger.debug(
                    "Retrieved webhook URL for channel %s in guild %s",
                    channel_id,
                    guild_id,
                )
                return channel.webhook_url
            return None

    async def clear_guild_data(self, guild_id: int) -> None:
        """Delete all settings and output channels for a guild."""
        async with self.session():
            await GuildSettings.filter(guild_id=guild_id).delete()
            await OutputChannel.filter(guild_id=guild_id).delete()
            logger.info("Cleared all data for guild %s", guild_id)
