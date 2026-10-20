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
from discord.ui import Button, View, LayoutView, TextDisplay, Separator, Container, ActionRow
import wavelink
from wavelink.enums import TrackSource
from utils import Paginator, DescriptionEmbedPaginator
from core import Cog, zyuna, Context
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
from utils.config import *
import json
import atexit
from colorama import Fore, Style
from typing import cast, Optional, Union, List, Dict, Any

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "db"))
SESSIONS_FILE = os.path.join(DB_DIR, "music_active_sessions.json")

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
            vc = self.ctx.voice_client or await self.ctx.author.voice.channel.connect(cls=wavelink.Player)
            vc.ctx = self.ctx

            if not vc.playing:
                await vc.play(track)
                await interaction.response.send_message(f"Started playing `{track.title}`.")
                await self.ctx.cog.display_player_embed(vc, track, self.ctx)
            else:
                await vc.queue.put_wait(track)
                await interaction.response.send_message(f"Added `{track.title}` to the queue.")

        return callback


class MusicControlView(LayoutView):
    def __init__(self, player, ctx, track=None, autoplay=False):
        super().__init__(timeout=None)
        self.player = player
        self.ctx = ctx
        self._build_ui(track, autoplay)

    def _build_ui(self, track=None, autoplay=False):
        from discord.ui import Section, Thumbnail, TextDisplay

        items = []

        if track:
            sec = track.length // 1000
            duration = f"{sec // 60:02d}:{sec % 60:02d}"
            
            requester = self.ctx.author.display_name
            if autoplay: requester += " (Autoplay)"

            title_text = f"**Now Playing [{track.title}]({track.uri})**"
            items.append(TextDisplay(title_text))

            bullet_text = (
                f"• **Author:** `{track.author}`\n"
                f"• **Duration:** `{duration}`\n"
                f"• **Requester:** {requester}"
            )

            if getattr(track, 'artwork', None):
                accessory = Thumbnail(media=track.artwork)
                items.append(Section(TextDisplay(bullet_text), accessory=accessory))
            else:
                items.append(TextDisplay(bullet_text))

        # Row 1 buttons (Main 5 from screenshot with exact styles)
        btn_pause = Button(emoji=ICONS_PAUSE, label="Pause", style=discord.ButtonStyle.primary)
        btn_skip = Button(emoji=SKIP, label="Skip", style=discord.ButtonStyle.secondary)
        btn_stop = Button(emoji=MUSICSTOP_ICONS, label="Stop", style=discord.ButtonStyle.danger)
        btn_loop = Button(emoji=ICONLOAD, label="Loop", style=discord.ButtonStyle.secondary)
        btn_autoplay = Button(emoji=ZUNMUTE, label="Autoplay", style=discord.ButtonStyle.secondary)

        # Row 2 buttons (Remaining controls)
        btn_prev = Button(emoji=REWIND, style=discord.ButtonStyle.secondary)
        btn_shuffle = Button(emoji=SHUFFLE, style=discord.ButtonStyle.secondary)
        btn_rewind = Button(emoji=REWIND_ALT1, style=discord.ButtonStyle.secondary)
        btn_forward = Button(emoji=FORWARD, style=discord.ButtonStyle.secondary)
        btn_replay = Button(emoji=ICONS_MUSIC, style=discord.ButtonStyle.secondary)

        btn_pause.callback = self._cb_pause
        btn_skip.callback = self._cb_skip
        btn_stop.callback = self._cb_stop
        btn_loop.callback = self._cb_loop
        btn_autoplay.callback = self._cb_autoplay

        btn_prev.callback = self._cb_previous
        btn_shuffle.callback = self._cb_shuffle
        btn_rewind.callback = self._cb_rewind
        btn_forward.callback = self._cb_forward
        btn_replay.callback = self._cb_replay

        items.append(ActionRow(btn_pause, btn_skip, btn_stop, btn_loop, btn_autoplay))
        items.append(ActionRow(btn_prev, btn_shuffle, btn_rewind, btn_forward, btn_replay))

        container = build_container(*items)
        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not self.ctx.voice_client or not self.player.playing:
            await interaction.response.send_message("I'm not currently playing this anymore.", ephemeral=True)
            return False
        if interaction.user in self.ctx.voice_client.channel.members:
            return True
        await interaction.response.send_message("Only members in the same voice channel can control the player.", ephemeral=True)
        return False

    async def _cb_autoplay(self, interaction):
        self.player.autoplay = (
            wavelink.AutoPlayMode.enabled if self.player.autoplay != wavelink.AutoPlayMode.enabled else wavelink.AutoPlayMode.disabled
        )
        await interaction.response.send_message(f"Autoplay {'enabled' if self.player.autoplay == wavelink.AutoPlayMode.enabled else 'disabled'} by **{interaction.user.display_name}**.")

    async def _cb_previous(self, interaction):
        guild_id = interaction.guild.id
        if guild_id in track_histories and len(track_histories[guild_id]) > 1:
            track_histories[guild_id].pop()
            previous_track = track_histories[guild_id][-1]
            if self.player.playing:
                await self.player.stop()
            await self.ctx.voice_client.queue.put_wait(previous_track)
            await interaction.response.send_message(f"Playing previous track: `{previous_track.title}`.")
        else:
            await interaction.response.send_message("No previous track available.", ephemeral=True)

    async def _cb_pause(self, interaction):
        if self.player.paused:
            await self.player.pause(False)
            await self.player.channel.edit(status=f"{ICONS_PAUSE} Playing: {self.player.current.title}")
            await interaction.response.send_message(f"Resumed by **{interaction.user.display_name}**.")
        elif self.player.playing:
            await self.player.pause(True)
            await self.player.channel.edit(status=f"{ICONS_PAUSE} Paused: {self.player.current.title}")
            await interaction.response.send_message(f"Paused by **{interaction.user.display_name}**.")

    async def _cb_skip(self, interaction):
        if self.player.autoplay == wavelink.AutoPlayMode.enabled:
            await self.player.stop()
            return await interaction.response.send_message(f"Skipped by **{interaction.user.display_name}**.")
        if self.player and self.player.playing and not self.player.queue.is_empty:
            await self.player.stop()
            await interaction.response.send_message(f"Skipped by **{interaction.user.display_name}**.")
        else:
            await interaction.response.send_message("No song in queue to skip.", ephemeral=True)

    async def _cb_loop(self, interaction):
        self.player.queue.mode = wavelink.QueueMode.loop if self.player.queue.mode != wavelink.QueueMode.loop else wavelink.QueueMode.normal
        await interaction.response.send_message(f"Loop {'enabled' if self.player.queue.mode == wavelink.QueueMode.loop else 'disabled'} by **{interaction.user.display_name}**.")

    async def _cb_shuffle(self, interaction):
        if self.player.queue:
            random.shuffle(self.player.queue)
            await interaction.response.send_message(f"Queue shuffled by **{interaction.user.display_name}**.")
        else:
            await interaction.response.send_message("Queue is empty.", ephemeral=True)

    async def _cb_rewind(self, interaction):
        if self.player.playing:
            new_position = max(self.player.position - 10000, 0)
            await self.player.seek(new_position)
            await interaction.response.send_message("Rewinded 10 seconds.", ephemeral=True)
        else:
            await interaction.response.send_message("No track is currently playing.", ephemeral=True)

    async def _cb_stop(self, interaction):
        if self.player:
            voice_channel = self.player.channel
            if voice_channel:
                try:
                    await voice_channel.edit(status=None)
                except Exception:
                    pass
            guild_id = self.player.guild.id
            if hasattr(self.player, "queue"):
                self.player.queue.clear()
            await self.player.disconnect()
            music_cog = self.player.client.get_cog("Music") if hasattr(self.player, "client") else None
            if music_cog and hasattr(music_cog, "remove_session"):
                music_cog.remove_session(guild_id)
            await interaction.response.send_message(f"Stopped and disconnected by **{interaction.user.display_name}**.")
        else:
            await interaction.response.send_message("Not connected.", ephemeral=True)

    async def _cb_forward(self, interaction):
        if self.player.playing:
            new_position = min(self.player.position + 10000, self.player.current.length)
            await self.player.seek(new_position)
            await interaction.response.send_message("Forwarded 10 seconds.", ephemeral=True)
        else:
            await interaction.response.send_message("No track is currently playing.", ephemeral=True)

    async def _cb_replay(self, interaction):
        if self.player.playing:
            await self.player.seek(0)
            await interaction.response.send_message("Replaying the current track.", ephemeral=True)
        else:
            await interaction.response.send_message("No track is currently playing.", ephemeral=True)


