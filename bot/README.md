<div align="center">

```
███████╗██╗   ██╗██╗   ██╗███╗   ██╗ █████╗ 
╚══███╔╝╚██╗ ██╔╝██║   ██║████╗  ██║██╔══██╗
  ███╔╝  ╚████╔╝ ██║   ██║██╔██╗ ██║███████║
 ███╔╝    ╚██╔╝  ██║   ██║██║╚██╗██║██╔══██║
███████╗   ██║   ╚██████╔╝██║ ╚████║██║  ██║
╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
```

<h3>Zyuna Bot — Python Discord Bot + FastAPI Backend</h3>

<p>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white"/></a>
  <a href="https://discordpy.readthedocs.io"><img src="https://img.shields.io/badge/Discord.py-v2-5865F2?style=for-the-badge&logo=discord&logoColor=white"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-red?style=for-the-badge"/></a>
</p>
<p>
  <a href="https://discord.gg/YzHCx5yQXv"><img src="https://img.shields.io/badge/Discord-Join_Server-5865F2?style=for-the-badge&logo=discord&logoColor=white"/></a>
  <a href="https://github.com/nithishkumar717/zyuna"><img src="https://img.shields.io/badge/GitHub-Zyuna-181717?style=for-the-badge&logo=github&logoColor=white"/></a>
</p>

</div>

---

## ✦ Overview

This directory contains the Zyuna Discord bot engine built on `discord.py v2` along with the high-performance `FastAPI` service that communicates with the Next.js web dashboard. Everything starts seamlessly from `python zyuna.py`.

```
bot/
├── api/                   FastAPI REST backend (/bot, /guilds, /admin)
│   ├── routes/            Modular route handlers
│   ├── db_manager.py      Persistent connection pool
│   ├── schemas.py         Pydantic v2 data models
│   └── server.py          Uvicorn server lifecycle
├── cogs/
│   ├── commands/          Feature command suites (music, filters, Embed, translate, blacklist, notify, stats...)
│   ├── events/            System, error, and mention event listeners
│   └── zyuna/             CV2 help category definitions
├── core/                  AutoShardedBot client, Context, session recovery
├── utils/                 MusicCardGenerator, CV2 components, emoji mappings, time utils
├── db/                    Active SQLite databases & session json
└── zyuna.py               Bot entry point
```

---

## ✦ Active Bot Modules

1. **Studio Audio (`cogs/commands/music.py`)**:
   - Wavelink v3 / Lavalink audio pipeline with lossless stream decoding
   - Dynamic Yuna-styled canvas player card generator (`utils/music_card.py`)
   - AI recommendation selector (`SuggestedByAISelect`) & 4-row CV2 controls
   - Uninterrupted audio recovery across host reboots (`db/music_active_sessions.json`)
   - Spotify listening card (`>spotify`) and Now Playing auto alerts (`>autonp`)

2. **DSP Audio FX Filters (`cogs/commands/filters.py`)**:
   - 15+ real-time equalizer filters: 8D, Bassboost, Nightcore, Vaporwave, Pop, Soft, Treblebass, Karaoke, Vibrato, Tremolo, and Studio Flat.

3. **Server Utilities (`cogs/commands/Embed.py`, `translate.py`, `map.py`, `youtube.py`)**:
   - Interactive visual embed designer with live modals
   - Colloquial Hinglish to English translator
   - Satellite terrain map viewer
   - Multi-result YouTube explorer and channel webhook creator/deleter

4. **Social Stream Alerts (`cogs/commands/notify.py`)**:
   - Automated push notifications for YouTube uploads and Twitch livestreams
   - Role ping mentions and custom announcement channels

5. **Chat Safety & Server Stats (`cogs/commands/blacklist.py`, `dms.py`, `messages.py`, `msgpack.py`)**:
   - Forbidden word filter with role bypass exemptions
   - Staff emergency direct dispatch (`>dm_staff`)
   - Server message counting and tracking

6. **Mini-Games (`cogs/commands/messages.py`)**:
   - High-speed reflex reaction test (`>reaction`)

7. **System Telemetry & Owner Suite (`cogs/commands/stats.py`, `status.py`, `owner.py`, `owner2.py`)**:
   - Memory usage, ping latency, cluster hardware statistics
   - Non-blocking hot-reload and safe threaded Git updates (`>gitpull`, `>reload`)

---

## ✦ Installation & Run

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows

# Install requirements
pip install -r requirements.txt

# Start bot and API backend
python zyuna.py
```
