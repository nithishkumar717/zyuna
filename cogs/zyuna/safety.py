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
from utils.emoji import LOCK
from discord.ext import commands


class _safety(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Chat Safety and Stats commands"""

    def help_custom(self):
        emoji = LOCK
        label = "Safety & Stats"
        description = "Word blacklist filters, staff dispatch & message statistics"
        return emoji, label, description

    @commands.group()
    async def __Safety__(self, ctx: commands.Context):
        """
__**Chat Protection**__
blacklistword add, blacklistword remove, blacklistword config, blacklistword reset, blacklistword bypass add, blacklistword bypass remove, blacklistword bypass list
__**Staff Dispatch & Tracking**__
dm_staff, messages, addmessages, removemessages, clearmessage, autonp add, autonp remove, autonp list
"""
