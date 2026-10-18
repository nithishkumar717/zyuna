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

from discord.ext import commands
from core import zyrox, Cog
import discord
from utils.emoji import ARROWRED, KING, ZBOT, ZHUMAN, ZROCKET
import logging
from discord.ui import View, Button, Select
from utils.config import *

logging.basicConfig(
    level=logging.INFO,
    format="\x1b[38;5;197m[\x1b[0m%(asctime)s\x1b[38;5;197m]\x1b[0m -> \x1b[38;5;197m%(message)s\x1b[0m",
    datefmt="%H:%M:%S",
)

client = zyrox()


class Guild(Cog):
    def __init__(self, client: zyrox):
        self.client = client
        self.recently_removed_guilds = set()
        self._removal_timestamps = {}

    @client.event
    @commands.Cog.listener(name="on_guild_join")
    async def on_guild_add(self, guild):
        try:
            rope = [
                inv
                for inv in await guild.invites()
                if inv.max_age == 0 and inv.max_uses == 0
            ]
            ch = 1396794297386532978
            me = self.client.get_channel(ch)
            if me is None:
                logging.error(f"Channel with ID {ch} not found.")
                return

            channels = len(set(self.client.get_all_channels()))
            embed = discord.Embed(title=f"{guild.name}'s Information", color=0xFF0000)

            embed.set_author(name="Guild Joined")
            embed.set_footer(text=f"Added in {guild.name}")

            embed.add_field(
                name="**__About__**",
                value=f"**Name : ** {guild.name}\n**ID :** {guild.id}\n**Owner {KING}  :** {guild.owner} (<@{guild.owner_id}>)\n**Created At : **{guild.created_at.month}/{guild.created_at.day}/{guild.created_at.year}\n**Members :** {len(guild.members)}",
                inline=False,
            )
            embed.add_field(
                name="**__Description__**",
                value=f"""{guild.description}""",
                inline=False,
            )
            embed.add_field(
                name="**__Members__**",
                value=f"""{ZROCKET} Members : {len(guild.members)}\n {ZHUMAN} Humans : {len(list(filter(lambda m: not m.bot, guild.members)))}\n {ZBOT} Bots : {len(list(filter(lambda m: m.bot, guild.members)))}
                """,
                inline=False,
            )
            embed.add_field(
                name="**__Channels__**",
                value=f"""
Categories : {len(guild.categories)}
Text Channels : {len(guild.text_channels)}
Voice Channels : {len(guild.voice_channels)}
Threads : {len(guild.threads)}
                """,
                inline=False,
            )
            embed.add_field(
                name="__Bot Stats:__",
                value=f"Servers: `{len(self.client.guilds)}`\nUsers: `{len(self.client.users)}`\nChannels: `{channels}`",
                inline=False,
            )

            if guild.icon is not None:
                embed.set_thumbnail(url=guild.icon.url)

            embed.timestamp = discord.utils.utcnow()
            await me.send(
                f"{rope[0]}" if rope else "No Pre-Made Invite Found", embed=embed
            )

            if not guild.chunked:
                await guild.chunk()

            try:
                from utils.Tools import getConfig
                prefix_data = await getConfig(guild.id)
                prefix = prefix_data.get("prefix", "$")
            except Exception:
                prefix = "$"

            brand = BRAND_NAME if BRAND_NAME else "Yuna"
            avatar_url = self.client.user.display_avatar.url if self.client.user else guild.me.display_avatar.url
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
                color=0x7C3AED,
            )
            embed.set_author(
                name=f"Thanks for adding to {guild.name}", icon_url=avatar_url
            )
            embed.set_thumbnail(url=avatar_url)
            embed.set_footer(
                text=f"{brand.upper()} Development™ • https://{domain}",
                icon_url=avatar_url,
            )
            embed.timestamp = discord.utils.utcnow()

            dashboard_btn = Button(
                label=f"{brand.lower()} web-dashboard",
                style=discord.ButtonStyle.link,
                url=websiteLink,
            )
            support = Button(
                label="Support",
                style=discord.ButtonStyle.link,
                url=serverLink,
            )

            view = View()
            view.add_item(dashboard_btn)
            view.add_item(support)
            channel = discord.utils.get(guild.text_channels, name="general")
            if not channel:
                channels = [
                    channel
                    for channel in guild.text_channels
                    if channel.permissions_for(guild.me).send_messages
                ]
                if channels:
                    channel = channels[0]
                else:
                    logging.error(
                        f"No channel found with send permissions in guild: {guild.name}"
                    )
                    return

            await channel.send(content=f"Thanks for adding to {guild.name}", embed=embed, view=view)

        except Exception as e:
            logging.error(f"Error in on_guild_join: {e}")

    @client.event
    @commands.Cog.listener(name="on_guild_remove")
    async def on_guild_remove(self, guild):
        import time

        current_time = time.time()

        if guild.id in self.recently_removed_guilds:
            last_removal = self._removal_timestamps.get(guild.id, 0)
            if current_time - last_removal < 60:
                return

        self.recently_removed_guilds.add(guild.id)
        self._removal_timestamps[guild.id] = current_time

        if len(self.recently_removed_guilds) > 100:
            self.recently_removed_guilds.clear()

        try:
            ch = 1396794297386532978
            idk = self.client.get_channel(ch)
            if idk is None:
                logging.error(f"Channel with ID {ch} not found.")
                return

            channels = len(set(self.client.get_all_channels()))
            embed = discord.Embed(title=f"{guild.name}'s Information", color=0xFF0000)

            embed.set_author(name="Guild Removed")
            embed.set_footer(text=f"{guild.name}")

            embed.add_field(
                name="**__About__**",
                value=f"**Name : ** {guild.name}\n**ID :** {guild.id}\n**Owner {KING} :** {guild.owner} (<@{guild.owner_id}>)\n**Created At : **{guild.created_at.month}/{guild.created_at.day}/{guild.created_at.year}\n**Members :** {len(guild.members)}",
                inline=False,
            )
            embed.add_field(
                name="**__Description__**",
                value=f"""{guild.description}""",
                inline=False,
            )

            embed.add_field(
                name="**__Members__**",
                value=f"""
Members : {len(guild.members)}
Humans : {len(list(filter(lambda m: not m.bot, guild.members)))}
Bots : {len(list(filter(lambda m: m.bot, guild.members)))}
                """,
                inline=False,
            )
            embed.add_field(
                name="**__Channels__**",
                value=f"""
Categories : {len(guild.categories)}
Text Channels : {len(guild.text_channels)}
Voice Channels : {len(guild.voice_channels)}
Threads : {len(guild.threads)}
                """,
                inline=False,
            )
            embed.add_field(
                name="__Bot Stats:__",
                value=f"Servers: `{len(self.client.guilds)}`\nUsers: `{len(self.client.users)}`\nChannels: `{channels}`",
                inline=False,
            )

            if guild.icon is not None:
                embed.set_thumbnail(url=guild.icon.url)

            embed.timestamp = discord.utils.utcnow()
            await idk.send(embed=embed)
        except Exception as e:
            logging.error(f"Error in on_guild_remove: {e}")


# client.add_cog(Guild(client))
