from __future__ import annotations

from typing import Optional

from discord.ext import commands

try:
    from bot.utils.Tools import DEFAULT_PREFIX, getConfig, updateConfig, blacklist_check, ignore_check
except (ImportError, ModuleNotFoundError):
    from utils.Tools import DEFAULT_PREFIX, getConfig, updateConfig, blacklist_check, ignore_check


class Prefix(commands.Cog):
    """Show or change the command prefix for the current server."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="prefix",
        aliases=["setprefix"],
        help="Show or change this server's command prefix.",
    )
    @commands.guild_only()
    @blacklist_check()
    @ignore_check()
    async def prefix(self, ctx: commands.Context, *, new_prefix: Optional[str] = None):
        config = await getConfig(ctx.guild.id)
        current_prefix = config.get("prefix", DEFAULT_PREFIX)

        if new_prefix is None:
            await ctx.reply(
                f"This server's prefix is `{current_prefix}`. "
                f"A server manager can use `{current_prefix}prefix <new prefix>` to change it, "
                f"or `{current_prefix}prefix reset` to restore `{DEFAULT_PREFIX}`.",
                mention_author=False,
            )
            return

        if not ctx.author.guild_permissions.manage_guild:
            await ctx.reply("You need the **Manage Server** permission to change this server's prefix.", mention_author=False)
            return

        if new_prefix.casefold() == "reset":
            new_prefix = DEFAULT_PREFIX
        elif (
            len(new_prefix) > 5
            or any(character.isspace() for character in new_prefix)
            or any(ord(character) < 32 for character in new_prefix)
        ):
            await ctx.reply("Choose a prefix with 1–5 non-space characters, or use `reset`.", mention_author=False)
            return

        await updateConfig(ctx.guild.id, {"prefix": new_prefix})
        await ctx.reply(
            f"This server's prefix is now `{new_prefix}`.",
            mention_author=False,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Prefix(bot))
