"""
Link management cog for Discord bot.

This module contains the LinkManager cog that provides commands for configuring
link forwarding channels and ACLs for different link types.
"""

import logging
import discord
from discord.ext import commands
from discord import ui
from core.db.models import OutputChannel
from core.db.db_manager import Database
from core.channel_utils import (
    get_or_create_channel,
    validate_acls,
    create_acls,
    LINK_TYPES,
)
from core.bot_setup import DiscordBot

logger: logging.Logger = logging.getLogger(name=__name__)


class ChannelSelectView(ui.View):
    """View for selecting a channel or creating a new one."""

    def __init__(
        self, cog: "LinkManager", ctx: commands.Context, acls: dict[str, bool]
    ) -> None:
        super().__init__(timeout=300)  # 5 minutes timeout
        self.cog = cog
        self.ctx = ctx
        self.acls = acls

    @ui.select(
        placeholder="Select a channel or create a new one...",
        options=[],
    )
    async def channel_select(
        self, interaction: discord.Interaction, select: ui.Select
    ) -> None:
        """Handle channel selection."""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "❌ Only the command author can use this menu!", ephemeral=True
            )
            return

        selected_value: str = select.values[0]

        if selected_value == "create_new":
            await interaction.response.send_modal(
                ChannelNameModal(self.cog, self.ctx, self.acls)
            )
        elif selected_value == "too_many":
            await interaction.response.send_message(
                "❌ This server has too many channels to display in the menu. Please contact an administrator to create channels manually.",
                ephemeral=True,
            )
        else:
            # Use existing channel
            if self.ctx.guild is None:
                await interaction.response.send_message(
                    "❌ This command can only be used in a server!", ephemeral=True
                )
                return
            channel_id: int = int(selected_value)
            channel: discord.TextChannel | None = self.ctx.guild.get_channel(channel_id)
            if channel is None or not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message(
                    "❌ Channel not found or not a text channel!", ephemeral=True
                )
                return

            await self.cog._configure_channel(interaction, channel, self.acls)


