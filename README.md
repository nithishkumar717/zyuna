<div align="center">

```
███████╗██╗   ██╗██╗   ██╗███╗   ██╗ █████╗ 
╚══███╔╝╚██╗ ██╔╝██║   ██║████╗  ██║██╔══██╗
  ███╔╝  ╚████╔╝ ██║   ██║██╔██╗ ██║███████║
 ███╔╝    ╚██╔╝  ██║   ██║██║╚██╗██║██╔══██║
███████╗   ██║   ╚██████╔╝██║ ╚████║██║  ██║
╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
```

<h3>High-Fidelity Studio Audio & Server Utility Discord Bot paired with Next.js 14 Dashboard</h3>

<p>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/></a>
  <a href="https://nextjs.org"><img src="https://img.shields.io/badge/Next.js-14+-000000?style=for-the-badge&logo=nextdotjs&logoColor=white"/></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white"/></a>
  <a href="https://discordpy.readthedocs.io"><img src="https://img.shields.io/badge/Discord.py-v2-5865F2?style=for-the-badge&logo=discord&logoColor=white"/></a>
</p>
<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-red?style=for-the-badge"/></a>
  <a href="https://discord.gg/YzHCx5yQXv"><img src="https://img.shields.io/badge/Discord-Join_Server-5865F2?style=for-the-badge&logo=discord&logoColor=white"/></a>
  <a href="https://github.com/nithishkumar717/zyuna"><img src="https://img.shields.io/badge/GitHub-Zyuna-181717?style=for-the-badge&logo=github&logoColor=white"/></a>
</p>

</div>

---

## ✦ Overview

**Zyuna** is a production-grade Discord bot and web platform featuring high-fidelity Wavelink studio audio, dynamic Yuna-styled canvas player cards, DSP audio equalizer filters, social livestream monitors, visual embed builders, chat safety filters, and state persistence that resumes audio seamlessly across restarts.

```
ZyroX-CV2-AIO-With-Dashboard/
├── 🤖  bot/                   Python Discord bot + FastAPI backend
│   ├── api/                   Dashboard REST API (FastAPI)
│   ├── cogs/                  Active bot cogs (Music, Filters, Utility, Alerts, Safety, Games, System)
│   │   ├── commands/          Command modules (music, filters, Embed, translate, map, blacklist, notify, stats...)
│   │   ├── events/            System & error event handlers
│   │   └── zyuna/             Department help menus & metadata
│   ├── core/                  Bot client, context, session handlers
│   ├── utils/                 Music card generator, CV2 UI components, emoji sets, time utils
│   ├── db/                    Active SQLite databases & state persistence
│   └── zyuna.py               Bot entry point
│
└── 🌐  dashboard/             Next.js 14 App Router frontend
    ├── app/                   Dashboard routes (/dashboard/guild/[guildId]/music, safety, alerts, settings)
    ├── components/            Guild tabs, music controls, safety panels, landing pages
    ├── lib/                   API clients & auth helpers
    └── types/                 TypeScript schemas & models
```

---

## ✦ Features

<table>
<tr>
<td width="50%">

**🎵 Studio Audio**
- **Wavelink v3 / Lavalink** lossless audio playback
- **Yuna UI Layout**: Dynamic high-res music canvas cards (`music_card.png`)
- **AI Recommendations**: Interactive song suggestion dropdown (`SuggestedByAISelect`)
- **CV2 4-Row Controls**: Volume sliders, loop modes, autoplay, shuffle, seek
- **Uninterrupted Audio**: Seamless session recovery across host reboots
- **Spotify Card**: Visual listening profile renderer (`>spotify`)
- **Now Playing Alerts**: Auto-announcements in voice channels (`>autonp`)

</td>
<td width="50%">

**🎛️ Audio FX DSP Filters**
- Real-time hardware-accelerated audio equalizers
- **8D Audio**: Rotating binaural surround sound
- **Bassboost**: Multi-tier low-frequency amplification
- **Nightcore & Vaporwave**: Pitch and tempo modulators
- **Genre Presets**: Pop, Soft, Treblebass, Karaoke, Vibrato, Tremolo
- Instant reset to studio flat sound (`>clearfilters`)

</td>
</tr>
<tr>
<td>

**🛠️ Server Utilities**
- **Visual Embed Builder**: Interactive modal designer (`>embed`)
- **Hinglish Translator**: Natural language translation (`>hinglish`)
- **Satellite Map**: High-res imagery viewer (`>map`)
- **YouTube Explorer**: Multi-result video finder (`>search_youtube`)
- **Webhook Manager**: Channel webhook operations (`>create_hook`, `>delete_hook`, `>list_hooks`)

</td>
<td>

**📡 Social Stream Alerts**
- Automated background pollers with zero-delay webhook pushes
- **YouTube Alerts**: Video uploads & livestream alerts (`>setnotif youtube`)
- **Twitch Alerts**: Instant streamer go-live broadcasts (`>setnotif twitch`)
- Configurable announcement channels & role ping mentions
- Quick configuration inspection (`>setnotif list`, `>setnotif reset`)

</td>
</tr>
<tr>
<td>

**🛡️ Chat Safety & Server Stats**
- **Word Blacklist**: Forbidden vocabulary filter with role bypasses (`>blacklistword`)
- **Staff Dispatch**: Direct emergency staff messaging line (`>dm_staff`)
- **Message Tracking**: Daily and total message counters (`>messages`)
- **Manual Adjustments**: Staff message point management (`>addmessages`, `>removemessages`, `>clearmessage`)

</td>
<td>

**🌐 Web Dashboard & Telemetry**
- **Next.js 14 Dashboard**: Edge-synchronized control panel
- Dedicated tabs for Studio Audio, Chat Safety, Stream Alerts, and Settings
- Live cluster telemetry, memory stats, and latency gauges (`>stats`, `>status`)
- Reaction time challenge mini-game (`>reaction`)
- Owner hot-reloader & safe threaded Git puller (`>gitpull`, `>reload`)

</td>
</tr>
</table>

---

## ✦ Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Java 17+ (for Lavalink)

### Bot Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/nithishkumar717/zyuna.git
   cd zyuna
   ```

2. Setup virtual environment:
   ```bash
   cd bot
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate # Linux/macOS
   pip install -r requirements.txt
   ```

3. Configure environment variables in `bot/.env`:
   ```env
   TOKEN=your_discord_bot_token
   LAVALINK_URI=http://localhost:2333
   LAVALINK_PASSWORD=youshallnotpass
   API_KEY=your_secure_api_key
   ```

4. Launch the bot:
   ```bash
   python zyuna.py
   ```

### Dashboard Setup
1. Navigate to the dashboard directory:
   ```bash
   cd ../dashboard
   npm install
   ```

2. Configure environment variables in `dashboard/.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   NEXT_PUBLIC_DASHBOARD_API_KEY=your_secure_api_key
   ```

3. Launch development server:
   ```bash
   npm run dev
   ```

---

## ✦ License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
