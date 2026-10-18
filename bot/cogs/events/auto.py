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
from discord.utils import *
from core import zyrox, Cog
from utils.Tools import *
from utils.config import BotName, BRAND_NAME, serverLink, websiteLink
from discord.ext import commands
from discord.ui import Button, View

class Autorole(Cog):
    def __init__(self, bot: zyrox):
       self.bot = bot

    @commands.Cog.listener(name="on_guild_join")
    async def send_msg_to_adder(self, guild: discord.Guild):
        async for entry in guild.audit_logs(limit=3):
            if entry.action == discord.AuditLogAction.bot_add:
                try:
                    prefix_data = await getConfig(guild.id)
                    prefix = prefix_data.get("prefix", "$")
                except Exception:
                    prefix = "$"

                brand = BRAND_NAME if BRAND_NAME else "Yuna"
                avatar_url = self.bot.user.display_avatar.url if self.bot.user else guild.me.display_avatar.url
                domain = websiteLink.replace("https://", "").replace("http://", "").rstrip("/")

                embed = discord.Embed(
                    description=(
                        f"**Welcome to {brand.upper()}**\n"
                        f"Thanks for adding to **{guild.name}**!\n"
                        f"Your elegant server companion is ready.\n\n"
                        f"**Prefix** · `{prefix}`\n"
                        f"**Help** · `{prefix}help`\n"
                        f"**Website** · [yuna dashboard]({websiteLink})\n"
                        f"**Support** · [Join our server]({serverLink})"
                    ),
                    color=0x7C3AED
                )
                embed.set_author(name=f"Thanks for adding to {guild.name}", icon_url=avatar_url)
                embed.set_thumbnail(url=avatar_url)
                embed.set_footer(
                    text=f"{brand.upper()} Development™ • https://{domain}",
                    icon_url=avatar_url
                )
                embed.timestamp = discord.utils.utcnow()

                dashboard_button = Button(
                    label=f"{brand.lower()} web-dashboard",
                    style=discord.ButtonStyle.link,
                    url=websiteLink
                )
                support_button = Button(
                    label="Support",
                    style=discord.ButtonStyle.link,
                    url=serverLink
                )
                view = View()
                view.add_item(dashboard_button)
                view.add_item(support_button)

                try:
                    await entry.user.send(content=f"Thanks for adding to {guild.name}", embed=embed, view=view)
                except Exception as e:
                    print(f"Failed to send welcome DM: {e}")
