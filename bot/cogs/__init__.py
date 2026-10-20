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
from .commands.welcome import Welcomer
from .commands.owner import Owner
from .commands.giveaway import Giveaway
from .commands.Embed import Embed
from .commands.blacklist import Blacklist
from .commands.block import Block
from .commands.owner import Badges
from .commands.autoresponder import AutoResponder
from .commands.autorole import AutoRole
from .commands.ticket import TicketCog
from .commands.translate import TranslateCog
from .commands.autoreact import AutoReaction
from .commands.stats import Stats
from .commands.notify import NotifCommands
from .commands.status import Status
from .commands.np import NoPrefix
from .commands.filters import FilterCog
from .commands.owner2 import Global
from .commands.messages import Messages
from .commands.fastgreet import FastGreet
from .commands.dms import StaffDMCog
from .commands.booster import Booster
from .commands.stickymessage import StickyMessage
from .commands.verification import Verification
from .commands.joindm import joindm
from .commands.Birthday import Birthdays
from .commands.youtube import Youtube

#____________ Events _____________
from .events.Errors import Errors
from .events.on_guild import Guild
from .events.autorole import Autorole2
from .events.auto import Autorole
from .events.greet2 import greet
from .events.mention import Mention
from .events.react import React
from .events.autoreact import AutoReactListener
from .events.stickymessage import StickyMessageListener

########-------HELP-------########
from .zyuna.music import _music
from .zyuna.welcome import _welcome 
from .zyuna.giveaway import _giveaway
from .zyuna.ticket import _ticket
from .zyuna.booster import __boost 
from .zyuna.sticky import _sticky
from .zyuna.verify import _verify
from .zyuna.joindm import _joindm
from .zyuna.birth import _birth

try:
    from bot.utils.config import BotName
except (ImportError, ModuleNotFoundError):
    from utils.config import BotName

async def setup(bot: zyuna):
  cogs_to_load = [
        Help, Welcomer, Owner, Embed, TicketCog,
        Blacklist, Block, Badges, Guild, Errors,
        Autorole2, Autorole, greet, AutoResponder, Mention, AutoRole, React,
        Stats, Status, NoPrefix, FilterCog, AutoReaction, AutoReactListener,
        Global, Messages, TranslateCog, FastGreet
    ]

  await bot.add_cog(Help(bot))
  await bot.add_cog(Music(bot))
  await bot.add_cog(Welcomer(bot))
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
  await bot.add_cog(FastGreet(bot))
  await bot.add_cog(StaffDMCog(bot))
  await bot.add_cog(StickyMessage(bot))
  await bot.add_cog(Verification(bot))
  await bot.add_cog(joindm(bot))
  await bot.add_cog(Birthdays(bot))
  await bot.add_cog(Youtube(bot))

  # Help category handlers
  await bot.add_cog(_music(bot))
  await bot.add_cog(_welcome(bot))
  await bot.add_cog(_giveaway(bot))
  await bot.add_cog(_ticket(bot))
  await bot.add_cog(__boost(bot))
  await bot.add_cog(_sticky(bot))
  await bot.add_cog(_verify(bot))
  await bot.add_cog(_joindm(bot))
  await bot.add_cog(_birth(bot))

  # Events
  await bot.add_cog(Guild(bot))
  await bot.add_cog(Errors(bot))
  await bot.add_cog(Autorole2(bot))
  await bot.add_cog(Autorole(bot))
  await bot.add_cog(greet(bot))
  await bot.add_cog(AutoResponder(bot))
  await bot.add_cog(Mention(bot))
  await bot.add_cog(AutoRole(bot))
  await bot.add_cog(React(bot))
  await bot.add_cog(AutoReaction(bot))
  await bot.add_cog(AutoReactListener(bot))
  await bot.add_cog(NotifCommands(bot))
  await bot.add_cog(StickyMessageListener(bot))

  for cog in cogs_to_load:
    print(Fore.RED + Style.BRIGHT + f"Loaded cog: {cog.__name__}")
  print(Fore.RED + Style.BRIGHT + f"All {BotName} Cogs loaded successfully.")
