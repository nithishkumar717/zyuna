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
from utils.emoji import MUSIC
from discord.ext import commands


class _music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Studio Audio commands"""

    def help_custom(self):
        emoji = MUSIC
        label = "Studio Audio"
        description = "High-fidelity music playback, queue controls & Spotify"
        return emoji, label, description

    @commands.group()
    async def __Music__(self, ctx: commands.Context):
        """
__**Playback Controls**__
play, search, pause, resume, skip, stop, seek, replay, volume, loop, shuffle, autoplay
__**Queue & Connection**__
queue, clearqueue, nowplaying, join, disconnect, spotify
"""
