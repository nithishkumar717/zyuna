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
from utils.emoji import CAST
from discord.ext import commands


class _filters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Audio FX Filters commands"""

    def help_custom(self):
        emoji = CAST
        label = "Audio Filters"
        description = "15+ real-time DSP audio filters: 8D, Bassboost, Nightcore & more"
        return emoji, label, description

    @commands.group()
    async def __Filters__(self, ctx: commands.Context):
        """
__**Filter Controls**__
filter, filter enable, filter disable
__**DSP Presets**__
8d, nightcore, vaporwave, bassboost, pop, treblebass, soft, karaoke, tremolo, vibrato, distortion, flat, reset
"""
