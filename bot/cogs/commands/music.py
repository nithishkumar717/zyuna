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

import os
import random
import discord
from utils.emoji import FORWARD, ICONLOAD, ICONS_MUSIC, ICONS_PAUSE, ICONS_WARNING_ALT1, MUSICSTOP_ICONS, MUSIC_ALT1, MUTE, REWIND, REWIND_ALT1, SHUFFLE, SKIP, TICK, WARNING, ZMUSICPAUSE, ZPLUS, ZUNMUTE
from discord.ext import commands, tasks
import datetime
from discord import ui
from discord.ui import Button, View, LayoutView, TextDisplay, Separator, Container, ActionRow, MediaGallery

try:
    from bot.utils.music_card import MusicCardGenerator
except (ImportError, ModuleNotFoundError):
    from utils.music_card import MusicCardGenerator
import wavelink
from wavelink.enums import TrackSource
from utils import Paginator, DescriptionEmbedPaginator
from core import Cog, zyuna, Context
from utils.music_intelligence import (
    MusicSessionState,
    AutoplayEngine,
    SongValidator,
    normalize_title,
    clean_display_title,
)
from core.ml import (
    SearchRankingModel,
    RankingModel,
    ContextualBandit,
    InteractionLogger,
    MusicTelemetryEvent,
)
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import aiohttp
from typing import cast
import asyncio
from utils.Tools import *
from utils.cv2 import CV2, build_container, CV2Embed
track_histories = {}
import base64
import re
from urllib.parse import urlsplit
from utils.config import *
import json
import atexit
from colorama import Fore, Style
from typing import cast, Optional, Union, List, Dict, Any

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "db"))
SESSIONS_FILE = os.path.join(DB_DIR, "music_active_sessions.json")
MUSIC_247_FILE = os.path.join(DB_DIR, "music_247_mode.json")

_music_cog_instance = None

def sync_save_music_sessions():
    global _music_cog_instance
    if _music_cog_instance:
        try:
            _music_cog_instance.save_all_sessions_sync()
        except Exception:
            pass

atexit.register(sync_save_music_sessions)

class RestoredMusicContext:
    """Lightweight context for restored players after bot/server restarts."""
    def __init__(self, bot, guild: discord.Guild, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread], author: Optional[discord.Member] = None):
        self.bot = bot
        self.guild = guild
        self.channel = channel
        self.author = author or guild.me
        self.voice_client = getattr(guild, "voice_client", None)
        self.message = None

    async def send(self, *args, **kwargs):
        if self.channel and hasattr(self.channel, "send"):
            try:
                return await self.channel.send(*args, **kwargs)
            except Exception:
                pass
        return None


SPOTIFY_TRACK_REGEX = r"https?://open\.spotify\.com/track/([a-zA-Z0-9]+)"
SPOTIFY_PLAYLIST_REGEX = r"https?://open\.spotify\.com/playlist/([a-zA-Z0-9]+)"
SPOTIFY_ALBUM_REGEX = r"https?://open\.spotify\.com/album/([a-zA-Z0-9]+)"
MUSIC_URL_PATTERN = re.compile(r"https?://[^\s<>]+", re.IGNORECASE)
MUSIC_URL_HOSTS = {
    "spotify.com",
    "spotify.link",
    "youtube.com",
    "youtu.be",
    "soundcloud.com",
    "on.soundcloud.com",
    "music.apple.com",
    "jiosaavn.com",
    "saavn.com",
}


def is_supported_music_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
    except ValueError:
        return False

    if parsed.scheme.lower() not in {"http", "https"}:
        return False
    return any(host == domain or host.endswith(f".{domain}") for domain in MUSIC_URL_HOSTS)

