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
from .commands.giveaway import Giveaway
from .commands.Embed import Embed
from .commands.blacklist import Blacklist
from .commands.block import Block
from .commands.ticket import TicketCog
from .commands.translate import TranslateCog
from .commands.stats import Stats
from .commands.notify import NotifCommands
from .commands.status import Status
from .commands.np import NoPrefix
from .commands.filters import FilterCog
from .commands.owner2 import Global
from .commands.messages import Messages
from .commands.dms import StaffDMCog
from .commands.booster import Booster
from .commands.verification import Verification
from .commands.Birthday import Birthdays
from .commands.youtube import Youtube

#____________ Events _____________
from .events.Errors import Errors
from .events.on_guild import Guild
from .events.mention import Mention

########-------HELP-------########
from .zyuna.music import _music
from .zyuna.giveaway import _giveaway
from .zyuna.ticket import _ticket
from .zyuna.booster import __boost 
from .zyuna.verify import _verify
from .zyuna.birth import _birth

try:
    from bot.utils.config import BotName
except (ImportError, ModuleNotFoundError):
    from utils.config import BotName

async def setup(bot: zyuna):
  cogs_to_load = [
        Help, Music, Owner, Embed, TicketCog,
        Blacklist, Block, Badges, Guild, Errors,
        Mention, Stats, Status, NoPrefix, FilterCog,
        Global, Messages, TranslateCog, Giveaway, Booster,
        StaffDMCog, Verification, Birthdays, Youtube, NotifCommands,
        _music, _giveaway, _ticket, __boost, _verify, _birth
    ]

  await bot.add_cog(Help(bot))
  await bot.add_cog(Music(bot))
  await bot.add_cog(Owner(bot))
  await bot.add_cog(Embed(bot))
  await bot.add_cog(Giveaway(bot))
  await bot.add_cog(Booster(bot))
  await bot.add_cog(Blacklist(bot))
  await bot.add_cog(Block(bot))
  await bot.add_cog(Badges(bot))
  await bot.add_cog(Stats(bot))
  await bot.add_cog(Status(bot))
  await bot.add_cog(NoPrefix(bot))
  await bot.add_cog(FilterCog(bot))
  await bot.add_cog(Global(bot))
  await bot.add_cog(TicketCog(bot))
  await bot.add_cog(Messages(bot))
  await bot.add_cog(TranslateCog(bot))
  await bot.add_cog(StaffDMCog(bot))
  await bot.add_cog(Verification(bot))
  await bot.add_cog(Birthdays(bot))
  await bot.add_cog(Youtube(bot))

  # Help category handlers
  await bot.add_cog(_music(bot))
  await bot.add_cog(_giveaway(bot))
  await bot.add_cog(_ticket(bot))
  await bot.add_cog(__boost(bot))
  await bot.add_cog(_verify(bot))
  await bot.add_cog(_birth(bot))

  # Events
  await bot.add_cog(Guild(bot))
  await bot.add_cog(Errors(bot))
  await bot.add_cog(Mention(bot))
  await bot.add_cog(NotifCommands(bot))

  for cog in cogs_to_load:
    print(Fore.RED + Style.BRIGHT + f"Loaded cog: {cog.__name__}")
  print(Fore.RED + Style.BRIGHT + f"All {BotName} Cogs loaded successfully.")
