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

from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Optional, Union

# --- Bot Schemas ---

class BotInfo(BaseModel):
    name: str
    id: Optional[str]
    guilds: int
    users: int
    commands: int
    latency: str

class BotStatus(BaseModel):
    user: str
    id: Optional[str]
    latency: float
    guild_count: int
    user_count: int
    shards: Optional[int]

# --- Guild Schemas ---

class GuildSummary(BaseModel):
    id: str
    name: str
    icon_url: Optional[str]
    owner_id: str
    member_count: int

class GuildDetails(BaseModel):
    id: str
    name: str
    icon: Optional[str]
    owner_id: str
    member_count: int
    role_count: int
    channel_count: int

class DiscordChannel(BaseModel):
    id: str
    name: str
    type: str

class DiscordRole(BaseModel):
    id: str
    name: str
    color: int
    position: int

# --- Prefix Configuration ---

class PrefixConfig(BaseModel):
    guild_id: Union[int, str]
    prefix: str

class PrefixUpdate(BaseModel):
    prefix: str

# --- Studio Audio Schemas ---

class MusicTrack(BaseModel):
    title: str
    author: str
    uri: str
    duration: float
    artwork: Optional[str] = None
    requester: Optional[str] = None

class MusicPlayerState(BaseModel):
    guild_id: str
    is_connected: bool
    is_playing: bool
    is_paused: bool
    volume: int
    current_track: Optional[MusicTrack] = None
    position: float = 0.0
    loop_mode: str = "off"
    filter_preset: str = "Flat"
    queue: List[MusicTrack] = []
    voice_channel: Optional[str] = None

class MusicControlAction(BaseModel):
    action: str  # pause, resume, skip, stop, set_volume, set_filter, set_loop
    value: Optional[Union[str, int, float]] = None

# --- Chat Safety & Moderation Schemas ---

class SafetyConfig(BaseModel):
    guild_id: str
    blacklisted_words: List[str] = []
    bypass_roles: List[str] = []
    bypass_users: List[str] = []

class SafetyUpdate(BaseModel):
    add_word: Optional[str] = None
    remove_word: Optional[str] = None
    add_bypass_role: Optional[str] = None
    remove_bypass_role: Optional[str] = None

# --- Social Alerts Schemas ---

class SocialAlertItem(BaseModel):
    id: int
    type: str  # youtube, twitch
    role_id: str
    channel_id: str

class AlertsConfig(BaseModel):
    guild_id: str
    alerts: List[SocialAlertItem] = []

class AlertsUpdate(BaseModel):
    type: str
    channel_id: str
    role_id: str

# --- Admin Schemas ---

class AdminNodeStatus(BaseModel):
    name: str
    status: str
    load: str
    icon: str

class AdminStats(BaseModel):
    total_users: str
    active_servers: str
    api_latency: str
    db_size: str
    nodes: List[AdminNodeStatus]

class AdminConfig(BaseModel):
    maintenance_mode: bool
    global_notification: Optional[str] = None

class AdminConfigUpdate(BaseModel):
    maintenance_mode: Optional[bool] = None
    global_notification: Optional[str] = None
