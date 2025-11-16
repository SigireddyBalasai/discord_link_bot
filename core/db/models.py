"""ORM models for Discord bot database."""
import logging
from tortoise.fields import (
    BigIntField,
    BooleanField,
    CharField,
    DatetimeField,
    IntField,
)
from tortoise.models import Model
from logging import Logger

logger: Logger = logging.getLogger(name=__name__)


class GuildSettings(Model):
    """Guild-specific settings."""

    guild_id = BigIntField(pk=True)
    links_channel_id = BigIntField(null=True)
    created_at = DatetimeField(auto_now_add=True)
    updated_at = DatetimeField(auto_now=True)

    class Meta(Model.Meta):
        table = "guild_settings"


class OutputChannel(Model):
    """Output channel configuration with ACLs for link types."""

    id = IntField(pk=True)
    guild_id = BigIntField()
    channel_id = BigIntField()
    webhook_url = CharField(max_length=200, null=True)
    youtube = BooleanField(default=False)
    twitch = BooleanField(default=False)
    twitter = BooleanField(default=False)
    instagram = BooleanField(default=False)
    tiktok = BooleanField(default=False)
    reddit = BooleanField(default=False)
    github = BooleanField(default=False)
    discord = BooleanField(default=False)
    other = BooleanField(default=False)
    created_at = DatetimeField(auto_now_add=True)
    updated_at = DatetimeField(auto_now=True)

    class Meta(Model.Meta):
        table = "output_channels"
        unique_together = (("guild_id", "channel_id"),)
