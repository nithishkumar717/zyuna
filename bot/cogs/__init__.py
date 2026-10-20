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
try:
    from bot.core import zyuna
except (ImportError, ModuleNotFoundError):
    from core import zyuna
from colorama import Fore, Style, init

from .commands.help import Help
from .commands.music import Music
from .commands.owner import Owner, Badges
from .commands.Embed import Embed
from .commands.blacklist import Blacklist
from .commands.block import Block
from .commands.translate import TranslateCog
from .commands.stats import Stats
from .commands.notify import NotifCommands
from .commands.status import Status
from .commands.np import NoPrefix
from .commands.filters import FilterCog
from .commands.owner2 import Global
from .commands.messages import Messages
from .commands.dms import StaffDMCog
from .commands.youtube import Youtube
from .commands.map import Map
from .commands.msgpack import Messagespack

#____________ Events _____________
from .events.Errors import Errors
from .events.on_guild import Guild
from .events.mention import Mention

########-------HELP CATEGORIES-------########
from .zyuna.music import _music
from .zyuna.filters import _filters
from .zyuna.utility import _utility
from .zyuna.alerts import _alerts
from .zyuna.safety import _safety
from .zyuna.games import _games
from .zyuna.system import _system

try:
    from bot.utils.config import BotName
except (ImportError, ModuleNotFoundError):
    from utils.config import BotName

async def setup(bot: zyuna):
    cogs_to_load = [
        Help, Music, Owner, Embed, Blacklist, Block, Badges,
        Guild, Errors, Mention, Stats, Status, NoPrefix, FilterCog,
        Global, Messages, TranslateCog, StaffDMCog, Youtube, Map, Messagespack,
        NotifCommands, _music, _filters, _utility, _alerts, _safety, _games, _system
    ]

    await bot.add_cog(Help(bot))
    await bot.add_cog(Music(bot))
    await bot.add_cog(Owner(bot))
    await bot.add_cog(Embed(bot))
    await bot.add_cog(Blacklist(bot))
    await bot.add_cog(Block(bot))
    await bot.add_cog(Badges(bot))
    await bot.add_cog(Stats(bot))
    await bot.add_cog(Status(bot))
    await bot.add_cog(NoPrefix(bot))
    await bot.add_cog(FilterCog(bot))
    await bot.add_cog(Global(bot))
    await bot.add_cog(Messages(bot))
    await bot.add_cog(TranslateCog(bot))
    await bot.add_cog(StaffDMCog(bot))
    await bot.add_cog(Youtube(bot))
    await bot.add_cog(Map(bot))
    await bot.add_cog(Messagespack(bot))

    # Help category handlers
    await bot.add_cog(_music(bot))
    await bot.add_cog(_filters(bot))
    await bot.add_cog(_utility(bot))
    await bot.add_cog(_alerts(bot))
    await bot.add_cog(_safety(bot))
    await bot.add_cog(_games(bot))
    await bot.add_cog(_system(bot))

    # Events
    await bot.add_cog(Guild(bot))
    await bot.add_cog(Errors(bot))
    await bot.add_cog(Mention(bot))
    await bot.add_cog(NotifCommands(bot))

    for cog in cogs_to_load:
        print(Fore.RED + Style.BRIGHT + f"Loaded cog: {cog.__name__}")
    print(Fore.RED + Style.BRIGHT + f"All {BotName} Cogs loaded successfully.")
