"""Database manager for Discord bot using DynamoDB (aioboto3) and Pydantic."""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

import aioboto3
from boto3.dynamodb.conditions import Key

from core.db.daos.guild_settings_dao import GuildSettingsDAO
from core.db.daos.output_channel_dao import OutputChannelDAO

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

        # Initialize DAOs
        self.guild_settings = GuildSettingsDAO(
            self._session, self.table_name, self.region_name
        )
        self.output_channels = OutputChannelDAO(
            self._session, self.table_name, self.region_name
        )

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
