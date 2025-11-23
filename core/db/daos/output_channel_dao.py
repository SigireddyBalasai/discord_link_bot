import logging
from typing import List, Optional
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from core.db.models import OutputChannel
from core.db.daos.guild_settings_dao import BaseDAO

logger = logging.getLogger(__name__)


class OutputChannelDAO(BaseDAO):
    async def add_output_channel(
        self, guild_id: int, channel_id: int, **acls: bool
    ) -> OutputChannel:
        """Add or update an output channel with ACL configuration."""
        async with self._table() as table:
            response = await table.get_item(
                Key={"pk": f"GUILD#{guild_id}", "sk": f"CHANNEL#{channel_id}"}
            )
            existing_item = response.get("Item", {})

            if existing_item:
                model = OutputChannel(**existing_item)
                for k, v in acls.items():
                    if hasattr(model, k):
                        setattr(model, k, v)
                    else:
                        logger.warning("Ignoring invalid ACL key: %s", k)
                model.updated_at = datetime.now(timezone.utc)
            else:
                model = OutputChannel(guild_id=guild_id, channel_id=channel_id)
                for k, v in acls.items():
                    if hasattr(model, k):
                        setattr(model, k, v)
                    else:
                        logger.warning("Ignoring invalid ACL key: %s", k)

            item = model.model_dump()
            item["pk"] = f"GUILD#{guild_id}"
            item["sk"] = f"CHANNEL#{channel_id}"
            item["created_at"] = item["created_at"].isoformat()
            item["updated_at"] = item["updated_at"].isoformat()

            try:
                await table.put_item(Item=item)
                logger.info(
                    "Updated output channel %s for guild %s", channel_id, guild_id
                )
                return model
            except Exception as e:
                logger.error("Failed to save output channel %s: %s", channel_id, e)
                raise

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
                    continue

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
                    except Exception as e:
                        logger.error(
                            f"Failed to parse output channel item during scan: {e}"
                        )
                        continue
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