class Music(commands.Cog):
    def __init__(self, client: zyuna):
        global _music_cog_instance
        self.client = client
        _music_cog_instance = self
        
        self.inactivity_timeout = 120 
        self.player_inactivity = {}
        self._restoring = False
        self._restored = False
        self._recovery_lock = asyncio.Lock()
        
        self.periodic_save_sessions.start()
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.connect_nodes())
            loop.create_task(self.monitor_inactivity())
        except RuntimeError:
            pass

    async def cog_unload(self):
        self.save_all_sessions_sync()
        if hasattr(self, "periodic_save_sessions"):
            self.periodic_save_sessions.cancel()

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

        autoplay = player.autoplay == wavelink.AutoPlayMode.enabled
        
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
            if not sessions:
                return

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

                    if data.get("autoplay"):
                        vc.autoplay = wavelink.AutoPlayMode.enabled
                    else:
                        vc.autoplay = wavelink.AutoPlayMode.disabled

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

        finally:
            self._restoring = False  

    async def monitor_inactivity(self):
        while True:
            for guild in self.client.guilds:
                await self.check_inactivity(guild.id) 
            await asyncio.sleep(60) 

    async def check_inactivity(self, guild_id):
        guild = self.client.get_guild(guild_id)
        if not guild:
            return

        player = None
        for vc in self.client.voice_clients:
            if vc.guild.id == guild.id:
                player = vc
                break

        if player and player.playing and len(player.channel.members) == 1:
            await self.inactivity_timer(guild)

    async def inactivity_timer(self, guild):
        await asyncio.sleep(self.inactivity_timeout)
        if len(guild.voice_channels[0].members) == 1:
            player = None
            for vc in self.client.voice_clients:
                if vc.guild.id == guild.id:
                    player = vc
                    break
            if player:
                await player.disconnect(force=True)
                try:
                    support = Button(label='Support', style=discord.ButtonStyle.link, url=serverLink)
                    vote = Button(label='Vote', style=discord.ButtonStyle.link, url='https://top.gg/bot//vote')
                    view = LayoutView(timeout=None)
                    container = build_container(
                        TextDisplay("**Inactive Timeout**"),
                        Separator(visible=True),
                        TextDisplay("Bot has been disconnected due to inactivity (being idle in Voice Channel) for more than 2 minutes."),
                        Separator(visible=True),
                        ActionRow(support, vote),
                        Separator(visible=True),
                        TextDisplay(f"*Thanks for choosing {BRAND_NAME}!*"),
                    )
                    view.add_item(container)
                    await player.ctx.channel.send(view=view)
                except:
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
        await ctx.send(view=MusicControlView(player, ctx, track, autoplay))


    async def on_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        if not player.queue:
            if player.queue.mode == wavelink.QueueMode.loop:
                await player.play(payload.track)
            elif player.autoplay == wavelink.AutoPlayMode.enabled:
                await asyncio.sleep(5)
                if player.current:
                    await self.display_player_embed(player, player.current, player.ctx, autoplay=True)
                else:
                    await player.ctx.send(view=CV2("No suitable track found for autoplay."))
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

        vc = ctx.voice_client or await ctx.author.voice.channel.connect(cls=wavelink.Player)
        vc.ctx = ctx
        
        
        if vc.playing:
            if ctx.voice_client and ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.send(view=CV2(f"You must be connected to {ctx.voice_client.channel.mention} to play."))
                return
        vc.autoplay = wavelink.AutoPlayMode.disabled

        """if re.match(SPOTIFY_TRACK_REGEX, query):
            await self.handle_spotify_link(ctx, vc, query, "track")
        elif re.match(SPOTIFY_PLAYLIST_REGEX, query):
            await self.handle_spotify_link(ctx, vc, query, "playlist")
        elif re.match(SPOTIFY_ALBUM_REGEX, query):
            await self.handle_spotify_link(ctx, vc, query, "album")
        
            return"""
            
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

    @commands.command(name="play", aliases=['p'], usage="play <query>", help="Plays a song or playlist.")
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
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def nowplaying(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc or not vc.playing:
            await ctx.send(view=CV2("No song is currently playing."))
            return

        if not ctx.author.voice or ctx.author.voice.channel.id != vc.channel.id:
            await ctx.send(view=CV2("You need to be in the same voice channel as me to use this command."))
            return

        track = vc.current
        position = vc.position / 1000  
        length = track.length / 1000  

        progress_bar = self.create_progress_bar(position, length, length=10)
        position_str = f"{int(position // 60)}:{int(position % 60):02}"
        length_str = f"{int(length // 60)}:{int(length % 60):02}"


        queue_length = len(vc.queue) if vc.queue else 0


        if "spotify" in track.uri:
            source_name = "Spotify"
        elif "youtube" in track.uri:
            source_name = "YouTube"
        elif "soundcloud" in track.uri:
            source_name = "SoundCloud"
        elif "jiosaavn" in track.uri:
            source_name = "JioSaavn"
        else:
            source_name = "Unknown Source"


        view = CV2Embed(
            title="🎶 Now Playing",
            color=0x1DB954 if source_name == "Spotify" else 0xFF0000
        )
        view.add_field(name="Track", value=f"[{track.title}]({track.uri})", inline=False)
        view.add_field(name="Song By", value=track.author, inline=False)
        view.add_field(name="Progress", value=f"{position_str} [{progress_bar}] {length_str}", inline=False)
        view.add_field(name="Duration", value=length_str, inline=False)
        view.add_field(name="Queue Length", value=str(queue_length), inline=False)
        view.add_field(name="Source", value=f"{source_name} - [Link]({track.uri})", inline=False)
        view.set_thumbnail(url=track.artwork if track.artwork else "")
        view.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

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
            vc.autoplay = (
                wavelink.AutoPlayMode.enabled if vc.autoplay != wavelink.AutoPlayMode.enabled else wavelink.AutoPlayMode.disabled
            )
            await ctx.send(view=CV2(f"{TICK} Autoplay {'enabled' if vc.autoplay == wavelink.AutoPlayMode.enabled else 'disabled'} by {ctx.author.mention}."))

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

        if vc.autoplay == wavelink.AutoPlayMode.enabled:
            await vc.stop()
            return await ctx.send(view=CV2(f"Skipped by {ctx.author.mention}."))


        if vc and vc.playing and not vc.queue.is_empty:
            await vc.stop()
            await ctx.send(view=CV2(f"Skipped by {ctx.author.mention}."))
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
            await ctx.author.voice.channel.connect(cls=wavelink.Player)
            await ctx.send(view=CV2("Joined the voice channel."))
        else:
            await ctx.send(view=CV2("You need to join a voice channel first."))

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
            self.remove_session(ctx.guild.id)
            await vc.disconnect()
            await ctx.send(view=CV2("Disconnected from the voice channel."))
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
        if member.id == self.client.user.id and before.channel and not after.channel:
            self.remove_session(member.guild.id)

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player = payload.player
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
        voice_channel = player.channel

        if voice_channel:
            try:
                await voice_channel.edit(status=None)
            except Exception:
                pass

        if not player.queue and player.queue.mode != wavelink.QueueMode.loop and player.autoplay != wavelink.AutoPlayMode.enabled:
            self.remove_session(player.guild.id)
        else:
            self.update_session(player)

        await self.on_track_end(payload)
