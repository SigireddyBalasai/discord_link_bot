"""Database manager for Discord bot using DynamoDB (aioboto3) and Pydantic."""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional, Any
from datetime import datetime, timezone

import aioboto3
from boto3.dynamodb.conditions import Key

from core.db.models import GuildSettings, OutputChannel

logger: logging.Logger = logging.getLogger(name=__name__)


class Database:
    """Database manager using DynamoDB for persistent bot state."""

    def __init__(self, table_name: str | None = None) -> None:
        """Initialize the Database manager.

        Args:
            table_name: The name of the DynamoDB table. If None, reads from DYNAMODB_TABLE_NAME env var.
        """
        self.table_name = table_name or os.getenv("DYNAMODB_TABLE_NAME")
        if not self.table_name:
            # Fallback for local testing if env var not set, though it should be.
            logger.warning(
                "DYNAMODB_TABLE_NAME not set, defaulting to 'discord-bot-table'"
            )
            self.table_name = "discord-bot-table"

        self.region_name = os.getenv("AWS_REGION", "us-east-1")
        self._session = aioboto3.Session()
        self._initialized: bool = False

    async def initialize(self) -> None:
        """Initialize the database connection (check table existence)."""
        if self._initialized:
            return

        async with self._session.resource(
            "dynamodb", region_name=self.region_name
        ) as dynamodb:
            table = await dynamodb.Table(self.table_name)
            try:
                # Just check if we can access the table
                await table.load()
                logger.info(f"Connected to DynamoDB table: {self.table_name}")
                self._initialized = True
            except Exception as e:
                logger.error(
                    f"Failed to connect to DynamoDB table {self.table_name}: {e}"
                )
                raise

    async def close(self) -> None:
        """Close database connections."""
        self._initialized = False
        logger.info("Database connection closed")

    @asynccontextmanager
    async def _table(self) -> AsyncGenerator[Any, None]:
        """Provide an async context manager for the DynamoDB table."""
        if not self._initialized:
            await self.initialize()

        async with self._session.resource(
            "dynamodb", region_name=self.region_name
        ) as dynamodb:
            yield await dynamodb.Table(self.table_name)

    # --- Guild Settings ---

    async def get_links_channel(self, guild_id: int) -> Optional[int]:
        """Return the links channel ID for a guild."""
        async with self._table() as table:
            response = await table.get_item(
                Key={"pk": f"GUILD#{guild_id}", "sk": "SETTINGS"}
            )
            item = response.get("Item")
            if item:
                # Validate/Parse with Pydantic (ignoring extra DynamoDB keys like pk/sk for the model)
                settings = GuildSettings(**item)
                return settings.links_channel_id
            return None

    async def set_links_channel(self, guild_id: int, channel_id: int) -> None:
        """Set or update the links channel for a guild."""
        async with self._table() as table:
            # Create model instance
            settings = GuildSettings(
                guild_id=guild_id,
                links_channel_id=channel_id,
                updated_at=datetime.now(timezone.utc),
            )
            # Dump to dict
            item = settings.model_dump()
            # Add DynamoDB keys
            item["pk"] = f"GUILD#{guild_id}"
            item["sk"] = "SETTINGS"
            # Convert datetime to string for DynamoDB
            item["created_at"] = item["created_at"].isoformat()
            item["updated_at"] = item["updated_at"].isoformat()

            await table.put_item(Item=item)
            logger.info("Set links channel %s for guild %s", channel_id, guild_id)

    async def remove_links_channel(self, guild_id: int) -> None:
        """Remove the links channel setting for a guild."""
        async with self._table() as table:
            await table.delete_item(Key={"pk": f"GUILD#{guild_id}", "sk": "SETTINGS"})
            logger.info("Removed links channel setting for guild %s", guild_id)

    # --- Output Channels ---

    async def add_output_channel(
        self, guild_id: int, channel_id: int, **acls: bool
    ) -> OutputChannel:
        """Add or update an output channel with ACL configuration."""
        async with self._table() as table:
            # Get existing to preserve other fields if updating
            response = await table.get_item(
                Key={"pk": f"GUILD#{guild_id}", "sk": f"CHANNEL#{channel_id}"}
            )
            existing_item = response.get("Item", {})

            if existing_item:
                # Update existing
                model = OutputChannel(**existing_item)
                for k, v in acls.items():
                    if hasattr(model, k):
                        setattr(model, k, v)
                model.updated_at = datetime.now(timezone.utc)
            else:
                # Create new
                model = OutputChannel(guild_id=guild_id, channel_id=channel_id)
                for k, v in acls.items():
                    if hasattr(model, k):
                        setattr(model, k, v)

            item = model.model_dump()
            item["pk"] = f"GUILD#{guild_id}"
            item["sk"] = f"CHANNEL#{channel_id}"
            item["created_at"] = item["created_at"].isoformat()
            item["updated_at"] = item["updated_at"].isoformat()

            await table.put_item(Item=item)
            logger.info("Updated output channel %s for guild %s", channel_id, guild_id)
            return model

    async def get_output_channels(
        self, guild_id: int, link_type: Optional[str] = None
    ) -> List[OutputChannel]:
        """Return all output channels for a guild, optionally filtered by link type."""
        async with self._table() as table:
            response = await table.query(
                KeyConditionExpression=Key("pk").eq(f"GUILD#{guild_id}")
                & Key("sk").begins_with("CHANNEL#")
            )
            items = response.get("Items", [])

            channels = []
            for item in items:
                try:
                    channel = OutputChannel(**item)
                    if link_type:
                        if getattr(channel, link_type, False) is True:
                            channels.append(channel)
                    else:
                        channels.append(channel)
                except Exception as e:
                    logger.error(f"Failed to parse output channel item: {e}")

            return channels

    async def get_all_output_channels(self) -> List[OutputChannel]:
        """Return all output channels across all guilds."""
        async with self._table() as table:
            response = await table.scan()
            items = response.get("Items", [])

            channels = []
            for item in items:
                if item.get("sk", "").startswith("CHANNEL#"):
                    try:
                        channels.append(OutputChannel(**item))
                    except Exception:
                        pass
            return channels

    async def get_output_channel(
        self, guild_id: int, channel_id: int
    ) -> Optional[OutputChannel]:
        """Return a specific output channel configuration."""
        async with self._table() as table:
            response = await table.get_item(
                Key={"pk": f"GUILD#{guild_id}", "sk": f"CHANNEL#{channel_id}"}
            )
            item = response.get("Item")
            if item:
                return OutputChannel(**item)
            return None

    async def remove_output_channel(self, guild_id: int, channel_id: int) -> bool:
        """Remove an output channel configuration."""
        async with self._table() as table:
            await table.delete_item(
                Key={"pk": f"GUILD#{guild_id}", "sk": f"CHANNEL#{channel_id}"}
            )
            logger.info("Removed output channel %s for guild %s", channel_id, guild_id)
            return True

    async def update_output_channel_acl(
        self, guild_id: int, channel_id: int, link_type: str, enabled: bool
    ) -> Optional[OutputChannel]:
        """Update the ACL for a specific output channel and link type."""
        # Read-Modify-Write is safer for Pydantic consistency than partial updates
        # unless we want to manually manage timestamps and validation.
        channel = await self.get_output_channel(guild_id, channel_id)
        if channel:
            if hasattr(channel, link_type):
                setattr(channel, link_type, enabled)
                channel.updated_at = datetime.now(timezone.utc)

                async with self._table() as table:
                    item = channel.model_dump()
                    item["pk"] = f"GUILD#{guild_id}"
                    item["sk"] = f"CHANNEL#{channel_id}"
                    item["created_at"] = item["created_at"].isoformat()
                    item["updated_at"] = item["updated_at"].isoformat()
                    await table.put_item(Item=item)
                return channel
        return None

    async def set_webhook_url(
        self, guild_id: int, channel_id: int, webhook_url: str | None
    ) -> None:
        """Store the webhook URL for an output channel."""
        channel = await self.get_output_channel(guild_id, channel_id)
        if channel:
            channel.webhook_url = webhook_url
            channel.updated_at = datetime.now(timezone.utc)

            async with self._table() as table:
                item = channel.model_dump()
                item["pk"] = f"GUILD#{guild_id}"
                item["sk"] = f"CHANNEL#{channel_id}"
                item["created_at"] = item["created_at"].isoformat()
                item["updated_at"] = item["updated_at"].isoformat()
                await table.put_item(Item=item)

    async def get_webhook_url(self, guild_id: int, channel_id: int) -> str | None:
        """Retrieve the webhook URL for an output channel."""
        channel = await self.get_output_channel(guild_id, channel_id)
        if channel:
            return channel.webhook_url
        return None

    async def clear_guild_data(self, guild_id: int) -> None:
        """Delete all settings and output channels for a guild."""
        async with self._table() as table:
            response = await table.query(
                KeyConditionExpression=Key("pk").eq(f"GUILD#{guild_id}")
            )
            items = response.get("Items", [])

            for item in items:
                await table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
            logger.info("Cleared all data for guild %s", guild_id)
