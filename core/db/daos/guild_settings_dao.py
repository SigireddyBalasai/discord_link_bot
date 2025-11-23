import logging
from typing import Optional, Any, AsyncGenerator
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from core.db.models import GuildSettings

logger = logging.getLogger(__name__)

class BaseDAO:
    def __init__(self, session: Any, table_name: str, region_name: str):
        self._session = session
        self.table_name = table_name
        self.region_name = region_name

    @asynccontextmanager
    async def _table(self) -> AsyncGenerator[Any, None]:
        """Provide an async context manager for the DynamoDB table."""
        async with self._session.resource(
            "dynamodb", region_name=self.region_name
        ) as dynamodb:
            yield await dynamodb.Table(self.table_name)

class GuildSettingsDAO(BaseDAO):
    async def get_links_channel(self, guild_id: int) -> Optional[int]:
        """Return the links channel ID for a guild."""
        async with self._table() as table:
            response = await table.get_item(
                Key={"pk": f"GUILD#{guild_id}", "sk": "SETTINGS"}
            )
            item = response.get("Item")
            if item:
                settings = GuildSettings(**item)
                return settings.links_channel_id
            return None

    async def set_links_channel(self, guild_id: int, channel_id: int) -> None:
        """Set or update the links channel for a guild."""
        async with self._table() as table:
            settings = GuildSettings(
                guild_id=guild_id,
                links_channel_id=channel_id,
                updated_at=datetime.now(timezone.utc),
            )
            item = settings.model_dump()
            item["pk"] = f"GUILD#{guild_id}"
            item["sk"] = "SETTINGS"
            item["created_at"] = item["created_at"].isoformat()
            item["updated_at"] = item["updated_at"].isoformat()

            await table.put_item(Item=item)
            logger.info("Set links channel %s for guild %s", channel_id, guild_id)

    async def remove_links_channel(self, guild_id: int) -> None:
        """Remove the links channel setting for a guild."""
        async with self._table() as table:
            await table.delete_item(Key={"pk": f"GUILD#{guild_id}", "sk": "SETTINGS"})
            logger.info("Removed links channel setting for guild %s", guild_id)
