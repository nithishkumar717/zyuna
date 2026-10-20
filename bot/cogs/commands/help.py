# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                  ║
# ║   ░█▄░█░█▀▀░█▀▄░█▀▄   ░█░█   ░█░░░▀█▀░█░█░█▀▀                 ║
# ║   ░█░▀█░█▀▀░█▀▄░█░█   ░▄▀▄   ░█░░░░█░░▀▄▀░█▀▀                 ║
# ║   ░▀░░▀░▀▀▀░▀░▀░▀▀░   ░▀░▀   ░▀▀▀░▀█▀░░▀░░▀▀▀                 ║
# ║                                                                  ║
# ║            © 2026 Nerd X Live — All Rights Reserved             ║
# ║                                                                  ║
# ║   discord  ──  https://discord.gg/YzHCx5yQXv                    ║
# ║   github   ──  https://github.com/nithishkumar717/zyuna         ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

import discord
import asyncio
from difflib import get_close_matches
from contextlib import suppress
from discord.ext import commands

try:
    from bot.core import Context, zyuna
    from bot.core.Cog import Cog
    from bot.utils.Tools import getConfig, ignore_check, blacklist_check
    from bot.utils.emoji import LOADINGRED, TICK, CROSS
    from bot.utils.config import serverLink, websiteLink, BotName, BRAND_NAME
    from bot.utils.cv2 import CV2, CV2Embed
    from bot.utils import help as vhelp
except (ImportError, ModuleNotFoundError):
    from core import Context, zyuna
    from core.Cog import Cog
    from utils.Tools import getConfig, ignore_check, blacklist_check
    from utils.emoji import LOADINGRED, TICK, CROSS
    from utils.config import serverLink, websiteLink, BotName, BRAND_NAME
    from utils.cv2 import CV2, CV2Embed
    from utils import help as vhelp

ACCENT_COLOR = 0xFF2A4D


