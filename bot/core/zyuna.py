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

from __future__ import annotations
from discord.ext import commands, tasks
import discord
import aiohttp
import json
import jishaku
import asyncio
import typing
from typing import List
import aiosqlite
try:
    from bot.utils.config import OWNER_IDS, BotName
    from bot.utils.Tools import getConfig, updateConfig
except (ImportError, ModuleNotFoundError):
    from utils.config import OWNER_IDS, BotName
    from utils.Tools import getConfig, updateConfig
from .Context import Context
from colorama import Fore, Style, init
import importlib
import inspect

init(autoreset=True)

# Corrected the extensions list
extensions: List[str] = [
    "cogs"
]

class zyuna(commands.AutoShardedBot):
    def __init__(self, *arg, **kwargs):
        intents = discord.Intents.all()
        intents.presences = True
        intents.members = True
        super().__init__(command_prefix=self.get_prefix,
                         case_insensitive=True,
                         intents=intents,
                         # The status is already set to Do Not Disturb here
                         status=discord.Status.do_not_disturb,
                         strip_after_prefix=True,
                         owner_ids=OWNER_IDS,
                         allowed_mentions=discord.AllowedMentions(
                             everyone=False, replied_user=False, roles=False),
                         sync_commands_debug=True,
                         sync_commands=True,
                         shard_count=1)
        self.status_index = 0
        self.status_list = []
        self._speech_bubble_engine = None

        # Setup Discord Mobile Client status indicator (phone badge 📱)
        try:
            from .discord.mobile_client import setup_mobile_status
            setup_mobile_status()
        except Exception as e:
            try:
                from bot.core.discord.mobile_client import setup_mobile_status
                setup_mobile_status()
            except Exception:
                pass

    async def close(self):
        if self._speech_bubble_engine:
            try:
                await self._speech_bubble_engine.stop()
            except Exception:
                pass
        music_cog = self.get_cog("Music")
        if music_cog and hasattr(music_cog, "save_all_sessions_sync"):
            try:
                music_cog.save_all_sessions_sync()
            except Exception:
                pass
        await super().close()

    async def setup_hook(self):
        await self.load_extensions()
        self.status_task.start()

    async def load_extensions(self):
        for extension in extensions:
            try:
                await self.load_extension(extension)
                print(Fore.GREEN + Style.BRIGHT + f"Loaded extension: {extension}")
            except Exception as e:
                try:
                    await self.load_extension(f"bot.{extension}")
                    print(Fore.GREEN + Style.BRIGHT + f"Loaded extension: bot.{extension}")
                except Exception as inner_e:
                    print(f"{Fore.RED}{Style.BRIGHT}Failed to load extension {extension}. {e} | {inner_e}")
        print(Fore.GREEN + Style.BRIGHT + "*" * 20)

    @tasks.loop(seconds=15)
    async def status_task(self):
        await self.wait_until_ready()
        if not self.guilds:
            return

        # Initialize speech bubble engine if not running
        if self._speech_bubble_engine is None:
            try:
                from .speech_bubble import SpeechBubbleEngine
                self._speech_bubble_engine = SpeechBubbleEngine(self)
                await self._speech_bubble_engine.start()
                return
            except Exception as e:
                try:
                    from bot.core.speech_bubble import SpeechBubbleEngine
                    self._speech_bubble_engine = SpeechBubbleEngine(self)
                    await self._speech_bubble_engine.start()
                    return
                except Exception as inner_e:
                    self._speech_bubble_engine = False

        # If speech bubble engine is handling presence, we pass to avoid overriding
        if self._speech_bubble_engine:
            return

        guild = self.guilds[0]  # Use first available guild for prefix
        try:
            config = await getConfig(guild.id)
            prefix = config.get("prefix", ">")
        except:
            prefix = ">"

        user_count = sum(g.member_count or 0 for g in self.guilds)
        guild_count = len(self.guilds)

        # Fallback custom activity
        custom_bubble = f"👑 Yuna • High-Fidelity Audio | {prefix}help"
        activity = discord.CustomActivity(name=custom_bubble)
        await self.change_presence(status=discord.Status.do_not_disturb, activity=activity)

    async def send_raw(self, channel_id: int, content: str, **kwargs) -> typing.Optional[discord.Message]:
        await self.http.send_message(channel_id, content, **kwargs)

    async def invoke_help_command(self, ctx: Context) -> None:
        return await ctx.send_help(ctx.command)

    async def fetch_message_by_channel(self, channel: discord.TextChannel, messageID: int) -> typing.Optional[discord.Message]:
        async for msg in channel.history(limit=1, before=discord.Object(messageID + 1), after=discord.Object(messageID - 1)):
            return msg

    async def get_prefix(self, message: discord.Message):
        if message.guild:
            guild_id = message.guild.id
            async with aiosqlite.connect('db/np.db') as db:
                async with db.execute("SELECT id FROM np WHERE id = ?", (message.author.id,)) as cursor:
                    row = await cursor.fetchone()
            data = await getConfig(guild_id)
            prefix = data["prefix"]
            if row:
                return commands.when_mentioned_or(prefix, '')(self, message)
            else:
                return commands.when_mentioned_or(prefix)(self, message)
        else:
            async with aiosqlite.connect('db/np.db') as db:
                async with db.execute("SELECT id FROM np WHERE id = ?", (message.author.id,)) as cursor:
                    row = await cursor.fetchone()
            if row:
                return commands.when_mentioned_or('?', '')(self, message)
            else:
                return commands.when_mentioned_or('')(self, message)

    async def on_message_edit(self, before, after):
        ctx: Context = await self.get_context(after, cls=Context)
        if before.content != after.content:
            if after.guild is None or after.author.bot:
                return
            if ctx.command is None:
                return
            if type(ctx.channel) == "public_thread":
                return
            await self.invoke(ctx)

def setup_bot():
    intents = discord.Intents.all()
    bot = zyuna(intents=intents)
    return bot

Bot = zyuna
