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
from utils.emoji import THUNDER
from discord.ext import commands


class _alerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Social Alerts commands"""

    def help_custom(self):
        emoji = THUNDER
        label = "Social Stream Alerts"
        description = "Automated live notifications for YouTube and Twitch streams"
        return emoji, label, description

    @commands.group()
    async def __Alerts__(self, ctx: commands.Context):
        """
__**Live Stream Monitors**__
setnotif youtube, setnotif twitch, setnotif list, setnotif reset
"""
