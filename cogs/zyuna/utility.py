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
from utils.emoji import INFO
from discord.ext import commands


class _utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Server utility commands"""

    def help_custom(self):
        emoji = INFO
        label = "Utilities & Tools"
        description = "Server prefix, visual embed builder, translation, webhooks & maps"
        return emoji, label, description

    @commands.group()
    async def __Utility__(self, ctx: commands.Context):
        """
__**Builder & Translation**__
embed, hinglish, map, search_youtube
__**Server Tools & Webhooks**__
prefix, create_hook, delete_hook, list_hooks
"""
