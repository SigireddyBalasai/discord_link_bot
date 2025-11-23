"""
Link monitoring cog for Discord bot.

This module contains the LinkMonitor cog that processes messages for links,
categorizes them, and forwards them to configured output channels.
"""

import logging
from discord.abc import GuildChannel
import discord
from discord.ext import commands
from link_utils.categories import categorize_link
from link_utils.url_tools import extract_urls
from core.db.models import OutputChannel
from core.db.db_manager import Database
from core.bot_setup import DiscordBot

logger: logging.Logger = logging.getLogger(name=__name__)


class LinkMonitor(commands.Cog):
    """Monitor messages for links and send them to a dedicated links channel.

    This cog detects URLs in messages, categorizes them by type (YouTube, Twitch, etc.),
    and forwards them via webhooks to configured output channels based on ACL filters.
    Original messages containing links are deleted to keep channels clean.
    """

    def __init__(self, db: Database) -> None:
        """Initialize the LinkMonitor cog.
        Args:
            db: The database instance for accessing configuration.
        """
        self.db = db

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Log when the cog is ready."""
        logger.info("LinkMonitor cog loaded")

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, message: discord.Message) -> None:
        """Process incoming messages for links and forward them to configured channels.

        Detects URLs in messages, categorizes them, and sends them via webhooks to
        output channels that have the corresponding link type enabled in their ACLs.
        The original message is deleted after successful forwarding.

        Args:
            message: The Discord message to process.
        """
        if message.author.bot or not message.guild:
            return

        if not isinstance(message.channel, (discord.TextChannel, discord.Thread)):
            return

        assert message.guild is not None

        urls: list[str] | None = extract_urls(text=message.content)
        if not urls:
            return

        channel_name = getattr(message.channel, "name", "unknown")
        logger.info(
            "Detected %d URLs in message from %s in #%s (guild: %s)",
            len(urls),
            message.author,
            channel_name,
            message.guild.name,
        )

        output_channels = await self.db.output_channels.get_output_channels(
            message.guild.id
        )
        if not output_channels:
            logger.debug("No output channels configured for guild %s", message.guild.id)
            return

        links_by_category: dict[str, list[str]] = {}
        for url in urls:
            category = categorize_link(url)
            if category not in links_by_category:
                links_by_category[category] = []
            links_by_category[category].append(url)

        logger.debug("Categorized links: %s", links_by_category)

        sent_channels: set[int] = set()

        for output_channel_config in output_channels:
            if output_channel_config.channel_id in sent_channels:
                continue

            output_channel: GuildChannel | None = message.guild.get_channel(
                output_channel_config.channel_id
            )

            if not output_channel or not isinstance(
                output_channel, discord.TextChannel
            ):
                logger.warning(
                    "Output channel %s not found or not a text channel",
                    output_channel_config.channel_id,
                )
                continue

            if await self._forward_links_to_channel(
                message, output_channel, output_channel_config, links_by_category
            ):
                sent_channels.add(output_channel_config.channel_id)

        if sent_channels:
            try:
                await message.delete()
                logger.info("Deleted original message with links in #%s", channel_name)
            except discord.Forbidden:
                channel_name = message.channel.name
                logger.warning("Could not delete message in #%s", channel_name)
            except discord.HTTPException as e:
                logger.error("Error deleting message: %s", e)

    async def _get_or_create_webhook(
        self, channel: discord.TextChannel
    ) -> discord.Webhook | None:
        """Get or create a webhook for the specified channel.

        Searches for existing bot-owned webhooks before creating a new one.

        Args:
            channel: The text channel to get or create a webhook for.

        Returns:
            A Discord webhook instance or None if creation/fetching fails.
        """
        try:
            webhooks = await channel.webhooks()
            bot_user = channel.guild.me
            for webhook in webhooks:
                if webhook.user and bot_user and webhook.user.id == bot_user.id:
                    await self.db.output_channels.set_webhook_url(
                        channel.guild.id, channel.id, webhook.url
                    )
                    logger.debug("Found existing webhook for #%s", channel.name)
                    return webhook
        except discord.Forbidden:
            logger.error("Missing permissions to manage webhooks in #%s", channel.name)
            return None

        try:
            webhook = await channel.create_webhook(name="Link Monitor")
            await self.db.output_channels.set_webhook_url(
                channel.guild.id, channel.id, webhook.url
            )
            logger.info("Created new webhook for #%s", channel.name)
            return webhook
        except discord.Forbidden:
            logger.error("Missing permissions to create webhook in #%s", channel.name)
            return None
        except discord.HTTPException as e:
            logger.error("Error creating webhook: %s", e)
            return None

    async def _forward_links_to_channel(
        self,
        message: discord.Message,
        output_channel: discord.TextChannel,
        output_channel_config: OutputChannel,
        links_by_category: dict[str, list[str]],
    ) -> bool:
        """Forward categorized links to a specific output channel.

        Args:
            message: The original message containing links.
            output_channel: The Discord text channel to send to.
            output_channel_config: The database config for the channel.
            links_by_category: Dict of category to list of URLs.

        Returns:
            True if any links were sent, False otherwise.
        """

        sent = False
        for category, category_urls in links_by_category.items():
            if getattr(output_channel_config, category, False):
                webhook = await self._get_or_create_webhook(output_channel)
                if webhook is None:
                    logger.error(
                        "Could not create webhook for #%s", output_channel.name
                    )
                    continue

                try:
                    avatar_url = (
                        message.author.avatar.url
                        if message.author.avatar
                        else message.author.default_avatar.url
                    )
                    await webhook.send(
                        content="\n".join(category_urls),
                        username=message.author.display_name,
                        avatar_url=avatar_url,
                    )
                    logger.info(
                        "Forwarded %d %s links to #%s",
                        len(category_urls),
                        category,
                        output_channel.name,
                    )
                    sent = True
                except discord.Forbidden:
                    logger.exception("Missing permissions in #%s", output_channel.name)
                except discord.HTTPException as e:
                    logger.exception("Error processing link: %s", e)
        return sent


async def setup(bot: DiscordBot) -> None:
    """Load the LinkMonitor cog into the bot.

    Args:
        bot: The Discord bot instance.
    """
    assert bot.db is not None, "Database not initialized"
    await bot.add_cog(LinkMonitor(bot.db))