class SpotifyAPI:
    BASE_URL = "https://api.spotify.com/v1"

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    async def get_token(self):
        auth_url = "https://accounts.spotify.com/api/token"
        auth_value = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode('utf-8')).decode('utf-8')
        headers = {"Authorization": f"Basic {auth_value}"}
        data = {"grant_type": "client_credentials"}
        async with aiohttp.ClientSession() as session:
            async with session.post(auth_url, headers=headers, data=data) as response:
                text = await response.text()
                if response.status != 200:
                    raise Exception(f"Failed to fetch token: {response.status}, response: {text}")
                self.token = (await response.json()).get("access_token")

    async def get(self, endpoint, params=None):
        retries = 2
        for attempt in range(retries):
            if not self.token or attempt > 0:
                await self.get_token()

            url = f"{self.BASE_URL}/{endpoint}"
            headers = {"Authorization": f"Bearer {self.token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 401 and attempt < retries - 1:
                        continue
                    elif response.status != 200:
                        raise Exception(f"Failed to fetch data from Spotify: {response.status}")
                    return await response.json()
        raise Exception("Exceeded max retries to fetch Spotify data")

    
    async def get_track(self, track_id):
        return await self.get(f"tracks/{track_id}")

    async def get_playlist(self, playlist_id):
        return await self.get(f"playlists/{playlist_id}")

spotify_api = SpotifyAPI(client_id="ac2b614ca5ce46a18dfd1d3475fd6fd9", client_secret="df7bec95ae88438e8286db597bac8621")

class PlatformSelectView(LayoutView):
    def __init__(self, ctx, query):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.query = query

        platforms = [
            ("YouTube", "ytsearch", discord.ButtonStyle.red),
            ("JioSaavn", "jssearch", discord.ButtonStyle.green),
            ("SoundCloud", "scsearch", discord.ButtonStyle.grey),
        ]
        buttons = []
        for name, source, style in platforms:
            btn = Button(label=name, style=style)
            btn.callback = self.create_callback(source)
            buttons.append(btn)

        container = build_container(
            TextDisplay("**Select a platform to search from:**"),
            Separator(visible=True),
            TextDisplay("Click a button below to choose."),
            Separator(visible=True),
            ActionRow(*buttons),
        )
        self.add_item(container)

    def create_callback(self, source):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("Only the command author can select a platform.", ephemeral=True)
                return
            await interaction.response.send_message(f"Searching...", ephemeral=True)
            await self.perform_search(source)
            await interaction.message.delete()
        return callback

    async def perform_search(self, source):
        results = await wavelink.Playable.search(self.query, source=source)
        if not results:
            return await self.ctx.send(view=CV2("No results found."))

        top_results = results[:5]
        await self.ctx.send(view=SearchResultView(self.ctx, top_results, self.query, source))

    

class SearchResultView(LayoutView):
    def __init__(self, ctx, results, query="", source=""):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.results = results

        lines = [f"**Top 5 Results for '{query}'**", ""]
        for i, track in enumerate(results, start=1):
            dur = f"{track.length // 1000 // 60}:{track.length // 1000 % 60:02d}"
            lines.append(f"`{i}.` **{track.title}** • `{dur}`")

        buttons = []
        for i in range(min(5, len(results))):
            btn = Button(label=str(i + 1), style=discord.ButtonStyle.primary)
            btn.callback = self.create_callback(i)
            buttons.append(btn)

        container = build_container(
            TextDisplay("\n".join(lines)),
            Separator(visible=True),
            ActionRow(*buttons),
        )
        self.add_item(container)

    def create_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("Only the command author can select a track.", ephemeral=True)
                return

            track = self.results[index]
            vc = self.ctx.voice_client
            if vc is None:
                vc = await self.ctx.author.voice.channel.connect(cls=wavelink.Player)
                vc.autoplay = wavelink.AutoPlayMode.disabled
                vc.smart_autoplay = True
            vc.ctx = self.ctx

            if not vc.playing:
                await vc.play(track)
                await interaction.response.send_message(f"Started playing `{track.title}`.")
                await self.ctx.cog.display_player_embed(vc, track, self.ctx)
            else:
                await vc.queue.put_wait(track)
                await interaction.response.send_message(f"Added `{track.title}` to the queue.")

        return callback


class VolumeModal(ui.Modal, title="🔊 Set Volume"):
    """Discord Modal that accepts volume % from 1 to 100."""
    volume_input = ui.TextInput(
        label="Volume (1% – 100%)",
        placeholder="Enter a number between 1 and 100...",
        min_length=1,
        max_length=3,
        required=True
    )

    def __init__(self, player):
        super().__init__()
        self.player = player
        curr_vol = getattr(player, "volume", 100)
        self.volume_input.default = str(curr_vol)

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.volume_input.value.strip().rstrip("%")
        if not raw.isdigit():
            return await interaction.response.send_message("❌ Please enter a **valid number** between 1 and 100.", ephemeral=True)
        pct = int(raw)
        if not (1 <= pct <= 100):
            return await interaction.response.send_message(f"❌ **{pct}%** is out of range. Enter a value between **1%** and **100%**.", ephemeral=True)

        await self.player.set_volume(pct)
        await interaction.response.send_message(f"🔊 Volume set to **{pct}%**", ephemeral=True)


class AddSongModal(ui.Modal, title="Search & Add Song to Queue"):
    """Discord Modal that lets a user type a song name or URL to add to the queue."""
    song_input = ui.TextInput(
        label="Song name or URL",
        placeholder="e.g. Pavazha Malli or https://youtu.be/...",
        min_length=2,
        max_length=200,
        required=True
    )

    def __init__(self, player, ctx):
        super().__init__()
        self.player = player
        self.ctx = ctx

    async def on_submit(self, interaction: discord.Interaction):
        query = self.song_input.value.strip()
        await interaction.response.defer(ephemeral=True)
        try:
            tracks = await wavelink.Playable.search(query)
            if not tracks:
                return await interaction.followup.send("❌ No tracks found for that search or URL.", ephemeral=True)
            track = tracks[0]
            await self.player.queue.put_wait(track)
            await interaction.followup.send(f"✅ Added **[{track.title}]({track.uri})** to the queue!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Could not add track: `{e}`", ephemeral=True)


class MusicControlQuickFilters(ui.LayoutView):
    """Expanded quick audio filters and DSP equalizer settings view."""
    def __init__(self, player):
        super().__init__(timeout=60)
        self.player = player
        
        container = ui.Container(accent_color=discord.Colour(0x2B2D31))
        container.add_item(TextDisplay("## 🎛️ Studio Audio Equalizer & Filters\nSelect a DSP sound profile to apply in real-time:"))
        
        btn_8d = ui.Button(label="8D Audio", emoji="🎧", style=discord.ButtonStyle.secondary, custom_id="filter_8d")
        btn_bass = ui.Button(label="Bass Boost", emoji="🔊", style=discord.ButtonStyle.secondary, custom_id="filter_bass")
        btn_nightcore = ui.Button(label="Nightcore", emoji="⚡", style=discord.ButtonStyle.secondary, custom_id="filter_nightcore")
        btn_vapor = ui.Button(label="Vaporwave", emoji="🌆", style=discord.ButtonStyle.secondary, custom_id="filter_vaporwave")
        btn_clear = ui.Button(label="Reset Filters", emoji="🔄", style=discord.ButtonStyle.danger, custom_id="filter_clear")

        btn_8d.callback = self._make_cb("8d", "🎧 8D Audio filter applied!")
        btn_bass.callback = self._make_cb("bassboost", "🔊 Bass Boost filter applied!")
        btn_nightcore.callback = self._make_cb("nightcore", "⚡ Nightcore filter applied!")
        btn_vapor.callback = self._make_cb("vaporwave", "🌆 Vaporwave filter applied!")
        btn_clear.callback = self._make_cb("reset", "🔄 Audio filters reset to default flat profile.")

        row1 = ui.ActionRow(btn_8d, btn_bass, btn_nightcore, btn_vapor)
        row2 = ui.ActionRow(btn_clear)
        container.add_item(row1)
        container.add_item(row2)
        self.add_item(container)

    def _make_cb(self, filter_name, msg_text):
        async def _cb(interaction: discord.Interaction):
            filter_cog = self.player.client.get_cog("FilterCog") if hasattr(self.player, "client") else None
            if filter_cog:
                if filter_name == "reset":
                    filter_cog.disable_all()
                    await self.player.set_filters(None)
                else:
                    await filter_cog.apply_filter_to_player(self.player, filter_name)
                await interaction.response.send_message(f"✨ **{msg_text}**", ephemeral=True)
            else:
                await interaction.response.send_message(f"Filter profile set to `{filter_name}`", ephemeral=True)
        return _cb


class SuggestedByAISelect(ui.Select):
    """Dropdown for AI song suggestions matching algorithmic recommendations."""
    def __init__(self, player, ctx, cog):
        self.player = player
        self.ctx = ctx
        self.cog = cog
        guild_id = player.guild.id if player and player.guild else 0

        suggestions = getattr(cog, "ai_suggestions", {}).get(guild_id, []) if cog else []
        options = []
        if suggestions:
            for s in suggestions[:5]:
                raw_title = getattr(s, "title", str(s))
                raw_artist = getattr(s, "author", "Artist")
                uri = getattr(s, "uri", str(s))

                lbl = raw_title[:95] if raw_title else "Suggested Track"
                desc = f"{raw_artist}"[:95]
                val = str(uri)[:100]

                options.append(discord.SelectOption(
                    label=lbl,
                    value=val,
                    description=desc,
                    emoji="🎵"
                ))

        if not options:
            options = [
                discord.SelectOption(
                    label="Analyzing recommendations...",
                    value="pending",
                    description="AI is selecting top related tracks",
                    emoji="✨"
                )
            ]

        super().__init__(
            placeholder="Suggested by AI",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="select_ai_suggestions",
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.voice or (interaction.guild.voice_client and interaction.guild.voice_client.channel != interaction.user.voice.channel):
            return await interaction.response.send_message("❌ You must be in the same voice channel!", ephemeral=True)

        selected_val = self.values[0]
        if selected_val == "pending":
            return await interaction.response.send_message("✨ AI is analyzing recommendations for this track. Please try again in a moment!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            tracks = await wavelink.Playable.search(selected_val)
            if tracks:
                track = tracks[0]
                await self.player.queue.put_wait(track)
                await interaction.followup.send(f"✨ **Added AI Recommendation to queue:** `[{track.title}]({track.uri})`", ephemeral=True)
            else:
                await interaction.followup.send("❌ Could not load the selected recommendation.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error adding suggested track: `{e}`", ephemeral=True)


class MusicControlView(LayoutView):
    """Modern Components V2 Music Player Controls matching Yuna's aesthetic."""
    def __init__(self, player, ctx, track=None, autoplay=False, has_card=True):
        super().__init__(timeout=None)
        self.player = player
        self.ctx = ctx
        self.track = track
        self.has_card = has_card
        self.cog = ctx.cog if ctx and hasattr(ctx, "cog") else None
        self.guild_id = player.guild.id if player and player.guild else 0
        self.build_components()
        self.update_button_styles()

    def build_components(self):
        self.clear_items()

        # ── V2 Container: Groups all player UI into a single component ──
        container = ui.Container(accent_color=discord.Colour(0x2B2D31))

        # ── TOP: Music Player Card (Components V2 Media Gallery) ──
        if self.has_card:
            mg = ui.MediaGallery(discord.MediaGalleryItem("attachment://music_card.png"))
            container.add_item(mg)
        elif self.track:
            sec = getattr(self.track, 'length', 0) // 1000
            duration = f"{sec // 60:02d}:{sec % 60:02d}"
            title_text = f"**Now Playing [{self.track.title}]({self.track.uri})**"
            bullet_text = f"• **Author:** `{self.track.author}` | **Duration:** `{duration}`"
            container.add_item(TextDisplay(f"{title_text}\n{bullet_text}"))

        # ── ROW 0: AI Suggestions Dropdown ──
        r0 = ui.ActionRow()
        r0.add_item(SuggestedByAISelect(self.player, self.ctx, self.cog))
        container.add_item(r0)

        # ── ROW 1: Playback Controls (4 buttons) ──
        self.btn_loop = ui.Button(emoji="<:loop:1562114982286721094>", style=discord.ButtonStyle.secondary, custom_id="btn_loop")
        self.btn_loop.callback = self._cb_loop

        self.btn_prev = ui.Button(emoji="<:previous:1562115003442794589>", style=discord.ButtonStyle.secondary, custom_id="btn_prev")
        self.btn_prev.callback = self._cb_previous

        self.btn_play_pause = ui.Button(emoji="<:playpause:1562115013718577222>", style=discord.ButtonStyle.secondary, custom_id="btn_play_pause")
        self.btn_play_pause.callback = self._cb_pause

        self.btn_skip = ui.Button(emoji="<:next:1562115023495495750>", style=discord.ButtonStyle.secondary, custom_id="btn_skip")
        self.btn_skip.callback = self._cb_skip

        r1 = ui.ActionRow(self.btn_loop, self.btn_prev, self.btn_play_pause, self.btn_skip)
        container.add_item(r1)

        # ── ROW 2: Volume & Quick Seek (4 buttons) ──
        self.btn_volume = ui.Button(emoji="<:volume:1562115086309662812>", style=discord.ButtonStyle.secondary, custom_id="btn_volume")
        self.btn_volume.callback = self._cb_volume

        self.btn_seek_back = ui.Button(emoji="<:sec10:1562114949440872470>", style=discord.ButtonStyle.secondary, custom_id="btn_seek_back")
        self.btn_seek_back.callback = self._cb_seek_back

        self.btn_stop = ui.Button(emoji="<:stopmusic:1562114968646848542>", style=discord.ButtonStyle.secondary, custom_id="btn_stop")
        self.btn_stop.callback = self._cb_stop

        self.btn_seek_forward = ui.Button(emoji="<:sec10plus:1562114958949355623>", style=discord.ButtonStyle.secondary, custom_id="btn_seek_forward")
        self.btn_seek_forward.callback = self._cb_seek_forward

        r2 = ui.ActionRow(self.btn_volume, self.btn_seek_back, self.btn_stop, self.btn_seek_forward)
        container.add_item(r2)

        # ── ROW 3: Shuffle, Search, Favorite & History (4 buttons) ──
        self.btn_shuffle = ui.Button(emoji="<:shuffle:1562115097093214209>", style=discord.ButtonStyle.secondary, custom_id="btn_shuffle")
        self.btn_shuffle.callback = self._cb_shuffle

        self.btn_search = ui.Button(emoji="<:musicsearch:1562115115468193894>", style=discord.ButtonStyle.secondary, custom_id="btn_search")
        self.btn_search.callback = self._cb_search

        self.btn_favorite = ui.Button(emoji="<a:heart:1562113133575933972>", style=discord.ButtonStyle.secondary, custom_id="btn_favorite")
        self.btn_favorite.callback = self._cb_favorite

        self.btn_history = ui.Button(emoji="<:history:1562115126180716644>", style=discord.ButtonStyle.secondary, custom_id="btn_history")
        self.btn_history.callback = self._cb_history

        r3 = ui.ActionRow(self.btn_shuffle, self.btn_search, self.btn_favorite, self.btn_history)
        container.add_item(r3)

        # ── ROW 4: Autoplay & Music Control (2 buttons) ──
        self.btn_autoplay = ui.Button(emoji="<a:enable:1562111115662598295>", label="Autoplay", style=discord.ButtonStyle.secondary, custom_id="btn_autoplay")
        self.btn_autoplay.callback = self._cb_autoplay

        self.btn_open_controls = ui.Button(emoji="<:musiccontrol:1562111127259848805>", label="Music Control", style=discord.ButtonStyle.secondary, custom_id="btn_open_controls")
        self.btn_open_controls.callback = self._cb_open_controls

        r4 = ui.ActionRow(self.btn_autoplay, self.btn_open_controls)
        container.add_item(r4)

        self.add_item(container)

    def update_button_styles(self):
        is_paused = getattr(self.player, "paused", False)
        is_loop = (getattr(self.player.queue, "mode", None) == wavelink.QueueMode.loop) if hasattr(self.player, "queue") else False
        is_autoplay = getattr(self.player, "smart_autoplay", True)

        if hasattr(self, "btn_play_pause"):
            self.btn_play_pause.style = discord.ButtonStyle.success if is_paused else discord.ButtonStyle.secondary

        if hasattr(self, "btn_loop"):
            self.btn_loop.style = discord.ButtonStyle.success if is_loop else discord.ButtonStyle.secondary

        if hasattr(self, "btn_autoplay"):
            self.btn_autoplay.style = discord.ButtonStyle.success if is_autoplay else discord.ButtonStyle.secondary
            self.btn_autoplay.emoji = "<a:enable:1562111115662598295>" if is_autoplay else "<:disable:1562115051215659078>"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not self.player or not getattr(self.player, "playing", False):
            if not getattr(self.player, "connected", False):
                await interaction.response.send_message("I'm not currently playing in this channel anymore.", ephemeral=True)
                return False
        if interaction.user.voice and self.ctx.voice_client and interaction.user.voice.channel == self.ctx.voice_client.channel:
            return True
        await interaction.response.send_message("❌ Only members in the same voice channel can control the player.", ephemeral=True)
        return False

    async def _cb_loop(self, interaction: discord.Interaction):
        if not await self.interaction_check(interaction): return
        is_loop = (self.player.queue.mode == wavelink.QueueMode.loop)
        self.player.queue.mode = wavelink.QueueMode.normal if is_loop else wavelink.QueueMode.loop
        self.update_button_styles()
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass
        status = "Disabled" if is_loop else "Enabled"
        await interaction.response.send_message(f"🔁 Loop mode **{status}**.", ephemeral=True)

    async def _cb_previous(self, interaction: discord.Interaction):
        if not await self.interaction_check(interaction): return
        guild_id = interaction.guild.id
        if guild_id in track_histories and len(track_histories[guild_id]) > 1:
            track_histories[guild_id].pop()
            previous_track = track_histories[guild_id][-1]
            if self.player.playing:
                await self.player.stop()
            await self.player.queue.put_wait(previous_track)
            await interaction.response.send_message(f"⏮️ Playing previous track: **{previous_track.title}**.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No previous track available in history.", ephemeral=True)

    async def _cb_pause(self, interaction: discord.Interaction):
        if not await self.interaction_check(interaction): return
        if self.player.paused:
            await self.player.pause(False)
            self.update_button_styles()
            try:
                await interaction.message.edit(view=self)
            except Exception:
                pass
            await interaction.response.send_message(f"▶️ Resumed by **{interaction.user.display_name}**.", ephemeral=True)
        elif self.player.playing:
            await self.player.pause(True)
            self.update_button_styles()
            try:
                await interaction.message.edit(view=self)
            except Exception:
                pass
            await interaction.response.send_message(f"⏸️ Paused by **{interaction.user.display_name}**.", ephemeral=True)

    async def _cb_skip(self, interaction: discord.Interaction):
        if not await self.interaction_check(interaction): return
        if getattr(self.player, "smart_autoplay", True) or not self.player.queue.is_empty:
            if self.player.current and self.cog:
                session = self.cog.get_session(self.player.guild.id)
                session.record_skip(self.player.current.title)
                self.player.client.loop.create_task(self.cog.telemetry.log_event(
                    event_type=MusicTelemetryEvent.SKIP,
                    guild_id=self.player.guild.id,
                    user_id=interaction.user.id,
                    track_id=getattr(self.player.current, "identifier", ""),
                    title=getattr(self.player.current, "title", ""),
                    artist=getattr(self.player.current, "author", ""),
                    track_duration=(self.player.current.length / 1000.0) if getattr(self.player.current, "length", None) else 0,
                    played_seconds=(self.player.position / 1000.0) if getattr(self.player, "position", None) else 0,
                ))
            await self.player.stop()
            await interaction.response.send_message(f"⏭️ Skipped by **{interaction.user.display_name}**.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No song in queue to skip.", ephemeral=True)

    async def _cb_volume(self, interaction: discord.Interaction):
        if not await self.interaction_check(interaction): return
        await interaction.response.send_modal(VolumeModal(self.player))

    async def _cb_seek_back(self, interaction: discord.Interaction):
        if not await self.interaction_check(interaction): return
        if self.player.playing:
            new_pos = max(0, self.player.position - 10000)
            await self.player.seek(new_pos)
            sec = new_pos // 1000
            await interaction.response.send_message(f"⏪ Rewound to **{sec // 60}:{sec % 60:02d}**", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)

    async def _cb_stop(self, interaction: discord.Interaction):
        if not await self.interaction_check(interaction): return
        guild_id = self.player.guild.id
        if hasattr(self.player, "queue"):
            self.player.queue.clear()
        if self.cog and hasattr(self.cog, "remove_session"):
            self.cog.remove_session(guild_id)
        keep_connected = self.cog and self.cog.is_247_enabled(guild_id)
        if keep_connected:
            await self.player.stop()
        else:
            await self.player.disconnect()
        embed = discord.Embed(
            description=(
                "<:stopmusic:1562114968646848542> **Playback stopped and queue cleared. 24/7 mode keeps me connected.**"
                if keep_connected
                else "<:stopmusic:1562114968646848542> **Stopped playback and cleared the queue.**"
            ),
            color=0x2B2D31
        )
        try:
            await interaction.response.edit_message(attachments=[], embed=embed, view=None)
        except Exception:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _cb_seek_forward(self, interaction: discord.Interaction):
        if not await self.interaction_check(interaction): return
        if self.player.playing:
            duration = self.player.current.length if self.player.current else 0
            new_pos = min(max(0, duration - 5000), self.player.position + 10000) if duration else self.player.position + 10000
            await self.player.seek(new_pos)
            sec = new_pos // 1000
            await interaction.response.send_message(f"⏩ Forwarded to **{sec // 60}:{sec % 60:02d}**", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)

    async def _cb_shuffle(self, interaction: discord.Interaction):
        if not await self.interaction_check(interaction): return
        if self.player.queue:
            random.shuffle(self.player.queue)
            await interaction.response.send_message(f"<:shuffle:1562115097093214209> Queue shuffled by **{interaction.user.display_name}**.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Queue is empty.", ephemeral=True)

    async def _cb_search(self, interaction: discord.Interaction):
        if not await self.interaction_check(interaction): return
        await interaction.response.send_modal(AddSongModal(self.player, self.ctx))

    async def _cb_favorite(self, interaction: discord.Interaction):
        if not await self.interaction_check(interaction): return
        track = self.player.current
        if track:
            await interaction.response.send_message(f"<a:heart:1562113133575933972> Added **{track.title}** to your favorites!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No track currently playing.", ephemeral=True)

    async def _cb_history(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        history = track_histories.get(guild_id, [])
        queue_len = len(self.player.queue) if hasattr(self.player, "queue") else 0
        if not history and queue_len == 0:
            return await interaction.response.send_message("<:history:1562115126180716644> No tracks in history or upcoming queue.", ephemeral=True)

        lines = []
        if history:
            lines.append("**Recent History:**")
            for i, t in enumerate(reversed(history[-5:])):
                lines.append(f"• `[{getattr(t, 'title', str(t))[:50]}]`")
        if queue_len > 0:
            lines.append(f"\n**Upcoming Queue ({queue_len} tracks):**")
            for i, t in enumerate(list(self.player.queue)[:5]):
                lines.append(f"{i+1}. `{getattr(t, 'title', str(t))[:50]}`")

        embed = discord.Embed(title="<:history:1562115126180716644> Session History & Queue", description="\n".join(lines), color=0x2B2D31)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _cb_autoplay(self, interaction: discord.Interaction):
        if not await self.interaction_check(interaction): return
        is_auto = getattr(self.player, "smart_autoplay", True)
        self.player.smart_autoplay = not is_auto
        self.player.autoplay = wavelink.AutoPlayMode.disabled


        self.update_button_styles()
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass
        status = "Disabled" if is_auto else "Enabled"
        emoji = "<:disable:1562115051215659078>" if is_auto else "<a:enable:1562111115662598295>"
        await interaction.response.send_message(f"{emoji} Smart ML Autoplay **{status}**.", ephemeral=True)

    async def _cb_open_controls(self, interaction: discord.Interaction):
        if not await self.interaction_check(interaction): return
        view = MusicControlQuickFilters(self.player)
        await interaction.response.send_message(view=view, ephemeral=True)


class MusicURLConfirmationView(LayoutView):
    def __init__(self, cog, ctx, url):
        super().__init__(timeout=15)
        self.cog = cog
        self.ctx = ctx
        self.url = url
        self.author_id = ctx.author.id
        self.message = None

        self.status_display = TextDisplay("**Want to play this audio?**")
        self.yes_button = Button(label="Yes", style=discord.ButtonStyle.success)
        self.no_button = Button(label="No", style=discord.ButtonStyle.secondary)
        self.yes_button.callback = self._yes
        self.no_button.callback = self._no

        container = build_container(
            self.status_display,
            Separator(visible=True),
            TextDisplay(url),
            Separator(visible=True),
            ActionRow(self.yes_button, self.no_button),
        )
        self.add_item(container)

    async def _check_owner(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Only the person who posted this link can choose.", ephemeral=True
            )
            return False
        return True

    async def _yes(self, interaction: discord.Interaction):
        if not await self._check_owner(interaction):
            return

        self.yes_button.disabled = True
        self.no_button.disabled = True
        self.status_display.content = "**Starting playback...**"
        await interaction.response.edit_message(view=self)
        self.stop()
        await self.cog.play_confirmed_url(self.ctx, self.url)

    async def _no(self, interaction: discord.Interaction):
        if not await self._check_owner(interaction):
            return

        self.yes_button.disabled = True
        self.no_button.disabled = True
        self.status_display.content = "**Playback cancelled.**"
        await interaction.response.edit_message(view=self)
        self.stop()

    async def on_timeout(self):
        self.yes_button.disabled = True
        self.no_button.disabled = True
        self.status_display.content = "**Confirmation expired.**"
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


class Music(commands.Cog):
    def __init__(self, client: zyuna):
        global _music_cog_instance
        self.client = client
        _music_cog_instance = self
        
        self.inactivity_timeout = 120
        self.ai_suggestions = {} 
        self.player_inactivity = {}
        self._inactivity_tasks = {}
        self._247_modes = self.load_247_modes()
        self._restoring = False
        self._restored = False
        self._recovery_lock = asyncio.Lock()
        
        # ML Music Intelligence & Session Subsystem
        self.sessions: Dict[int, MusicSessionState] = {}
        self.search_ranker = SearchRankingModel()
        self.ranking_model = RankingModel()
        self.bandit = ContextualBandit()
        self.telemetry = InteractionLogger.get_instance()
        
        self.periodic_save_sessions.start()
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.connect_nodes())
            loop.create_task(self.monitor_inactivity())
            loop.create_task(self.telemetry.initialize())
        except RuntimeError:
            pass

    async def cog_unload(self):
        self.save_all_sessions_sync()
        if hasattr(self, "periodic_save_sessions"):
            self.periodic_save_sessions.cancel()

    def load_247_modes(self) -> Dict[str, int]:
        try:
            with open(MUSIC_247_FILE, "r", encoding="utf-8") as file:
                stored_modes = json.load(file)
            return {
                str(int(guild_id)): int(channel_id)
                for guild_id, channel_id in stored_modes.items()
            }
        except (OSError, ValueError, TypeError, AttributeError):
            return {}

    def save_247_modes(self):
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            temp_file = MUSIC_247_FILE + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as file:
                json.dump(self._247_modes, file, indent=2)
            os.replace(temp_file, MUSIC_247_FILE)
        except OSError as error:
            print(f"[Music 24/7] Could not save mode settings: {error}")

    def is_247_enabled(self, guild_id: int) -> bool:
        return str(guild_id) in self._247_modes

    def enable_247_mode(self, guild_id: int, channel_id: int):
        self._247_modes[str(guild_id)] = int(channel_id)
        self.save_247_modes()

    def disable_247_mode(self, guild_id: int):
        self._247_modes.pop(str(guild_id), None)
        self.save_247_modes()

    def cancel_inactivity_timer(self, guild_id: int):
        task = self._inactivity_tasks.pop(guild_id, None)
        if task and not task.done():
            task.cancel()

    def get_session(self, guild_id: int) -> MusicSessionState:
        if guild_id not in self.sessions:
            self.sessions[guild_id] = MusicSessionState(guild_id)
        return self.sessions[guild_id]

    async def precompute_ai_suggestions(self, guild_id: int, current_track_dict: dict):
        try:
            session = self.get_session(guild_id)
            queries = AutoplayEngine.generate_smart_queries(
                current_track_dict,
                lang_pref=session.active_language if session.language_established else "auto",
                mood_pref=session.get_next_balanced_mood()
            )
            gathered_playables = []
            for q in queries[:2]:
                try:
                    res = await wavelink.Playable.search(q)
                    if res:
                        if isinstance(res, wavelink.Playlist):
                            gathered_playables.extend(res.tracks[:5])
                        else:
                            gathered_playables.extend(res[:5])
                except Exception:
                    pass

            if not gathered_playables:
                return

            candidates = []
            for t in gathered_playables:
                candidates.append({
                    "title": t.title,
                    "uploader": t.author,
                    "artist": t.author,
                    "duration": (t.length / 1000.0) if hasattr(t, "length") and t.length else 0,
                    "url": getattr(t, "uri", ""),
                    "id": getattr(t, "identifier", ""),
                    "source": getattr(t, "source", "youtube"),
                    "playable": t,
                })

            scored = self.ranking_model.rank_candidates(candidates, session_state=session)
            history_set = {
                normalize_title(t.get("title", ""))
                for t in session.recent_tracks
            }
            history_set.add(normalize_title(current_track_dict.get("title", "")))

            suggestions = []
            for score, c in scored:
                if score <= -100.0:
                    continue
                if AutoplayEngine.is_fuzzy_duplicate(c, history_set):
                    continue
                p = c.get("playable")
                if p and p not in suggestions:
                    suggestions.append(p)
                if len(suggestions) >= 5:
                    break

            if suggestions:
                self.ai_suggestions[guild_id] = suggestions
        except Exception as e:
            print(f"[ML AI Suggestions] Error: {e}")

    async def fetch_smart_autoplay_track(self, player: wavelink.Player, last_track: Any) -> Optional[wavelink.Playable]:
        try:
            guild_id = player.guild.id
            session = self.get_session(guild_id)
            last_dict = {
                "title": getattr(last_track, "title", ""),
                "uploader": getattr(last_track, "author", ""),
                "artist": getattr(last_track, "author", ""),
                "duration": (last_track.length / 1000.0) if hasattr(last_track, "length") and last_track.length else 0,
                "url": getattr(last_track, "uri", ""),
                "id": getattr(last_track, "identifier", ""),
            }
            session.record_played_track(last_dict, is_manual=False)

            queries = AutoplayEngine.generate_smart_queries(
                last_dict,
                lang_pref=session.active_language if session.language_established else "auto",
                mood_pref=session.get_next_balanced_mood()
            )

            gathered_candidates = []
            played_history_set = {
                normalize_title(t.get("title", "")) for t in session.recent_tracks
            }
            for t in session.recent_tracks:
                if t.get("id"):
                    played_history_set.add(str(t["id"]))
                if t.get("url"):
                    played_history_set.add(str(t["url"]))

            for q in queries[:3]:
                try:
                    res = await wavelink.Playable.search(q)
                    if res:
                        tracks_list = res.tracks if isinstance(res, wavelink.Playlist) else res
                        for t in tracks_list[:6]:
                            c = {
                                "title": t.title,
                                "uploader": t.author,
                                "artist": t.author,
                                "duration": (t.length / 1000.0) if hasattr(t, "length") and t.length else 0,
                                "url": getattr(t, "uri", ""),
                                "id": getattr(t, "identifier", ""),
                                "source": getattr(t, "source", "youtube"),
                                "playable": t,
                            }
                            if not AutoplayEngine.is_fuzzy_duplicate(c, played_history_set):
                                gathered_candidates.append(c)
                except Exception:
                    continue

                if len(gathered_candidates) >= 12:
                    break

            if not gathered_candidates:
                return None

            scored = self.ranking_model.rank_candidates(gathered_candidates, session_state=session)
            chosen_entry = self.bandit.select_best_track(scored, session_state=session, played_history_set=played_history_set)
            if chosen_entry and "playable" in chosen_entry:
                chosen_playable = chosen_entry["playable"]
                track_dict = {
                    "title": chosen_playable.title,
                    "uploader": chosen_playable.author,
                    "artist": chosen_playable.author,
                    "duration": (chosen_playable.length / 1000.0) if hasattr(chosen_playable, "length") and chosen_playable.length else 0,
                    "url": getattr(chosen_playable, "uri", ""),
                    "id": getattr(chosen_playable, "identifier", ""),
                }
                session.record_played_track(track_dict, is_manual=False)
                self.client.loop.create_task(self.precompute_ai_suggestions(guild_id, track_dict))
                return chosen_playable

            return None
        except Exception as e:
            print(f"[ML AUTOPLAY ERROR] {e}")
            return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        # Let recognized commands and non-empty configured prefixes follow their
        # usual path. Some users have an empty prefix, so ctx.prefix can be ""
        # even for an ordinary message.
        ctx = await self.client.get_context(message)
        if ctx.valid or (ctx.prefix and message.content.startswith(ctx.prefix)):
            return

        urls = []
        for match in MUSIC_URL_PATTERN.finditer(message.content):
            url = match.group(0).rstrip(".,!?;:)]}")
            if is_supported_music_url(url):
                urls.append(url)

        # A single link is unambiguous; multiple links should not trigger an
        # unexpected playback choice.
        if len(urls) != 1:
            return

        view = MusicURLConfirmationView(self, ctx, urls[0])
        try:
            view.message = await message.channel.send(view=view)
        except discord.HTTPException:
            return

    async def play_confirmed_url(self, ctx: commands.Context, url: str):
        original_command = ctx.command
        ctx.command = self.play
        try:
            await self.play.can_run(ctx)
            self.play._prepare_cooldowns(ctx)
            await self.play(ctx, query=url)
        except commands.CommandError as error:
            await ctx.send(view=CV2(f"{WARNING} {error}"))
        except Exception as error:
            print(f"[Music URL Confirmation] Playback failed: {error}")
            await ctx.send(view=CV2("I couldn't start playback for that link."))
        finally:
            ctx.command = original_command

    def serialize_player(self, player: wavelink.Player) -> dict | None:
        if not player or not player.channel or not player.current:
            return None

        current_track = player.current
        raw_data = getattr(current_track, "raw_data", None)
        current_dict = {
            "title": current_track.title,
            "author": current_track.author,
            "uri": current_track.uri,
            "length": current_track.length,
            "position": max(0, player.position),
            "is_stream": getattr(current_track, "is_stream", False),
            "raw_data": raw_data,
        }

        queue_list = []
        for t in player.queue:
            queue_list.append({
                "title": t.title,
                "author": t.author,
                "uri": t.uri,
                "length": t.length,
                "is_stream": getattr(t, "is_stream", False),
                "raw_data": getattr(t, "raw_data", None)
            })

        text_channel_id = None
        requester_id = None
        if hasattr(player, "ctx") and player.ctx:
            if hasattr(player.ctx, "channel") and player.ctx.channel:
                text_channel_id = player.ctx.channel.id
            if hasattr(player.ctx, "author") and player.ctx.author:
                requester_id = player.ctx.author.id

        loop_mode = "normal"
        if hasattr(player.queue, "mode"):
            if player.queue.mode == wavelink.QueueMode.loop:
                loop_mode = "loop"
            elif player.queue.mode == wavelink.QueueMode.loop_all:
                loop_mode = "loop_all"

        autoplay = getattr(player, "smart_autoplay", True)
        
        active_filter = None
        filter_cog = self.client.get_cog("FilterCog")
        if filter_cog and hasattr(filter_cog, "active_filters"):
            active_filter = filter_cog.active_filters.get(player.guild.id)

        return {
            "guild_id": player.guild.id,
            "voice_channel_id": player.channel.id,
            "text_channel_id": text_channel_id,
            "requester_id": requester_id,
            "current_track": current_dict,
            "queue": queue_list,
            "volume": player.volume,
            "loop_mode": loop_mode,
            "autoplay": autoplay,
            "paused": player.paused,
            "filter": active_filter,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    def load_sessions(self) -> dict:
        if not os.path.exists(SESSIONS_FILE):
            return {}
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_sessions(self, sessions: dict):
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            temp_file = SESSIONS_FILE + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(sessions, f, indent=2)
            os.replace(temp_file, SESSIONS_FILE)
        except Exception:
            pass

    def save_all_sessions_sync(self):
        sessions = {}
        for vc in self.client.voice_clients:
            if isinstance(vc, wavelink.Player) and (vc.playing or vc.paused) and vc.current:
                data = self.serialize_player(vc)
                if data:
                    sessions[str(vc.guild.id)] = data
        self.save_sessions(sessions)

    def remove_session(self, guild_id: int):
        sessions = self.load_sessions()
        key = str(guild_id)
        if key in sessions:
            sessions.pop(key, None)
            self.save_sessions(sessions)

    def update_session(self, player: wavelink.Player):
        if not player or not player.guild:
            return
        sessions = self.load_sessions()
        if (player.playing or player.paused) and player.current:
            data = self.serialize_player(player)
            if data:
                sessions[str(player.guild.id)] = data
                self.save_sessions(sessions)
        else:
            self.remove_session(player.guild.id)

    @tasks.loop(seconds=3)
    async def periodic_save_sessions(self):
        try:
            sessions = self.load_sessions()
            current_guild_ids = set()

            for vc in self.client.voice_clients:
                if isinstance(vc, wavelink.Player) and (vc.playing or vc.paused) and vc.current:
                    data = self.serialize_player(vc)
                    if data:
                        sessions[str(vc.guild.id)] = data
                        current_guild_ids.add(str(vc.guild.id))

            for g_id in list(sessions.keys()):
                guild = self.client.get_guild(int(g_id))
                if not guild:
                    sessions.pop(g_id, None)
                elif g_id not in current_guild_ids and guild.voice_client is None:
                    sessions.pop(g_id, None)

            self.save_sessions(sessions)
        except Exception:
            pass

    async def reconstruct_track(self, track_data: dict) -> wavelink.Playable | None:
        if not track_data or not isinstance(track_data, dict):
            return None

        raw = track_data.get("raw_data")
        if raw and isinstance(raw, dict):
            try:
                return wavelink.Playable(raw)
            except Exception:
                pass

        query = track_data.get("uri") or f"{track_data.get('title', '')} {track_data.get('author', '')}".strip()
        if query:
            try:
                results = await wavelink.Playable.search(query)
                if results:
                    return results[0] if not isinstance(results, wavelink.Playlist) else results.tracks[0]
            except Exception:
                pass

        return None

    async def restore_music_sessions(self):
        async with self._recovery_lock:
            if self._restored:
                return
            self._restored = True
            self._restoring = True

        try:
            await self.client.wait_until_ready()

            connected_node = None
            for _ in range(45):
                try:
                    node = wavelink.Pool.get_node()
                    if node and node.status == wavelink.NodeStatus.CONNECTED:
                        connected_node = node
                        break
                except Exception:
                    pass
                await asyncio.sleep(1)

            if not connected_node:
                self._restored = False
                return

            sessions = self.load_sessions()
            if sessions:
                print(f"{Fore.CYAN}{Style.BRIGHT}[MUSIC RECOVERY] Found {len(sessions)} active session(s) to restore after restart.")

            for guild_id_str, data in list(sessions.items()):
                try:
                    guild_id = int(guild_id_str)
                    guild = self.client.get_guild(guild_id)
                    if not guild:
                        continue

                    voice_channel_id = data.get("voice_channel_id")
                    voice_channel = guild.get_channel(voice_channel_id)
                    if not voice_channel or not isinstance(voice_channel, (discord.VoiceChannel, discord.StageChannel)):
                        self.remove_session(guild_id)
                        continue

                    vc: wavelink.Player = guild.voice_client
                    if not vc:
                        try:
                            vc = await voice_channel.connect(cls=wavelink.Player)
                        except Exception as e:
                            print(f"{Fore.RED}[MUSIC RECOVERY ERROR] Failed to connect to {voice_channel.name} in {guild.name}: {e}")
                            continue

                    text_channel_id = data.get("text_channel_id")
                    text_channel = guild.get_channel(text_channel_id) if text_channel_id else None
                    if not text_channel or not isinstance(text_channel, (discord.TextChannel, discord.Thread)):
                        text_channel = voice_channel

                    requester_id = data.get("requester_id")
                    requester = guild.get_member(requester_id) if requester_id else None

                    vc.ctx = RestoredMusicContext(self.client, guild, text_channel, requester)
                    vc.ctx.voice_client = vc

                    volume = data.get("volume", 100)
                    try:
                        await vc.set_volume(volume)
                    except Exception:
                        pass

                    loop_mode = data.get("loop_mode", "normal")
                    if loop_mode == "loop":
                        vc.queue.mode = wavelink.QueueMode.loop
                    elif loop_mode == "loop_all":
                        vc.queue.mode = wavelink.QueueMode.loop_all
                    else:
                        vc.queue.mode = wavelink.QueueMode.normal

                    if data.get("autoplay", True):
                        vc.autoplay = wavelink.AutoPlayMode.disabled
                        vc.smart_autoplay = True
                    else:
                        vc.autoplay = wavelink.AutoPlayMode.disabled
                        vc.smart_autoplay = False

                    queue_items = data.get("queue", [])
                    for q_item in queue_items:
                        q_track = await self.reconstruct_track(q_item)
                        if q_track:
                            await vc.queue.put_wait(q_track)

                    current_data = data.get("current_track")
                    if current_data:
                        current_track = await self.reconstruct_track(current_data)
                        if current_track:
                            start_pos = int(current_data.get("position", 0))
                            if current_track.length and start_pos >= current_track.length:
                                start_pos = 0
                            elif start_pos < 0:
                                start_pos = 0

                            if getattr(current_track, "is_stream", False):
                                start_pos = 0

                            paused = data.get("paused", False)

                            await vc.play(current_track, start=start_pos, volume=volume, paused=paused)

                            saved_filter = data.get("filter")
                            if saved_filter:
                                filter_cog = self.client.get_cog("FilterCog")
                                if filter_cog and hasattr(filter_cog, "apply_filter_to_player"):
                                    try:
                                        await filter_cog.apply_filter_to_player(vc, saved_filter)
                                    except Exception:
                                        pass

                            try:
                                await voice_channel.edit(status=f"{MUSIC_ALT1} Playing: {current_track.title}")
                            except Exception:
                                pass

                            if text_channel and hasattr(text_channel, "send"):
                                try:
                                    sec = start_pos // 1000
                                    time_str = f"{sec // 60:02d}:{sec % 60:02d}"
                                    tot_sec = current_track.length // 1000 if current_track.length else 0
                                    tot_str = f"{tot_sec // 60:02d}:{tot_sec % 60:02d}"
                                    queue_len = len(queue_items)

                                    resume_view = CV2(
                                        f"🎵 Playback Resumed (Server Restart)",
                                        f"Playback of **[{current_track.title}]({current_track.uri or serverLink})** has uninterruptedly resumed at `{time_str} / {tot_str}`.",
                                        f"• **Queue Preserved:** `{queue_len}` song{'s' if queue_len != 1 else ''}\n"
                                        f"• **Volume:** `{volume}%` | **Channel:** {voice_channel.mention}"
                                    )
                                    await text_channel.send(view=resume_view)
                                except Exception:
                                    pass

                            print(f"{Fore.GREEN}{Style.BRIGHT}[MUSIC RECOVERY SUCCESS] Resumed '{current_track.title}' in {guild.name} ({voice_channel.name}) at {start_pos}ms.")

                except Exception as e:
                    print(f"{Fore.RED}[MUSIC RECOVERY ERROR] Failed to restore session for guild {guild_id_str}: {e}")

            await self.restore_247_connections()

        finally:
            self._restoring = False  

    async def restore_247_connections(self):
        for guild_id, channel_id in list(self._247_modes.items()):
            guild = self.client.get_guild(int(guild_id))
            if not guild or guild.voice_client:
                continue

            voice_channel = guild.get_channel(channel_id)
            if not isinstance(voice_channel, (discord.VoiceChannel, discord.StageChannel)):
                continue

            try:
                player = await voice_channel.connect(cls=wavelink.Player)
                player.autoplay = wavelink.AutoPlayMode.disabled
                player.smart_autoplay = True
                player.ctx = RestoredMusicContext(self.client, guild, voice_channel, guild.me)
                player.ctx.voice_client = player
                print(f"{Fore.GREEN}{Style.BRIGHT}[MUSIC 24/7] Reconnected in {guild.name} ({voice_channel.name}).")
            except Exception as error:
                print(f"{Fore.RED}[MUSIC 24/7] Could not reconnect in {guild.name}: {error}")

    async def reconnect_247(self, guild_id: int):
        await asyncio.sleep(3)
        if self.is_247_enabled(guild_id):
            await self.restore_247_connections()

    async def monitor_inactivity(self):
        while True:
            for guild in self.client.guilds:
                await self.check_inactivity(guild.id) 
            await asyncio.sleep(60) 

    async def check_inactivity(self, guild_id):
        guild = self.client.get_guild(guild_id)
        if not guild:
            self.cancel_inactivity_timer(guild_id)
            return

        player = guild.voice_client
        if (
            not player
            or self.is_247_enabled(guild_id)
            or not player.playing
            or not player.channel
            or len(player.channel.members) != 1
        ):
            self.cancel_inactivity_timer(guild_id)
            return

        task = self._inactivity_tasks.get(guild_id)
        if task is None or task.done():
            self._inactivity_tasks[guild_id] = asyncio.create_task(self.inactivity_timer(player))

    async def inactivity_timer(self, player):
        guild_id = player.guild.id
        try:
            await asyncio.sleep(self.inactivity_timeout)
            if (
                self.is_247_enabled(guild_id)
                or player.guild.voice_client is not player
                or not player.playing
                or not player.channel
                or len(player.channel.members) != 1
            ):
                return

            await player.disconnect(force=True)
            self.remove_session(guild_id)
            support = Button(label='Support', style=discord.ButtonStyle.link, url=serverLink)
            vote = Button(label='Vote', style=discord.ButtonStyle.link, url='https://top.gg/bot//vote')
            view = LayoutView(timeout=None)
            container = build_container(
                TextDisplay("**Inactive Timeout**"),
                Separator(visible=True),
                TextDisplay("Bot has been disconnected after being alone in the voice channel for more than 2 minutes."),
                Separator(visible=True),
                ActionRow(support, vote),
                Separator(visible=True),
                TextDisplay(f"*Thanks for choosing {BRAND_NAME}!*"),
            )
            view.add_item(container)
            if getattr(player, "ctx", None):
                await player.ctx.channel.send(view=view)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            print(f"[Music] Inactivity disconnect failed in guild {guild_id}: {error}")
        finally:
            task = self._inactivity_tasks.get(guild_id)
            if task is asyncio.current_task():
                self._inactivity_tasks.pop(guild_id, None)

    async def refresh_ai_suggestions(self, guild_id: int, track):
        """Fetch smart algorithmic recommendations for current track."""
        try:
            author = getattr(track, 'author', '') or ''
            title = getattr(track, 'title', '') or ''
            query = f"{author} songs" if author else f"{title} mix"
            tracks = await wavelink.Playable.search(query)
            if tracks:
                filtered = [t for t in tracks if getattr(t, 'title', '').lower() != title.lower()][:5]
                self.ai_suggestions[guild_id] = filtered
        except Exception:
            pass

    async def connect_nodes(self) -> None:
        host = os.getenv("LAVALINK_HOST", "lava-v4.ajieblogs.eu.org")
        password = os.getenv("LAVALINK_PASSWORD", "https://dsc.gg/ajidevserver")
        secure = os.getenv("LAVALINK_SECURE", "true").strip().lower() == "true"
        port = os.getenv("LAVALINK_PORT", "").strip()

        if secure:
            uri = f"https://{host}"
        else:
            uri = f"http://{host}:{port}" if port else f"http://{host}"

        nodes = [wavelink.Node(uri=uri, password=password)]
        await wavelink.Pool.connect(nodes=nodes, client=self.client, cache_capacity=None)
        asyncio.create_task(self.restore_music_sessions())


    async def display_player_embed(self, player, track, ctx, autoplay=False):
        guild_id = player.guild.id if player and player.guild else 0
        if guild_id and track:
            asyncio.create_task(self.refresh_ai_suggestions(guild_id, track))

        channel = getattr(ctx, "channel", None) or getattr(player, "channel", None)
        if not channel:
            return

        try:
            title = getattr(track, 'title', 'Unknown Track')
            artist = getattr(track, 'author', 'Unknown Artist')
            duration_sec = int(getattr(track, 'length', 0) // 1000)
            elapsed_sec = int(getattr(player, 'position', 0) // 1000)
            thumb_url = getattr(track, 'artwork', None)

            uri = getattr(track, 'uri', '') or ''
            if "spotify" in uri:
                platform = "spotify"
            elif "soundcloud" in uri:
                platform = "soundcloud"
            elif "jiosaavn" in uri:
                platform = "jiosaavn"
            elif "apple" in uri:
                platform = "apple"
            elif "music.youtube" in uri:
                platform = "youtubemusic"
            else:
                platform = "youtube"

            card_file = await MusicCardGenerator.create_card_file(
                title=title,
                artist=artist,
                elapsed_sec=elapsed_sec,
                duration_sec=duration_sec,
                thumbnail_url=thumb_url,
                platform=platform
            )
            is_autoplay = getattr(player, "smart_autoplay", True) or autoplay
            view = MusicControlView(player, ctx, track=track, autoplay=is_autoplay, has_card=True)
            await channel.send(file=card_file, view=view)
        except Exception as e:
            print(f"[Music UI] Card file error: {e}")
            is_autoplay = getattr(player, "smart_autoplay", True) or autoplay
            view = MusicControlView(player, ctx, track=track, autoplay=is_autoplay, has_card=False)
            await channel.send(view=view)


    async def on_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        guild_id = player.guild.id
        session = self.get_session(guild_id)

        track_dur = (payload.track.length / 1000.0) if payload.track and payload.track.length else 0.0
        if payload.reason == "finished" and track_dur > 0:
            await self.telemetry.log_event(
                event_type=MusicTelemetryEvent.PLAY_COMPLETED,
                guild_id=guild_id,
                track_id=getattr(payload.track, "identifier", ""),
                title=getattr(payload.track, "title", ""),
                artist=getattr(payload.track, "author", ""),
                track_duration=track_dur,
                played_seconds=track_dur,
            )
        if not player.queue:
            if player.queue.mode == wavelink.QueueMode.loop:
                await player.play(payload.track)
            elif getattr(player, "smart_autoplay", True):
                next_track = await self.fetch_smart_autoplay_track(player, payload.track)
                if next_track:
                    await player.play(next_track)
                    await self.display_player_embed(player, next_track, player.ctx, autoplay=True)
                elif self.is_247_enabled(player.guild.id):
                    await player.ctx.send(view=CV2("Queue ended. 24/7 mode is keeping me in the voice channel."))
                else:
                    await player.disconnect()
                    support = Button(label='Support', style=discord.ButtonStyle.link, url=serverLink)
                    vote = Button(label='Vote', style=discord.ButtonStyle.link, url='https://top.gg/bot//vote')
                    view = LayoutView(timeout=None)
                    container = build_container(
                        TextDisplay("**Queue Ended**"),
                        Separator(visible=True),
                        TextDisplay("All tracks have been played, leaving the voice channel."),
                        Separator(visible=True),
                        ActionRow(support, vote),
                    )
                    view.add_item(container)
                    await player.ctx.send(view=view)

                await asyncio.sleep(5)
                if player.current:
                    await self.display_player_embed(player, player.current, player.ctx, autoplay=True)
                else:
                    await player.ctx.send(view=CV2("No suitable track found for autoplay."))
            elif self.is_247_enabled(player.guild.id):
                await player.ctx.send(view=CV2("Queue ended. 24/7 mode is keeping me in the voice channel."))
            else:
                await player.disconnect()
                support = Button(label='Support', style=discord.ButtonStyle.link, url=serverLink)
                vote = Button(label='Vote', style=discord.ButtonStyle.link, url='https://top.gg/bot//vote')
                view = LayoutView(timeout=None)
                container = build_container(
                    TextDisplay("**Queue Ended**"),
                    Separator(visible=True),
                    TextDisplay("All tracks have been played, leaving the voice channel."),
                    Separator(visible=True),
                    ActionRow(support, vote),
                )
                view.add_item(container)
                await player.ctx.send(view=view)
        else:
            next_track = await player.queue.get_wait()
            await player.play(next_track)
            await self.display_player_embed(player, next_track, player.ctx)



    async def play_source(self, ctx, query):
        if not ctx.author.voice:
            await ctx.send(view=CV2(f"{WARNING} you need to be in a voice channel to use this command."))
            return

        vc = ctx.voice_client
        if vc is None:
            vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            vc.autoplay = wavelink.AutoPlayMode.disabled
            vc.smart_autoplay = True
        vc.ctx = ctx
        
        
        if vc.playing:
            if ctx.voice_client and ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.send(view=CV2(f"You must be connected to {ctx.voice_client.channel.mention} to play."))
                return
        if re.match(SPOTIFY_TRACK_REGEX, query):
            await self.handle_spotify_link(ctx, vc, query, "track")
            return
        elif re.match(SPOTIFY_PLAYLIST_REGEX, query):
            await self.handle_spotify_link(ctx, vc, query, "playlist")
            return
        elif re.match(SPOTIFY_ALBUM_REGEX, query):
            await self.handle_spotify_link(ctx, vc, query, "album")
            return
            
        tracks = await wavelink.Playable.search(query)
        if not tracks:
            await ctx.send(view=CV2("No results found."))
            return

        if isinstance(tracks, wavelink.Playlist):
            await vc.queue.put_wait(tracks.tracks)
            await ctx.send(view=CV2(f"{ZPLUS} Added playlist [{tracks.name}]({serverLink}) with **{len(tracks.tracks)} songs** to the queue."))
            if not vc.playing:
                track = await vc.queue.get_wait()
                await vc.play(track)
                await self.display_player_embed(vc, track, ctx)
        else:
            track = tracks[0]
            if len(tracks) > 1:
                candidates = []
                for t in tracks:
                    candidates.append({
                        "title": t.title,
                        "uploader": t.author,
                        "artist": t.author,
                        "duration": (t.length / 1000.0) if hasattr(t, "length") and t.length else 0,
                        "url": getattr(t, "uri", ""),
                        "id": getattr(t, "identifier", ""),
                        "source": getattr(t, "source", "youtube"),
                        "playable": t,
                    })
                ranked = self.search_ranker.rank_candidates(query, candidates)
                if ranked:
                    top_candidate = ranked[0][1]
                    track = top_candidate.get("playable", track)

            session = self.get_session(ctx.guild.id)
            session.set_hard_constraints_from_query(query)
            track_dict = {
                "title": track.title,
                "uploader": track.author,
                "artist": track.author,
                "duration": (track.length / 1000.0) if hasattr(track, "length") and track.length else 0,
                "url": getattr(track, "uri", ""),
                "id": getattr(track, "identifier", ""),
            }
            session.record_played_track(track_dict, is_manual=True)
            self.client.loop.create_task(self.precompute_ai_suggestions(ctx.guild.id, track_dict))
            self.client.loop.create_task(self.telemetry.log_event(
                event_type=MusicTelemetryEvent.PLAY_STARTED,
                guild_id=ctx.guild.id,
                user_id=ctx.author.id,
                track_id=getattr(track, "identifier", ""),
                title=getattr(track, "title", ""),
                artist=getattr(track, "author", ""),
                track_duration=track_dict["duration"],
            ))

            await vc.queue.put_wait(track)
            await ctx.send(view=CV2(f"{ZPLUS}   Added [{track.title}]({serverLink}) to the queue."))
            if not vc.playing:
                await vc.play(await vc.queue.get_wait())
                await self.display_player_embed(vc, track, ctx)
            self.client.loop.create_task(self.check_inactivity(ctx.guild.id))
           # await interaction.response.defer()


    
    async def handle_spotify_link(self, ctx, vc, link, type_):
        try:
            if type_ == "track":
                track_id = re.search(SPOTIFY_TRACK_REGEX, link).group(1)
                track_info = await spotify_api.get_track(track_id)

                
                title = track_info['name']
                author = ', '.join(artist['name'] for artist in track_info['artists'])

                
                search_query = f"{title} by {author}"
                search_results = await wavelink.Playable.search(search_query, source=wavelink.enums.TrackSource.YouTube)

                if not search_results:
                    await ctx.send("Can't play this track from Spotify, please try with another track.")
                    return

                track = search_results[0]
                if len(search_results) > 1:
                    candidates = []
                    for t in search_results:
                        candidates.append({
                            "title": t.title,
                            "uploader": t.author,
                            "artist": t.author,
                            "duration": (t.length / 1000.0) if hasattr(t, "length") and t.length else 0,
                            "url": getattr(t, "uri", ""),
                            "id": getattr(t, "identifier", ""),
                            "source": getattr(t, "source", "youtube"),
                            "playable": t,
                        })
                    ranked = self.search_ranker.rank_candidates(search_query, candidates, target_artist=author)
                    if ranked:
                        top_candidate = ranked[0][1]
                        track = top_candidate.get("playable", track)

                session = self.get_session(ctx.guild.id)
                session.set_hard_constraints_from_query(search_query)
                track_dict = {
                    "title": track.title,
                    "uploader": track.author,
                    "artist": track.author,
                    "duration": (track.length / 1000.0) if hasattr(track, "length") and track.length else 0,
                    "url": getattr(track, "uri", ""),
                    "id": getattr(track, "identifier", ""),
                }
                session.record_played_track(track_dict, is_manual=True)
                self.client.loop.create_task(self.precompute_ai_suggestions(ctx.guild.id, track_dict))
                self.client.loop.create_task(self.telemetry.log_event(
                    event_type=MusicTelemetryEvent.PLAY_STARTED,
                    guild_id=ctx.guild.id,
                    user_id=ctx.author.id,
                    track_id=getattr(track, "identifier", ""),
                    title=getattr(track, "title", ""),
                    artist=getattr(track, "author", ""),
                    track_duration=track_dict["duration"],
                ))

                await vc.queue.put_wait(track)
                await ctx.send(view=CV2(f"{ZPLUS}  Added [{track.title}]({serverLink}) to the queue."))
                if not vc.playing:
                    await vc.play(track)
                    await self.display_player_embed(vc, track, ctx)

                #await self.display_player_embed(vc, track, ctx)
                
            elif type_ == "playlist":
                lmao = await ctx.send("⏳ Processing to add tracks from the playlist, this may take a while...")
                
                playlist_id = re.search(SPOTIFY_PLAYLIST_REGEX, link).group(1)
                playlist_info = await spotify_api.get(f"playlists/{playlist_id}")
                tracks = playlist_info.get("tracks", {}).get("items", [])
                playlist_length = len(tracks)

                if not tracks:
                    await ctx.send("No tracks found in the playlist.")
                    return

                c = 0
                for track in tracks:
                    title = track['track']['name']
                    author = ', '.join(artist['name'] for artist in track['track']['artists'])
                    search_query = f"{title} {author}"

                    track_results = await wavelink.Playable.search(search_query, source=wavelink.enums.TrackSource.YouTube)
                    if track_results:
                        await vc.queue.put_wait(track_results[0])
                        c += 1
                        await ctx.message.add_reaction("✅")

                await ctx.send(view=CV2(f"{ZPLUS} Added **{c}** of **{playlist_length}** tracks from **playlist** **[{playlist_info['name']}]({serverLink})** to the queue."))
                await lmao.delete()
                
                if not vc.playing:
                    next_track = await vc.queue.get_wait()
                    await vc.play(next_track)
                    await self.display_player_embed(vc, next_track, ctx)


            elif type_ == "album":
                await ctx.message.add_reaction("⌛")
                album_id = re.search(SPOTIFY_ALBUM_REGEX, link).group(1)
                album_info = await spotify_api.get(f"albums/{album_id}")
                tracks = album_info.get("tracks", {}).get("items", [])

                if not tracks:
                    await ctx.send("No tracks found in the album.")
                    return

                for track in tracks:
                    title = track['name']
                    author = ', '.join(artist['name'] for artist in track['artists'])
                    search_query = f"{title} {author}"

                    track_results = await wavelink.Playable.search(search_query, source=wavelink.enums.TrackSource.YouTube)
                    if track_results:
                        await vc.queue.put_wait(track_results[0])

                await ctx.send(view=CV2(f"{ZPLUS} Added all tracks from album **[{album_info['name']}]({serverLink})** to the queue."))
                if not vc.playing:
                    next_track = await vc.queue.get_wait()
                    await vc.play(next_track)
                    await self.display_player_embed(vc, next_track, ctx)

                
        except Exception as e:
            await ctx.send(f"An error occurred while processing the Spotify link: {e}")



    def create_progress_bar(self, completed, total, length=10):
        filled_length = int(length * (completed / total))
        bar = '█' * filled_length + '░' * (length - filled_length)
        return bar

    @commands.command(name="play", aliases=['p', '-p'], usage="play <query>", help="Plays a song or playlist.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def play(self, ctx: commands.Context, *, query: str):
        
        await self.play_source(ctx, query)


    @commands.command(name="search", usage="search <query>", help="Searches music from multiple platforms.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def search2(self, ctx: commands.Context, *, query: str):
        if not ctx.author.voice:
            await ctx.send(view=CV2(f"{WARNING} You need to be in a voice channel to use this command."))
            return

        await ctx.send(view=PlatformSelectView(ctx, query))


    @commands.command(name="nowplaying", aliases=["nop"], usage="nowplaying", help="Shows the info about current playing song.")
    async def nowplaying(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc or not vc.playing:
            await ctx.send(view=CV2("No song is currently playing."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2("You need to be in the same voice channel as me to use this command."))
            return

        track = vc.current
        try:
            title = getattr(track, 'title', 'Unknown Track')
            artist = getattr(track, 'author', 'Unknown Artist')
            duration_sec = int(getattr(track, 'length', 0) // 1000)
            elapsed_sec = int(getattr(vc, 'position', 0) // 1000)
            thumb_url = getattr(track, 'artwork', None)

            uri = getattr(track, 'uri', '') or ''
            if "spotify" in uri:
                platform = "spotify"
            elif "soundcloud" in uri:
                platform = "soundcloud"
            elif "jiosaavn" in uri:
                platform = "jiosaavn"
            elif "apple" in uri:
                platform = "apple"
            elif "music.youtube" in uri:
                platform = "youtubemusic"
            else:
                platform = "youtube"

            card_file = await MusicCardGenerator.create_card_file(
                title=title,
                artist=artist,
                elapsed_sec=elapsed_sec,
                duration_sec=duration_sec,
                thumbnail_url=thumb_url,
                platform=platform
            )
            is_autoplay = getattr(vc, "smart_autoplay", True)
            view = MusicControlView(vc, ctx, track=track, autoplay=is_autoplay, has_card=True)
            await ctx.send(file=card_file, view=view)
        except Exception as e:
            print(f"[Music] nowplaying card error: {e}")
            is_autoplay = getattr(vc, "smart_autoplay", True)
            view = MusicControlView(vc, ctx, track=track, autoplay=is_autoplay, has_card=False)
            await ctx.send(view=view)

    @commands.command(name="autoplay", usage="autoplay", help="Toggles autoplay mode.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def autoplay(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc or not vc.playing:
            await ctx.send(view=CV2(f"{WARNING} No song is currently playing."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2(f"{WARNING} You need to be in the same voice channel as me to use this command."))
            return

        if vc:
            current_val = getattr(vc, "smart_autoplay", True)
            vc.smart_autoplay = not current_val
            vc.autoplay = wavelink.AutoPlayMode.disabled
            status = "enabled" if vc.smart_autoplay else "disabled"
            await ctx.send(view=CV2(f"{TICK} Smart ML Autoplay **{status}** by {ctx.author.mention}."))

    @commands.command(name="loop", usage="loop", help="Toggles loop mode.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def loop(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc or not vc.playing:
            await ctx.send(view=CV2(f"{WARNING} No song is currently playing."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2(f"{WARNING} You need to be in the same voice channel as me to use this command."))
            return

        if vc:
            vc.queue.mode = wavelink.QueueMode.loop if vc.queue.mode != wavelink.QueueMode.loop else wavelink.QueueMode.normal
            await ctx.send(view=CV2(f"{TICK} Loop {'enabled' if vc.queue.mode == wavelink.QueueMode.loop else 'disabled'} by {ctx.author.mention}."))
        else:
            await ctx.send(view=CV2("I'm not connected to a voice channel."))


    @commands.command(name="pause", usage="pause", help="Pauses the current song.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pause(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc or not vc.playing:
            await ctx.send(view=CV2(f"{WARNING} No song is currently playing."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2(f"{WARNING} You need to be in the same voice channel as me to use this command."))
            return

        if vc and vc.playing and not vc.paused:
            await vc.pause(True)
            await vc.channel.edit(status=f"{ZMUSICPAUSE} Paused: {vc.current.title}")
            await ctx.send(view=CV2(f"Paused by {ctx.author.mention}."))
        else:
            await ctx.send(view=CV2(f"{WARNING}   Nothing is playing or already paused."))

    @commands.command(name="resume", usage="resume", help="Resumes the paused song.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def resume(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc or not vc.playing:
            await ctx.send(view=CV2(f"{WARNING} No song is currently playing."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2(f"{ICONS_WARNING_ALT1} You need to be in the same voice channel as me to use this command."))
            return

        if vc and vc.paused:
            await vc.pause(False)
            await vc.channel.edit(status=f"{MUSIC_ALT1} Playing: {vc.current.title}")
            await ctx.send(view=CV2(f"Resumed by {ctx.author.mention}."))
        else:
            await ctx.send(view=CV2("Player is not paused."))

    @commands.command(name="skip", usage="skip", help="Skips the current song.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def skip(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc or not vc.playing:
            await ctx.send(view=CV2("No song is currently playing."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2(f"{WARNING} You need to be in the same voice channel as me to use this command."))
            return

        if vc.current:
            session = self.get_session(ctx.guild.id)
            session.record_skip(vc.current.title)
            self.client.loop.create_task(self.telemetry.log_event(
                event_type=MusicTelemetryEvent.SKIP,
                guild_id=ctx.guild.id,
                user_id=ctx.author.id,
                track_id=getattr(vc.current, "identifier", ""),
                title=getattr(vc.current, "title", ""),
                artist=getattr(vc.current, "author", ""),
                track_duration=(vc.current.length / 1000.0) if getattr(vc.current, "length", None) else 0,
                played_seconds=(vc.position / 1000.0) if getattr(vc, "position", None) else 0,
            ))

        if getattr(vc, "smart_autoplay", True) or not vc.queue.is_empty:
            await vc.stop()
            return await ctx.send(view=CV2(f"Skipped by {ctx.author.mention}."))
        else:
            await ctx.send(view=CV2(f"{WARNING} No song is playing or in the queue to skip."))

    @commands.command(name="shuffle", usage="shuffle", help="Shuffles the queue.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def shuffle(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc or not vc.playing:
            await ctx.send(view=CV2(f"{WARNING}  No song is currently playing."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2(f"{WARNING} You need to be in the same voice channel as me to use this command."))
            return

        if vc and vc.queue:
            random.shuffle(vc.queue)
            await ctx.send(view=CV2(f"Queue shuffled by {ctx.author.mention}."))
        else:
            await ctx.send(view=CV2("Queue is empty."))

    @commands.command(name="stop", usage="stop", help="Stops the current song and clears the queue.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def stop(self, ctx: commands.Context):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        vc = ctx.voice_client
        if not vc or not vc.playing:
            await ctx.send(view=CV2(f"{WARNING} No song is currently playing."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2(f"{WARNING} You need to be in the same voice channel as me to use this command."))
            return

        if vc and player:
            self.remove_session(ctx.guild.id)
            await vc.channel.edit(status=None)
            vc.queue.clear()
            if self.is_247_enabled(ctx.guild.id):
                await vc.stop()
                await ctx.send(view=CV2(f"Stopped and cleared the queue. 24/7 mode keeps me connected by request from {ctx.author.mention}."))
            else:
                await vc.disconnect(force=True)
                await ctx.send(view=CV2(f"Stopped and queue cleared by {ctx.author.mention}."))
        else:
            await ctx.send(view=CV2("Nothing is playing to stop."))

    @commands.command(name="volume", aliases=["vol"], usage="volume <level>", help="Sets the volume of the player.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def volume(self, ctx: commands.Context, level: int):
        vc = ctx.voice_client

        if not vc:
            await ctx.send(view=CV2(f"{WARNING} I'm not connected to a voice channel."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2(f"{WARNING} You need to be in the same voice channel as me to use this command."))
            return

        if vc:
            if 1 <= level <= 150:
                await vc.set_volume(level)
                await ctx.send(view=CV2(f"{MUTE} Volume set to {level}% by {ctx.author.mention}."))
            else:
                await ctx.send(view=CV2(f"{WARNING} Volume must be between 1 and 150."))
        else:
            await ctx.send(view=CV2("Bot is not connected to a voice channel."))

    @commands.command(name="queue", usage="queue", help="Shows the current queue.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def queue(self, ctx: commands.Context):
        vc = ctx.voice_client

        if not vc or not vc.queue or vc.queue.is_empty:
            await ctx.send(view=CV2(f"{WARNING} The queue is currently empty."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2(f"{WARNING} you need to be in the same voice channel as me to use this command."))
            return


        entries = [f"{index + 1}. [{track.title} - {track.author}]({track.uri})" for index, track in enumerate(vc.queue)]
        paginator = Paginator(source=DescriptionEmbedPaginator(
            entries=entries,
            title="Current Queue",
            description="List of upcoming songs.",
            per_page=10,
            color=0xFF0000),
            ctx=ctx)
        await paginator.paginate()

    @commands.command(name="clearqueue", usage="clearqueue", help="Clears the queue.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def clearqueue(self, ctx: commands.Context):
        vc = ctx.voice_client

        if not vc or not vc.queue or vc.queue.is_empty:
            await ctx.send(view=CV2(f"{WARNING} No Queue to clear."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2(f"{WARNING} You need to be in the same voice channel as me to use this command."))
            return

        if vc and vc.queue:
            vc.queue.clear()
            await ctx.send(view=CV2("Queue has been cleared."))
        else:
            await ctx.send(view=CV2("No queue to clear."))

    @commands.command(name="replay", usage="replay", help="Replays the current song.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def replay(self, ctx: commands.Context):
        vc = ctx.voice_client

        if not vc or not vc.playing:
            await ctx.send(view=CV2(f"{WARNING} I'm not connected to any voice channel."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2(f"{WARNING} You need to be in the same voice channel as me to use this command."))
            return

        if vc and vc.playing:
            await vc.seek(0)
            await ctx.send(view=CV2("Replaying the current track."))
        else:
            await ctx.send(view=CV2("No track is currently playing."))

    @commands.command(name="join", aliases=["connect"], usage="join", help="Joins the voice channel.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def join(self, ctx: commands.Context):
        if ctx.author.voice:
            vc = ctx.voice_client
            if vc is None:
                vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
                vc.autoplay = wavelink.AutoPlayMode.disabled
                vc.smart_autoplay = True
            await ctx.send(view=CV2("Joined the voice channel."))
        else:
            await ctx.send(view=CV2("You need to join a voice channel first."))

    @commands.command(
        name="247",
        aliases=["24/7", "24-7", "alwayson"],
        usage="247 [on|off]",
        help="Keeps the bot connected to your voice channel while idle.",
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def mode_247(self, ctx: commands.Context, state: Optional[str] = None):
        state = state.lower() if state else "toggle"
        if state in {"on", "enable", "enabled", "true", "1"}:
            enable = True
        elif state in {"off", "disable", "disabled", "false", "0"}:
            enable = False
        elif state == "toggle":
            enable = not self.is_247_enabled(ctx.guild.id)
        else:
            await ctx.send(view=CV2("Use `247 on`, `247 off`, or `247` to toggle the mode."))
            return

        player = ctx.voice_client
        if enable:
            if not ctx.author.voice:
                await ctx.send(view=CV2("Join a voice channel before enabling 24/7 mode."))
                return

            voice_channel = ctx.author.voice.channel
            if player and player.channel != voice_channel:
                await ctx.send(view=CV2(f"Join {player.channel.mention} to change this server's 24/7 setting."))
                return

            if player is None:
                try:
                    player = await voice_channel.connect(cls=wavelink.Player)
                    player.autoplay = wavelink.AutoPlayMode.disabled
                    player.smart_autoplay = True
                except Exception as error:
                    print(f"[Music 24/7] Could not join {voice_channel.id}: {error}")
                    await ctx.send(view=CV2("I couldn't join your voice channel. Check my voice permissions and Lavalink connection."))
                    return

            player.ctx = ctx
            self.enable_247_mode(ctx.guild.id, voice_channel.id)
            self.cancel_inactivity_timer(ctx.guild.id)
            await ctx.send(view=CV2("24/7 mode enabled. I'll stay connected to this voice channel while idle."))
            return

        if not self.is_247_enabled(ctx.guild.id):
            await ctx.send(view=CV2("24/7 mode is already disabled."))
            return

        if player and (not ctx.author.voice or ctx.author.voice.channel != player.channel):
            await ctx.send(view=CV2(f"Join {player.channel.mention} to change this server's 24/7 setting."))
            return

        self.disable_247_mode(ctx.guild.id)
        if player and not player.playing:
            self.cancel_inactivity_timer(ctx.guild.id)
            self.remove_session(ctx.guild.id)
            await player.disconnect(force=True)
            await ctx.send(view=CV2("24/7 mode disabled. I left the idle voice channel."))
        else:
            await ctx.send(view=CV2("24/7 mode disabled. Normal idle disconnect behavior is restored."))

    @commands.hybrid_command(name="disconnect", aliases=["dc", "leave"], usage="disconnect", help="Disconnects the bot from the voice channel.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def disconnect(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc:
            await ctx.send(view=CV2(f"{ICONS_WARNING_ALT1}  I'm not connected to any voice channel."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2(f"{WARNING} You need to be in the same voice channel as me to use this command."))
            return

        if vc:
            mode_was_enabled = self.is_247_enabled(ctx.guild.id)
            if mode_was_enabled:
                self.disable_247_mode(ctx.guild.id)
            self.remove_session(ctx.guild.id)
            await vc.disconnect()
            message = "Disconnected from the voice channel."
            if mode_was_enabled:
                message += " 24/7 mode has been disabled."
            await ctx.send(view=CV2(message))
        else:
            await ctx.send(view=CV2("Bot is not connected to any voice channel."))

    @commands.command(name="seek", usage="seek <percentage>", help="Seeks to a specific percentage of the song.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def seek(self, ctx: commands.Context, percentage: int):
        if not 1 <= percentage <= 100:
            await ctx.send(view=CV2("Please provide a percentage between 1 and 100."))
            return

        vc = ctx.voice_client
        if not vc or not vc.playing:
            await ctx.send(view=CV2("No song is currently playing."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2("You need to be in the same voice channel as me to use this command."))
            return

        track = vc.current
        target_position = int(track.length * (percentage / 100))  
        await vc.seek(target_position)

        await ctx.send(view=CV2(f"Seeked to {percentage}% of the current track."))

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        print(f"{Fore.GREEN}[WAVELINK] Node {payload.node.identifier} is ready (resumed: {payload.resumed}).")
        if not self._restored:
            asyncio.create_task(self.restore_music_sessions())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if not self.client.user or member.id != self.client.user.id:
            return

        guild_id = member.guild.id
        if before.channel and not after.channel:
            if self.is_247_enabled(guild_id):
                asyncio.create_task(self.reconnect_247(guild_id))
            else:
                self.remove_session(guild_id)
        elif after.channel and before.channel != after.channel and self.is_247_enabled(guild_id):
            self.enable_247_mode(guild_id, after.channel.id)

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player = payload.player
        guild_id = player.guild.id
        session = self.get_session(guild_id)

        track_dur = (payload.track.length / 1000.0) if payload.track and payload.track.length else 0.0
        if payload.reason == "finished" and track_dur > 0:
            await self.telemetry.log_event(
                event_type=MusicTelemetryEvent.PLAY_COMPLETED,
                guild_id=guild_id,
                track_id=getattr(payload.track, "identifier", ""),
                title=getattr(payload.track, "title", ""),
                artist=getattr(payload.track, "author", ""),
                track_duration=track_dur,
                played_seconds=track_dur,
            )
        track = player.current
        guild_id = player.guild.id

        voice_channel = player.channel
        if voice_channel:
            await voice_channel.edit(status=f"{MUSIC_ALT1} Playing: {track.title}")  # type: ignore

        if guild_id not in track_histories:
            track_histories[guild_id] = []

        if not track_histories[guild_id] or track_histories[guild_id][-1] != track:
            track_histories[guild_id].append(track)


            if len(track_histories[guild_id]) > 10:
                track_histories[guild_id].pop(0)

        self.update_session(player)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        guild_id = player.guild.id
        session = self.get_session(guild_id)

        track_dur = (payload.track.length / 1000.0) if payload.track and payload.track.length else 0.0
        if payload.reason == "finished" and track_dur > 0:
            await self.telemetry.log_event(
                event_type=MusicTelemetryEvent.PLAY_COMPLETED,
                guild_id=guild_id,
                track_id=getattr(payload.track, "identifier", ""),
                title=getattr(payload.track, "title", ""),
                artist=getattr(payload.track, "author", ""),
                track_duration=track_dur,
                played_seconds=track_dur,
            )
        voice_channel = player.channel

        if voice_channel:
            try:
                await voice_channel.edit(status=None)
            except Exception:
                pass

        if not player.queue and player.queue.mode != wavelink.QueueMode.loop and not getattr(player, "smart_autoplay", True):
            self.remove_session(player.guild.id)
        else:
            self.update_session(player)

        await self.on_track_end(payload)
