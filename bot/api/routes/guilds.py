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

from fastapi import APIRouter, Depends, HTTPException, Request
from api.dependencies import get_bot, limiter
from api.db_manager import db_manager
from api.schemas import (
    GuildSummary, GuildDetails, DiscordChannel, DiscordRole,
    PrefixConfig, PrefixUpdate,
    MusicPlayerState, MusicTrack, MusicControlAction,
    SafetyConfig, SafetyUpdate,
    AlertsConfig, AlertsUpdate, SocialAlertItem
)
from typing import TYPE_CHECKING, List, Optional
import aiosqlite
import os

if TYPE_CHECKING:
    from core.zyuna import zyuna

router = APIRouter()

@router.get("/", response_model=List[GuildSummary], summary="List all guilds")
async def list_guilds(bot: "zyuna" = Depends(get_bot)):
    guilds_list = []
    for guild in bot.guilds:
        guilds_list.append(GuildSummary(
            id=str(guild.id),
            name=guild.name,
            icon_url=str(guild.icon.url) if guild.icon else None,
            owner_id=str(guild.owner_id),
            member_count=guild.member_count or 0
        ))
    return guilds_list

@router.get("/{guild_id}", response_model=GuildDetails, summary="Get guild details")
async def get_guild_details(guild_id: int, bot: "zyuna" = Depends(get_bot)):
    guild = bot.get_guild(guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")
        
    return GuildDetails(
        id=str(guild.id),
        name=guild.name,
        icon=str(guild.icon.url) if guild.icon else None,
        owner_id=str(guild.owner_id),
        member_count=guild.member_count or 0,
        role_count=len(guild.roles),
        channel_count=len(guild.channels)
    )

@router.get("/{guild_id}/channels", response_model=List[DiscordChannel], summary="Get guild channels")
async def get_guild_channels(guild_id: int, bot: "zyuna" = Depends(get_bot)):
    guild = bot.get_guild(guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    channels = []
    for c in guild.channels:
        channels.append(DiscordChannel(
            id=str(c.id),
            name=c.name,
            type=str(c.type)
        ))
    return channels

@router.get("/{guild_id}/roles", response_model=List[DiscordRole], summary="Get guild roles")
async def get_guild_roles(guild_id: int, bot: "zyuna" = Depends(get_bot)):
    guild = bot.get_guild(guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    roles = []
    for r in guild.roles:
        if r.is_default():
            continue
        roles.append(DiscordRole(
            id=str(r.id),
            name=r.name,
            color=r.color.value,
            position=r.position
        ))
    return sorted(roles, key=lambda x: x.position, reverse=True)

# --- Prefix ---

@router.get("/{guild_id}/prefix", response_model=PrefixConfig, summary="Get guild prefix")
async def get_guild_prefix(guild_id: int):
    db = await db_manager.get_connection('db/prefix.db')
    cursor = await db.execute("SELECT prefix FROM prefixes WHERE guild_id = ?", (guild_id,))
    row = await cursor.fetchone()
    prefix = row[0] if row else ">"
    return PrefixConfig(guild_id=guild_id, prefix=prefix)

@router.post("/{guild_id}/prefix", summary="Update guild prefix")
async def update_guild_prefix(guild_id: int, data: PrefixUpdate):
    if not data.prefix or len(data.prefix) > 10:
        raise HTTPException(status_code=400, detail="Invalid prefix. Must be 1-10 characters.")

    db = await db_manager.get_connection('db/prefix.db')
    await db.execute(
        "INSERT OR REPLACE INTO prefixes (guild_id, prefix) VALUES (?, ?)",
        (guild_id, data.prefix)
    )
    await db.commit()
    return {"status": "success", "new_prefix": data.prefix}

# --- Studio Audio Player State & Controls ---

@router.get("/{guild_id}/music", response_model=MusicPlayerState, summary="Get live audio player state")
async def get_music_state(guild_id: int, bot: "zyuna" = Depends(get_bot)):
    guild = bot.get_guild(guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")

    player = guild.voice_client
    if not player or not hasattr(player, "current"):
        return MusicPlayerState(
            guild_id=str(guild_id),
            is_connected=False,
            is_playing=False,
            is_paused=False,
            volume=100,
            current_track=None,
            position=0.0,
            loop_mode="off",
            filter_preset="Flat",
            queue=[],
            voice_channel=None
        )

    current_track = None
    if player.current:
        current_track = MusicTrack(
            title=getattr(player.current, "title", "Unknown Title"),
            author=getattr(player.current, "author", "Unknown Artist"),
            uri=getattr(player.current, "uri", ""),
            duration=float(getattr(player.current, "length", 0)) / 1000.0,
            artwork=getattr(player.current, "artwork", None),
            requester=str(getattr(player.current, "requester", "")) if hasattr(player.current, "requester") else None
        )

    queue_tracks = []
    if hasattr(player, "queue"):
        for t in list(player.queue)[:25]:
            queue_tracks.append(MusicTrack(
                title=getattr(t, "title", "Unknown Title"),
                author=getattr(t, "author", "Unknown Artist"),
                uri=getattr(t, "uri", ""),
                duration=float(getattr(t, "length", 0)) / 1000.0,
                artwork=getattr(t, "artwork", None)
            ))

    loop_mode = "off"
    if getattr(player, "loop_mode", None):
        loop_mode = str(player.loop_mode)
    elif getattr(player, "loop", False):
        loop_mode = "track"

    filter_preset = getattr(player, "current_filter", "Flat") or "Flat"

    return MusicPlayerState(
        guild_id=str(guild_id),
        is_connected=True,
        is_playing=bool(player.playing),
        is_paused=bool(player.paused),
        volume=int(getattr(player, "volume", 100)),
        current_track=current_track,
        position=float(getattr(player, "position", 0)) / 1000.0,
        loop_mode=loop_mode,
        filter_preset=filter_preset,
        queue=queue_tracks,
        voice_channel=str(player.channel.name) if getattr(player, "channel", None) else None
    )

@router.post("/{guild_id}/music/control", summary="Control studio audio playback")
async def control_music(guild_id: int, action: MusicControlAction, bot: "zyuna" = Depends(get_bot)):
    guild = bot.get_guild(guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")

    player = guild.voice_client
    if not player:
        raise HTTPException(status_code=400, detail="Bot is not connected to a voice channel in this server")

    act = action.action.lower()
    if act == "pause":
        if hasattr(player, "pause"):
            await player.pause(True)
        return {"status": "success", "detail": "Paused"}
    elif act == "resume":
        if hasattr(player, "pause"):
            await player.pause(False)
        return {"status": "success", "detail": "Resumed"}
    elif act == "skip":
        if hasattr(player, "skip"):
            await player.skip()
        return {"status": "success", "detail": "Skipped track"}
    elif act == "stop":
        if hasattr(player, "disconnect"):
            await player.disconnect()
        return {"status": "success", "detail": "Stopped and disconnected"}
    elif act == "set_volume":
        vol = int(action.value or 100)
        if hasattr(player, "set_volume"):
            await player.set_volume(max(0, min(150, vol)))
        return {"status": "success", "detail": f"Volume set to {vol}"}
    elif act == "set_filter":
        preset = str(action.value or "Flat")
        filters_cog = bot.get_cog("FilterCog")
        if filters_cog and hasattr(filters_cog, "apply_filter_preset"):
            try:
                await filters_cog.apply_filter_preset(player, preset)
                player.current_filter = preset
            except Exception as e:
                pass
        return {"status": "success", "detail": f"Filter applied: {preset}"}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {act}")

# --- Chat Safety & Word Filter ---

@router.get("/{guild_id}/safety", response_model=SafetyConfig, summary="Get chat safety and word blacklist")
async def get_safety_config(guild_id: int):
    db = await db_manager.get_connection('db/blword.db')
    await db.execute("""
        CREATE TABLE IF NOT EXISTS blacklist (
            guild_id TEXT,
            word TEXT,
            PRIMARY KEY (guild_id, word)
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS bypass_roles (
            guild_id TEXT,
            role_id INTEGER,
            PRIMARY KEY (guild_id, role_id)
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS bypass (
            guild_id TEXT,
            user_id INTEGER,
            PRIMARY KEY (guild_id, user_id)
        )
    """)
    await db.commit()

    cursor = await db.execute("SELECT word FROM blacklist WHERE guild_id = ?", (str(guild_id),))
    words = [r[0] for r in await cursor.fetchall()]

    cursor = await db.execute("SELECT role_id FROM bypass_roles WHERE guild_id = ?", (str(guild_id),))
    bypass_roles = [str(r[0]) for r in await cursor.fetchall()]

    cursor = await db.execute("SELECT user_id FROM bypass WHERE guild_id = ?", (str(guild_id),))
    bypass_users = [str(r[0]) for r in await cursor.fetchall()]

    return SafetyConfig(
        guild_id=str(guild_id),
        blacklisted_words=words,
        bypass_roles=bypass_roles,
        bypass_users=bypass_users
    )

@router.patch("/{guild_id}/safety", summary="Update chat safety config")
async def update_safety_config(guild_id: int, data: SafetyUpdate):
    db = await db_manager.get_connection('db/blword.db')

    if data.add_word:
        await db.execute(
            "INSERT OR IGNORE INTO blacklist (guild_id, word) VALUES (?, ?)",
            (str(guild_id), data.add_word.lower().strip())
        )
    if data.remove_word:
        await db.execute(
            "DELETE FROM blacklist WHERE guild_id = ? AND word = ?",
            (str(guild_id), data.remove_word.lower().strip())
        )
    if data.add_bypass_role:
        await db.execute(
            "INSERT OR IGNORE INTO bypass_roles (guild_id, role_id) VALUES (?, ?)",
            (str(guild_id), int(data.add_bypass_role))
        )
    if data.remove_bypass_role:
        await db.execute(
            "DELETE FROM bypass_roles WHERE guild_id = ? AND role_id = ?",
            (str(guild_id), int(data.remove_bypass_role))
        )

    await db.commit()
    return {"status": "success"}

# --- Social Alerts ---

@router.get("/{guild_id}/alerts", response_model=AlertsConfig, summary="Get social stream notification alerts")
async def get_alerts_config(guild_id: int):
    db = await db_manager.get_connection('db/notify.db')
    await db.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL UNIQUE,
            role_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL
        )
    """)
    await db.commit()

    cursor = await db.execute("SELECT id, type, role_id, channel_id FROM notifications")
    rows = await cursor.fetchall()
    alerts = []
    for r in rows:
        alerts.append(SocialAlertItem(
            id=r[0],
            type=r[1],
            role_id=str(r[2]),
            channel_id=str(r[3])
        ))

    return AlertsConfig(guild_id=str(guild_id), alerts=alerts)

@router.patch("/{guild_id}/alerts", summary="Update stream notification alerts")
async def update_alerts_config(guild_id: int, data: AlertsUpdate):
    db = await db_manager.get_connection('db/notify.db')
    await db.execute("""
        INSERT OR REPLACE INTO notifications (type, role_id, channel_id)
        VALUES (?, ?, ?)
    """, (data.type.lower(), int(data.role_id), int(data.channel_id)))
    await db.commit()
    return {"status": "success"}
