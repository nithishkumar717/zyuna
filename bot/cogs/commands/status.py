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

import asyncio
import math
import time

import aiosqlite
import discord
from utils.emoji import DND, ICON_BROWSER, IDLE, LOADING_ALT1, MOBILE, OFFLINE, ONLINE, PC
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import os
from utils.Tools import *


class PingLoadingView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        container = discord.ui.Container(
            discord.ui.TextDisplay("**Checking Latency...**"),
            discord.ui.Separator(visible=True),
            discord.ui.TextDisplay("Calculating response times, please wait."),
        )
        self.add_item(container)


class PingTelemetryView(discord.ui.LayoutView):
    def __init__(self, cog, ctx, metrics):
        super().__init__(timeout=120)
        self.cog = cog
        self.author_id = ctx.author.id
        self.requester = ctx.author
        self.message = None
        self.cooldown = commands.CooldownMapping.from_cooldown(
            1, 2.5, commands.BucketType.user
        )

        self.container = discord.ui.Container()
        self.header_display = discord.ui.TextDisplay("**Ultra-Low Latency**")
        self.top_sep = discord.ui.Separator(visible=True)
        self.body_display = discord.ui.TextDisplay(cog._format_ping_metrics(metrics))
        self.bottom_sep = discord.ui.Separator(visible=True)
        self.refresh_btn = discord.ui.Button(
            label="Refresh",
            emoji="🔄",
            style=discord.ButtonStyle.secondary,
            custom_id=f"zyrox_ping_refresh_{self.author_id}",
        )
        self.refresh_btn.callback = self.refresh_callback
        self.action_row = discord.ui.ActionRow(self.refresh_btn)
        self.footer_sep = discord.ui.Separator(visible=True)
        self.footer_display = discord.ui.TextDisplay(self._footer_text())

        for item in (
            self.header_display,
            self.top_sep,
            self.body_display,
            self.bottom_sep,
            self.action_row,
            self.footer_sep,
            self.footer_display,
        ):
            self.container.add_item(item)
        self.add_item(self.container)

    def _footer_text(self):
        requester_name = getattr(
            self.requester, "display_name", str(self.requester)
        )
        return f"-# Requested by {requester_name} • Last refreshed <t:{int(time.time())}:R>"

    async def refresh_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Uh oh! That message doesn't belong to you. You must run this command to interact with it.",
                ephemeral=True,
            )
            return

        bucket = self.cooldown.get_bucket(interaction.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            await interaction.response.send_message(
                f"Please try again after {retry_after:.1f}s", ephemeral=True
            )
            return

        await interaction.response.defer()
        metrics = await self.cog._collect_ping_metrics(interaction.guild)
        self.body_display.content = self.cog._format_ping_metrics(metrics)
        self.footer_display.content = self._footer_text()

        try:
            await interaction.edit_original_response(view=self)
        except Exception:
            if interaction.message:
                await interaction.message.edit(view=self)
            elif self.message:
                await self.message.edit(view=self)

    async def on_timeout(self):
        self.refresh_btn.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.started_at = time.monotonic()

    async def _probe_api_latency(self):
        started = time.perf_counter()
        try:
            route = discord.http.Route("GET", "/gateway")
            await self.bot.http.request(route)
            return max(0.01, round((time.perf_counter() - started) * 1000, 2))
        except Exception:
            return "N/A"

    async def _probe_sqlite_latency(self):
        try:
            async with aiosqlite.connect("db/prefix.db") as db:
                started = time.perf_counter()
                await db.execute("SELECT 1")
                return max(0.01, round((time.perf_counter() - started) * 1000, 2))
        except Exception:
            return "N/A"

    async def _collect_ping_metrics(self, guild):
        shard_id = getattr(guild, "shard_id", 0) if guild else 0
        shard = self.bot.get_shard(shard_id) if hasattr(self.bot, "get_shard") else None
        raw_ws = getattr(shard, "latency", None) if shard else None
        if raw_ws is None:
            raw_ws = getattr(self.bot, "latency", None)
        if not isinstance(raw_ws, (int, float)) or not math.isfinite(raw_ws):
            gateway_ms = "N/A"
        else:
            gateway_ms = max(0.01, round(raw_ws * 1000, 2))

        api_ms, sqlite_ms = await asyncio.gather(
            self._probe_api_latency(), self._probe_sqlite_latency()
        )
        if api_ms == "N/A":
            api_ms = gateway_ms

        uptime_seconds = max(0, int(time.monotonic() - self.started_at))
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days:
            uptime = f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours:
            uptime = f"{hours}h {minutes}m {seconds}s"
        elif minutes:
            uptime = f"{minutes}m {seconds}s"
        else:
            uptime = f"{seconds}s"

        return {
            "gateway": gateway_ms,
            "api": api_ms,
            "sqlite": sqlite_ms,
            "uptime": uptime,
        }

    @staticmethod
    def _format_ping_metrics(metrics):
        def format_ms(value):
            if value is None or str(value).strip().upper() in ("N/A", "NONE"):
                return "N/A"
            if isinstance(value, str) and value.strip().lower().endswith("ms"):
                value = value.strip()[:-2]
            try:
                return f"{round(float(value))}ms"
            except (TypeError, ValueError):
                return str(value)

        return "\n".join(
            (
                f"**Gateway:** `{format_ms(metrics['gateway'])}`",
                f"**API:** `{format_ms(metrics['api'])}`",
                f"**SQLite:** `{format_ms(metrics['sqlite'])}`",
                f"**System Uptime:** `{metrics['uptime']}`",
            )
        )

    async def _execute_ping_telemetry(self, ctx):
        message = await ctx.send(view=PingLoadingView())
        metrics = await self._collect_ping_metrics(ctx.guild)
        view = PingTelemetryView(self, ctx, metrics)
        view.message = message
        try:
            await message.edit(view=view)
        except Exception:
            if ctx.interaction:
                await ctx.interaction.edit_original_response(view=view)

    @commands.hybrid_command(
        name="ping",
        aliases=["pong"],
        description="Displays detailed network and database telemetry.",
        help="Checks the bot's WebSocket, API, and Database latencies.",
        with_app_command=True,
    )
    @ignore_check()
    @blacklist_check()
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def ping(self, ctx):
        await self._execute_ping_telemetry(ctx)

    @commands.command(name="status", help="Shows the status of the user in detail.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def status(self, ctx, user: discord.User = None):
        user = user or ctx.author
        processing = await ctx.send(f"{LOADING_ALT1} Loading Status...")
        embed = discord.Embed(title=f"{user.display_name}'s Status", color=0xFF0000)

        status_emoji = {
            "online": f"{ONLINE} Online",
            "idle": f"{IDLE} Idle",
            "dnd": f"{DND} Do Not Disturb",
            "offline": f"{OFFLINE}  Offline"
        }

        member = None
        for guild in self.bot.guilds:
            member = guild.get_member(user.id)
            if member:
                break

        if member:
            status = status_emoji.get(str(member.status), f"{OFFLINE} Offline")
            embed.add_field(name="Status:", value=status, inline=False)

            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed.set_thumbnail(url=avatar_url)

            platform = self.get_platform(member)
            embed.add_field(name="Platform:", value=platform, inline=False)

            custom_status = self.get_custom_status(member)
            if custom_status:
                embed.add_field(name="Custom Status:", value=custom_status, inline=False)

            activity_text = self.get_activity_text(member.activities)
            if activity_text:
                embed.add_field(name="__Activity__:", value=activity_text, inline=False)

            for activity in member.activities:
                if isinstance(activity, discord.Spotify):
                    song_name = activity.title
                    album_cover_url = str(activity.album_cover_url)

                    album_image_path = 'data/pictures/album_image.png'

                    async with aiohttp.ClientSession() as session:
                        async with session.get(album_cover_url) as resp:
                            if resp.status == 200:
                                album_data = await resp.read()
                                with open(album_image_path, 'wb') as f:
                                    f.write(album_data)

                    card_image_path = self.create_spotify_card(song_name, album_image_path)

                    if os.path.exists(card_image_path):
                        file = discord.File(card_image_path, filename="spotify_card.png")
                        embed.set_image(url="attachment://spotify_card.png")
                    else:
                        await ctx.send("Failed to generate the Spotify card image.")
        else:
            try:
                user = await self.bot.fetch_user(user.id)
                embed.add_field(name="Status:", value=f"{OFFLINE} Offline", inline=False)
                avatar_url = user.default_avatar.url
                embed.set_thumbnail(url=avatar_url)
            except discord.NotFound:
                await ctx.send("User not found.")
                return

        requester_avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=requester_avatar_url)

        await ctx.send(embed=embed, file=file if 'file' in locals() else None)
        await processing.delete()

    def create_spotify_card(self, song_name, album_image_path):
        card_path = 'data/pictures/spotify.png'
        output_path = 'data/pictures/spotify_card_output.png'

        base_img = Image.open(card_path).convert("RGBA")
        draw = ImageDraw.Draw(base_img)

        album_img = Image.open(album_image_path).convert("RGBA")
        album_img = album_img.resize((160, 160))

        mask = Image.new("L", album_img.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 160, 160), fill=255)

        base_img.paste(album_img, (30, 30), mask) 

        font_path = 'utils/arial.ttf'
        font = ImageFont.truetype(font_path, 40)

        truncated_song_name = song_name if len(song_name) <= 60 else song_name[:57] + "..."
        song_name_position = (220, 70) 
        draw.text(song_name_position, truncated_song_name, font=font, fill="white")

        base_img.save(output_path)
        return output_path

    def get_platform(self, member):
        if member.desktop_status != discord.Status.offline:
            return f"{PC}  Desktop"
        elif member.mobile_status != discord.Status.offline:
            return f"{MOBILE} Mobile"
        elif member.web_status != discord.Status.offline:
            return f"{ICON_BROWSER} Browser"
        return "Unknown"

    def get_custom_status(self, member):
        for activity in member.activities:
            if isinstance(activity, discord.CustomActivity):
                status_text = activity.name or ""
                if activity.name == "Custom Status":
                    status_text = "‎"
                status_emoji = str(activity.emoji) if activity.emoji else ""

                if status_emoji and not status_text:
                    return status_emoji
                elif status_emoji and status_text:
                    return f"{status_emoji} {status_text}"
                elif status_text:
                    return status_text
        return None

    def get_activity_text(self, activities):
        activity_list = []
        for activity in activities:
            if isinstance(activity, discord.Game):
                activity_list.append(f"Playing {activity.name}")
            elif isinstance(activity, discord.Streaming):
                activity_list.append(f"Streaming {activity.name} on **[Twitch]({activity.url})**")
            elif isinstance(activity, discord.Spotify):
                activity_list.append(f"**[Listening to Spotify](https://open.spotify.com/track/{activity.track_id})**")
            elif isinstance(activity, discord.Activity):
                activity_list.append(f"{activity.type.name.capitalize()} {activity.name}")
        return "\n".join(activity_list) if activity_list else None