class ChannelNameModal(ui.Modal, title="Create New Channel"):
    """Modal for entering a new channel name."""

    channel_name = ui.TextInput(
        label="Channel Name",
        placeholder="Enter channel name (without #)",
        required=True,
        max_length=100,
    )

    def __init__(
        self, cog: "LinkManager", ctx: commands.Context, acls: dict[str, bool]
    ) -> None:
        super().__init__()
        self.cog = cog
        self.ctx = ctx
        self.acls = acls

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission."""
        channel_name: str = str(self.channel_name).strip()
        if not channel_name:
            await interaction.response.send_message(
                "❌ Channel name cannot be empty!", ephemeral=True
            )
            return

        channel: discord.TextChannel | None = await get_or_create_channel(
            self.ctx, channel_name
        )
        if channel is None:
            await interaction.response.send_message(
                "❌ Failed to create channel!", ephemeral=True
            )
            return

        await self.cog._configure_channel(interaction, channel, self.acls)


class LinkManager(commands.Cog):
    """Manage link forwarding configuration for the server.

    This cog provides commands to configure channels for receiving forwarded links,
    set link type filters, and manage the bot's link monitoring settings.
    """

    def __init__(self, db: Database) -> None:
        """Initialize the LinkManager cog.
        Args:
            db: The database instance for accessing configuration.
        """
        self.db = db

    async def _configure_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        acls: dict[str, bool],
    ) -> None:
        """Configure a channel with the given ACLs.

        Args:
            interaction: The Discord interaction.
            channel: The text channel to configure.
            acls: Dictionary of link type ACLs.
        """
        assert interaction.guild is not None
        try:
            await self.db.output_channels.add_output_channel(interaction.guild.id, channel.id, **acls)

            enabled_types = [name for name, enabled in acls.items() if enabled]
            action = "configured"

            await interaction.response.send_message(
                f"✅ Output Channel {action.title()}\n{channel.mention} will now receive:\n"
                + "\n".join(f"• {t.capitalize()}" for t in enabled_types),
                ephemeral=True,
            )
            logger.info(
                "Successfully %s output channel #%s in guild %s with ACLs: %s",
                action,
                channel.name,
                interaction.guild.name,
                enabled_types,
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Error adding output channel: {e}",
                ephemeral=True,
            )

    @commands.hybrid_command(
        name="add_link_channel",
        description="Add or configure a channel to receive specific types of links.",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)  # pyrefly: ignore
    async def add_output(
        self,
        ctx: commands.Context,
        youtube: bool = False,
        twitch: bool = False,
        twitter: bool = False,
        instagram: bool = False,
        tiktok: bool = False,
        reddit: bool = False,
        github: bool = False,
        discord_links: bool = False,
        other: bool = False,
    ) -> None:
        """Add or update an output channel with ACL configuration.

        Select a channel to receive specific link types. At least one link type must be enabled.

        Args:
            ctx: The command context.
            youtube: Enable YouTube links.
            twitch: Enable Twitch links.
            twitter: Enable Twitter/X links.
            instagram: Enable Instagram links.
            tiktok: Enable TikTok links.
            reddit: Enable Reddit links.
            github: Enable GitHub links.
            discord_links: Enable Discord invite links.
            other: Enable all other links.
        """
        assert ctx.guild is not None
        logger.info(
            "User %s in guild %s executing add_output command",
            ctx.author,
            ctx.guild.name,
        )

        acls = create_acls(
            youtube=youtube,
            twitch=twitch,
            twitter=twitter,
            instagram=instagram,
            tiktok=tiktok,
            reddit=reddit,
            github=github,
            discord_links=discord_links,
            other=other,
        )

        if not validate_acls(acls):
            await ctx.send(
                "❌ You must enable at least one link type!",
                ephemeral=True,
            )
            return

        options = []
        for channel in ctx.guild.text_channels:
            options.append(
                discord.SelectOption(
                    label=f"#{channel.name}",
                    value=str(channel.id),
                    description=f"Configure existing channel #{channel.name}",
                )
            )

        options.append(
            discord.SelectOption(
                label="➕ Create New Channel",
                value="create_new",
                description="Create a new channel for link forwarding",
            )
        )

        if len(options) > 25:
            options = options[:24]
            options.append(
                discord.SelectOption(
                    label="⚠️ Too many channels",
                    value="too_many",
                    description="Server has too many channels to display",
                )
            )

        view = ChannelSelectView(self, ctx, acls)
        view.channel_select.options = options

        await ctx.send(
            "Select a channel to configure for link forwarding:",
            view=view,
        )

    @commands.hybrid_command(
        name="remove_link_channel",
        description="Remove a channel from receiving forwarded links.",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)  # pyrefly: ignore
    async def remove_output(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
    ) -> None:
        """Remove an output channel configuration.

        Args:
            ctx: The command context.
            channel: The channel to remove from output channel list.
        """
        assert ctx.guild is not None
        logger.info(
            "User %s in guild %s executing remove_output command for channel #%s",
            ctx.author,
            ctx.guild.name,
            channel.name,
        )

        success = await self.db.output_channels.remove_output_channel(ctx.guild.id, channel.id)

        if success:
            await ctx.send(
                f"✅ Output Channel Removed\n{channel.mention} will no longer receive links.",
                ephemeral=True,
            )
            logger.info(
                "Successfully removed output channel #%s in guild %s",
                channel.name,
                ctx.guild.name,
            )
        else:
            await ctx.send(
                f"❌ {channel.mention} is not configured as an output channel.",
                ephemeral=True,
            )
            logger.warning(
                "Failed to remove output channel #%s in guild %s - not configured",
                channel.name,
                ctx.guild.name,
            )

    @commands.hybrid_command(
        name="list_link_channels",
        description="Show all channels set to receive forwarded links and their filters.",
    )
    @commands.guild_only()
    async def list_outputs(self, ctx: commands.Context) -> None:
        """List all configured output channels and their ACL settings.

        Args:
            ctx: The command context.
        """
        assert ctx.guild is not None
        output_channels: list[OutputChannel] = await self.db.output_channels.get_output_channels(
            ctx.guild.id
        )

        if not output_channels:
            await ctx.send(
                "❌ No output channels configured. Use `/add_link_channel` to add one.",
                ephemeral=True,
            )
            return

        response = "📤 Output Channels\nConfigured output channels and their link type filters:\n"

        for config in output_channels:
            channel = ctx.guild.get_channel(config.channel_id)
            if not channel or not isinstance(channel, discord.TextChannel):
                continue

            enabled_types = []
            for link_type in LINK_TYPES:
                if getattr(config, link_type, False):
                    enabled_types.append(link_type.capitalize())

            response += f"\n#{channel.name}: {', '.join(enabled_types) if enabled_types else 'None'}"

        await ctx.send(response, ephemeral=True)

    @commands.hybrid_command(
        name="set_link_filter",
        description="Enable or disable a specific link type for a channel.",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)  # pyrefly: ignore
    async def update_acl(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        link_type: str,
        enabled: bool,
    ) -> None:
        """Update a specific ACL for an output channel.

        Args:
            ctx: The command context.
            channel: The output channel to update.
            link_type: The link type (youtube, twitch, twitter, instagram, tiktok, reddit, github, discord, other).
            enabled: Whether to enable or disable this link type.
        """
        assert ctx.guild is not None
        valid_types = LINK_TYPES
        link_type = link_type.lower()

        if link_type not in valid_types:
            await ctx.send(
                f"❌ Invalid link type. Valid types: {', '.join(valid_types)}",
                ephemeral=True,
            )
            return

        result = await self.db.output_channels.update_output_channel_acl(
            ctx.guild.id,
            channel.id,
            link_type,
            enabled,
        )

        if result:
            status = "enabled" if enabled else "disabled"
            await ctx.send(
                f"✅ ACL Updated\n{link_type.capitalize()} links are now {status} for {channel.mention}",
                ephemeral=True,
            )
        else:
            await ctx.send(
                f"❌ {channel.mention} is not configured as an output channel. Use `/addoutput` first.",
                ephemeral=True,
            )

    @commands.hybrid_command(
        name="quick_link_setup",
        description="Create a channel that receives all link types in one step.",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)  # pyrefly: ignore
    async def quick_setup(
        self, ctx: commands.Context, channel_name: str = "links"
    ) -> None:
        """Quick setup to create a channel that receives all link types.

        Creates a new channel (or uses an existing one with the same name)
        and enables all link type filters for easy one-step configuration.

        Args:
            ctx: The command context.
            channel_name: Name for the links channel (default: "links").
        """
        assert ctx.guild is not None
        channel = await get_or_create_channel(ctx, channel_name)
        if channel is None:
            return

        try:
            acls = {link_type: True for link_type in LINK_TYPES}
            await self.db.output_channels.add_output_channel(ctx.guild.id, channel.id, **acls)

            await ctx.send(
                f"✅ Quick Setup Complete!\n{channel.mention} is now configured to receive all link types!\n\n"
                f"All links posted in this server will be forwarded to this channel.\n\n"
                f"Use `/listoutputs` to see the configuration.\n"
                f"Use `/updateacl` to modify link type filters.",
                ephemeral=True,
            )

            welcome_embed = discord.Embed(
                title="🔗 Links Channel Ready!",
                description="All links shared in this server will be posted here automatically.",
                color=discord.Color.green(),
            )
            await channel.send(embed=welcome_embed)
        except discord.HTTPException as e:
            await ctx.send(
                f"❌ Error configuring channel: {e}",
                ephemeral=True,
            )

    @commands.hybrid_command(
        name="support",
        description="Get the link to the support server.",
    )
    async def support(self, ctx: commands.Context) -> None:
        """Get the support server link.

        Args:
            ctx: The command context.
        """
        await ctx.send(
            "Join our support server: https://discord.gg/WYJUCbENFu",
            ephemeral=True,
        )

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Handle errors for all commands in this cog.

        Args:
            ctx: The command context.
            error: The exception that was raised.
        """
        try:
            if isinstance(error, commands.MissingPermissions):
                await ctx.send(
                    "❌ You don't have permission to manage channels!",
                    ephemeral=True,
                )
            elif isinstance(error, commands.BadArgument):
                await ctx.send(
                    "❌ Invalid argument provided. Please check the command usage.",
                    ephemeral=True,
                )
            else:
                await ctx.send(
                    f"❌ An error occurred: {error}",
                    ephemeral=True,
                )
                logger.error("Command error in LinkManager: %s", error)
        except discord.NotFound:
            logger.warning(
                "Could not send error message - interaction expired: %s", error
            )
        except discord.HTTPException as e:
            logger.error("Error in error handler: %s", e)


async def setup(bot: DiscordBot) -> None:
    """Load the LinkManager cog into the bot.

    Args:
        bot: The Discord bot instance.
    """
    assert bot.db is not None, "Database not initialized"
    await bot.add_cog(LinkManager(bot.db))
