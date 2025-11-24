"""
Custom help command for Discord bot.

Provides a clean, embed-based help interface for both prefix and slash commands.
"""

import discord
from discord import app_commands
from discord.ext import commands
from collections.abc import Mapping


class CustomHelpCommand(commands.HelpCommand, commands.Cog):
    """Custom help command with embed-based display.
    
    Inherits from both HelpCommand and Cog to support both prefix and slash commands.
    """

    def __init__(self) -> None:
        """Initialize the custom help command."""
        super().__init__(
            command_attrs={
                "help": "Shows help information for commands",
                "aliases": ["h"],
            }
        )

    def _add_to_bot(self, bot: commands.Bot) -> None:
        """Add the help command to the bot and register the slash command.
        
        Args:
            bot: The bot instance to add the command to.
        """
        super()._add_to_bot(bot)
        self.bot = bot
        bot.tree.add_command(self._app_command_callback)

    def _remove_from_bot(self, bot: commands.Bot) -> None:
        """Remove the help command from the bot and unregister the slash command.
        
        Args:
            bot: The bot instance to remove the command from.
        """
        super()._remove_from_bot(bot)
        bot.tree.remove_command(self._app_command_callback.name)

    @app_commands.command(name="help", description="Shows help information for commands")
    @app_commands.describe(command="The command to get help for")
    async def _app_command_callback(
        self, interaction: discord.Interaction, command: str | None = None
    ) -> None:
        """Application command callback for /help.
        
        This bridges the slash command to the prefix help command.
        
        Args:
            interaction: The interaction that triggered this command.
            command: Optional command name to get help for.
        """
        await interaction.response.defer(ephemeral=False)
        bot = interaction.client
        ctx = await commands.Context.from_interaction(interaction)
        ctx.bot = bot
        await ctx.invoke(bot.get_command("help"), command=command)

    async def send_bot_help(
        self, mapping: Mapping[commands.Cog | None, list[commands.Command]]
    ) -> None:
        """Send help for all commands.

        Args:
            mapping: Mapping of cogs to commands.
        """
        embed = discord.Embed(
            title="🔗 Discord Link Bot - Help",
            description="A bot that monitors and forwards links to dedicated channels.",
            color=discord.Color.blue(),
        )

        # Add bot info
        if self.context.bot.user:
            embed.set_thumbnail(url=self.context.bot.user.display_avatar.url)

        embed.add_field(
            name="📖 Usage",
            value="Use `!help <command>` or `/help <command>` for more info on a command.",
            inline=False,
        )

        for cog, cog_commands in mapping.items():
            filtered = await self.filter_commands(cog_commands, sort=True)
            if not filtered:
                continue

            cog_name = getattr(cog, "qualified_name", "Other")
            command_list = ", ".join(f"`{c.name}`" for c in filtered)

            embed.add_field(
                name=f"**{cog_name}**",
                value=command_list or "No commands",
                inline=False,
            )

        embed.set_footer(text="Use !help <command> for detailed information")

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command) -> None:
        """Send help for a specific command.

        Args:
            command: The command to show help for.
        """
        embed = discord.Embed(
            title=f"Command: {command.name}",
            description=command.help or "No description available.",
            color=discord.Color.blue(),
        )

        # Add usage
        if command.signature:
            embed.add_field(
                name="Usage",
                value=f"`!{command.name} {command.signature}`",
                inline=False,
            )
        else:
            embed.add_field(
                name="Usage",
                value=f"`!{command.name}`",
                inline=False,
            )

        # Add aliases
        if command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in command.aliases),
                inline=False,
            )

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group) -> None:
        """Send help for a command group.

        Args:
            group: The command group to show help for.
        """
        embed = discord.Embed(
            title=f"Command Group: {group.name}",
            description=group.help or "No description available.",
            color=discord.Color.blue(),
        )

        # Add subcommands
        if group.commands:
            subcommands = await self.filter_commands(group.commands, sort=True)
            if subcommands:
                command_list = "\n".join(
                    f"`{c.name}` - {c.short_doc or 'No description'}"
                    for c in subcommands
                )
                embed.add_field(
                    name="Subcommands",
                    value=command_list,
                    inline=False,
                )

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        """Send help for a cog.

        Args:
            cog: The cog to show help for.
        """
        embed = discord.Embed(
            title=f"Category: {cog.qualified_name}",
            description=cog.description or "No description available.",
            color=discord.Color.blue(),
        )

        # Add commands
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        if filtered:
            command_list = "\n".join(
                f"`{c.name}` - {c.short_doc or 'No description'}" for c in filtered
            )
            embed.add_field(
                name="Commands",
                value=command_list,
                inline=False,
            )

        await self.get_destination().send(embed=embed)