class HelpCommand(commands.HelpCommand):
    """Next-Generation Components V2 (CV2) Command Help Engine."""

    async def send_ignore_message(self, ctx, ignore_type: str):
        if ignore_type == "channel":
            await ctx.reply("❌ This channel is currently ignored by the bot.", mention_author=False)
        elif ignore_type == "command":
            await ctx.reply(f"{ctx.author.mention} This command or channel has been restricted.", delete_after=6)
        elif ignore_type == "user":
            await ctx.reply("❌ You are currently blacklisted from using bot commands.", mention_author=False)

    async def on_help_command_error(self, ctx, error):
        errors = [
            commands.CommandOnCooldown, commands.CommandNotFound,
            discord.HTTPException, commands.CommandInvokeError
        ]
        if not type(error) in errors:
            await self.context.reply(f"Unknown Help Error: {getattr(error, 'original', error)}", mention_author=False)
        else:
            if isinstance(error, commands.CommandOnCooldown):
                return
        return await super().on_help_command_error(ctx, error)

    async def command_not_found(self, string: str) -> None:
        ctx = self.context
        check_ignore = await ignore_check().predicate(ctx)
        check_blacklist = await blacklist_check().predicate(ctx)

        if not check_blacklist or not check_ignore:
            return

        cmds = [str(cmd) for cmd in self.context.bot.walk_commands()]
        matches = get_close_matches(string, cmds, n=3, cutoff=0.55)

        prefix = ctx.prefix or ">"
        desc = f"> Ops! Could not find any command matching `{string}`."
        if matches:
            suggestions = " • ".join(f"`{prefix}{m}`" for m in matches)
            desc += f"\n\n💡 **Did you mean:** {suggestions}"
        desc += f"\n\n-# Run `{prefix}help` to explore the full interactive Command Center."

        embed = CV2Embed(
            title=f"# 🔍 Command Not Found",
            description=desc,
            color=ACCENT_COLOR
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name} • Support: {serverLink}")
        await ctx.reply(view=embed, mention_author=False)

    async def send_bot_help(self, mapping):
        ctx = self.context
        check_ignore = await ignore_check().predicate(ctx)
        check_blacklist = await blacklist_check().predicate(ctx)

        if not check_blacklist:
            return
        if not check_ignore:
            await self.send_ignore_message(ctx, "command")
            return

        # Smooth Loading Indicator
        loading_embed = CV2(f"{LOADINGRED} Initializing {BRAND_NAME} Command Center...")
        loading_msg = await ctx.reply(view=loading_embed)

        await asyncio.sleep(0.3)
        with suppress(discord.NotFound):
            await loading_msg.delete()

        # Telemetry & Configuration
        try:
            data = await getConfig(self.context.guild.id)
            prefix = data.get("prefix", ">")
        except Exception:
            prefix = self.context.prefix or ">"

        total_commands = len(set(self.context.bot.walk_commands()))
        active_cogs = len(self.context.bot.cogs)
        latency_ms = round(self.context.bot.latency * 1000)

        # High-Aesthetic Home Embed Card
        embed = CV2Embed(
            title=f"# ✨ {BRAND_NAME} System Operations • Command Center",
            description=(
                f"> High-performance Discord architecture featuring high-fidelity studio audio, "
                f"interactive web dashboard synchronization, and next-generation server engagement.\n\n"
                f"### 📊 System Telemetry\n"
                f"• **Prefix:** `{prefix}` | **Version:** `v7.02 Core` | **Latency:** `{latency_ms}ms`\n"
                f"• **Commands Available:** `{total_commands}` | **Active Modules:** `{active_cogs} Systems`\n"
                f"• **Architecture:** `Discord Components V2 (CV2)` | **Cluster:** `Operational`\n\n"
                f"### 🧭 Module Directory\n"
                f"🎵 **`Studio Audio`** `»` Music Playback • Audio FX Filters • Queue Management • Search\n"
                f"⚔️ **`Server Governance`** `»` Tickets • Member Verification\n"
                f"💎 **`Community & Celebrations`** `»` Birthdays • Giveaways • Boost Roles\n\n"
                f"### ⚡ Quick Deployment\n"
                f"• `{prefix}play <query>` `»` *Play high-fidelity music from YouTube/Spotify*\n"
                f"• `{prefix}ticket setup` `»` *Deploy interactive user ticket panel*\n"
                f"• `{prefix}verification setup` `»` *Deploy secure member verification gate*\n\n"
                f"### 🕹️ Interactive Navigation\n"
                f"Select any category from the dropdowns below or use the navigation bar."
            ),
            color=ACCENT_COLOR
        )
        embed.set_footer(text=f"Requested By {self.context.author.display_name} • Support: {serverLink}")

        view = vhelp.View(mapping=mapping, ctx=self.context, homeembed=embed, ui=2)
        await ctx.reply(view=view, mention_author=False)

    async def send_command_help(self, command):
        ctx = self.context
        check_ignore = await ignore_check().predicate(ctx)
        check_blacklist = await blacklist_check().predicate(ctx)

        if not check_blacklist or not check_ignore:
            return

        sig = f"{self.context.prefix}{command.qualified_name} {command.signature}".strip()
        help_desc = command.help or "No detailed description provided for this command."

        embed = CV2Embed(
            title=f"# 📌 Command: {self.context.prefix}{command.qualified_name}",
            description=f"> {help_desc}",
            color=ACCENT_COLOR
        )
        embed.add_field(name="Usage & Syntax", value=f"```bash\n{sig}\n```", inline=False)

        if command.aliases:
            aliases_fmt = " • ".join(f"`{a}`" for a in command.aliases)
            embed.add_field(name="Alternative Aliases", value=aliases_fmt, inline=False)

        if command.cog_name:
            clean_cog = command.cog_name.strip("_").replace("_", " ").title()
            embed.add_field(name="Module Department", value=f"`{clean_cog}`", inline=True)

        embed.set_footer(text="Parameters: <required> • [optional] | Do not type brackets when running commands.")
        await self.context.reply(view=embed, mention_author=False)

    def get_command_signature(self, command: commands.Command) -> str:
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = ' | '.join(command.aliases)
            alias = f"[{command.name} | {aliases}]"
            if parent:
                alias = f"{parent} {alias}"
        else:
            alias = command.name if not parent else f"{parent} {command.name}"
        return f"{alias} {command.signature}".strip()

    async def send_group_help(self, group):
        ctx = self.context
        check_ignore = await ignore_check().predicate(ctx)
        check_blacklist = await blacklist_check().predicate(ctx)

        if not check_blacklist or not check_ignore:
            return

        embed = CV2Embed(
            title=f"# 📁 Group: {self.context.prefix}{group.qualified_name}",
            description=f"> {group.help or 'Command group with multiple subcommands.'}",
            color=ACCENT_COLOR
        )

        sub_list = []
        for cmd in group.commands:
            doc = cmd.short_doc or "No description"
            sub_list.append(f"• **`{self.context.prefix}{cmd.qualified_name} {cmd.signature}`**\n  ↳ *{doc}*")

        if sub_list:
            embed.add_field(name=f"Subcommands ({len(group.commands)})", value="\n".join(sub_list), inline=False)

        embed.set_footer(text=f"Requested by {ctx.author.display_name} • Type {self.context.prefix}help <subcommand> for details.")
        await ctx.reply(view=embed, mention_author=False)

    async def send_cog_help(self, cog):
        ctx = self.context
        check_ignore = await ignore_check().predicate(ctx)
        check_blacklist = await blacklist_check().predicate(ctx)

        if not check_blacklist or not check_ignore:
            return

        clean_name = cog.qualified_name.strip("_").replace("_", " ").title()
        embed = CV2Embed(
            title=f"# 🛡️ Module: {clean_name}",
            description=f"> Browsing commands registered under **{clean_name}**.",
            color=ACCENT_COLOR
        )

        cmds = cog.get_commands()
        cmd_entries = []
        for cmd in cmds:
            doc = cmd.short_doc or "No description"
            cmd_entries.append(f"• **`{self.context.prefix}{cmd.qualified_name}`** — *{doc}*")

        if cmd_entries:
            embed.add_field(name=f"Registered Commands ({len(cmds)})", value="\n".join(cmd_entries[:20]), inline=False)

        embed.set_footer(text=f"Requested by {ctx.author.display_name} • Support: {serverLink}")
        await ctx.reply(view=embed, mention_author=False)


class Help(Cog, name="help"):
    """Core Help Cog."""
    def __init__(self, client: zyuna):
        self._original_help_command = client.help_command
        attributes = {
            'name': "help",
            'aliases': ['h'],
            'cooldown': commands.CooldownMapping.from_cooldown(1, 4, commands.BucketType.user),
            'help': 'Shows comprehensive help about the bot, commands, and modules'
        }
        client.help_command = HelpCommand(command_attrs=attributes)
        client.help_command.cog = self

    async def cog_unload(self):
        self.help_command = self._original_help_command