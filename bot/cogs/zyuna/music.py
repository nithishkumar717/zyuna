# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                  ║
# ║   ░█▄░█░█▀▀░█▀▄░█▀▄   ░█░█   ░█░░░▀█▀░█░█░█▀▀                 ║
# ║   ░█░▀█░█▀▀░█▀▄░█░█   ░▄▀▄   ░█░░░░█░░▀▄▀░█▀▀                 ║
# ║   ░▀░░▀░▀▀▀░▀░▀░▀▀░   ░▀░▀   ░▀▀▀░▀█▀░░▀░░▀▀▀                 ║
# ║                                                                  ║
# ║            © 2026 Nerd X Live — All Rights Reserved             ║
# ║                                                                  ║
# ║   discord  ──  https://discord.gg/YzHCx5yQXv                    ║
# ║   github   ──  https://github.com/nithishkumar717/yuna-bot      ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

import discord
from utils.emoji import MUSIC
from discord.ext import commands


class _music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Music commands"""

    def help_custom(self):
              emoji = MUSIC
              label = "Music Commands"
              description = "Show you Commands of Music"
              return emoji, label, description

    @commands.group()
    async def __Music__(self, ctx: commands.Context):
        """`play` , `search` , `loop` , `autoplay` , `nowplaying` , `shuffle` , `stop` , `skip` , `seek` , `join` , `disconnect` , `replay` , `queue` , `clearqueue` , `pause` , `resume` , `volume` , `filter` , `filter enable` , `filter disable`"""