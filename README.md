<div align="center">

```
███████╗██╗   ██╗██╗   ██╗███╗   ██╗ █████╗ 
╚══███╔╝╚██╗ ██╔╝██║   ██║████╗  ██║██╔══██╗
  ███╔╝  ╚████╔╝ ██║   ██║██╔██╗ ██║███████║
 ███╔╝    ╚██╔╝  ██║   ██║██║╚██╗██║██╔══██║
███████╗   ██║   ╚██████╔╝██║ ╚████║██║  ██║
╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
```

<h3>High-Fidelity Studio Audio & Server Utility Discord Bot</h3>

<p>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/></a>
  <a href="https://discordpy.readthedocs.io"><img src="https://img.shields.io/badge/Discord.py-v2-5865F2?style=for-the-badge&logo=discord&logoColor=white"/></a>
  <a href="https://wavelink.dev"><img src="https://img.shields.io/badge/Wavelink-v3-blue?style=for-the-badge"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-red?style=for-the-badge"/></a>
</p>
<p>
  <a href="https://discord.gg/YzHCx5yQXv"><img src="https://img.shields.io/badge/Discord-Join_Server-5865F2?style=for-the-badge&logo=discord&logoColor=white"/></a>
  <a href="https://github.com/nithishkumar717/zyuna"><img src="https://img.shields.io/badge/GitHub-Zyuna-181717?style=for-the-badge&logo=github&logoColor=white"/></a>
</p>

</div>

---

## ✦ Overview

**Zyuna** is a standalone, high-performance Discord bot powered by `discord.py v2` and `Wavelink v3`. Engineered for audiophiles and community servers, it delivers lossless audio playback, Yuna-styled canvas player cards, 15+ real-time hardware DSP equalizer filters, social livestream monitors, visual embed builders, chat safety filters, and uninterrupted state persistence across bot restarts.

```
Zyuna/
├── assets/                    Images, fonts, and bot artwork
├── cogs/                      Commands, events, and CV2 help categories
│   ├── commands/              Music, filters, Embed, translate, map, blacklist, notify, stats...
│   ├── events/                Errors, guild join/leave, auto-blacklist, mention responses
│   └── zyuna/                  Interactive CV2 help category modules
├── core/                      AutoShardedBot client, Context, session recovery
├── data/                      Cards, music art, and game assets
├── db/                        SQLite databases & active music session persistence
├── lang/                      Language files
├── utils/                      Music cards, CV2 components, emoji mappings, time utilities
├── requirements.txt
└── zyuna.py                   Bot entry point
```

---

## ✦ Bot Feature Suites

<table>
<tr>
<td width="50%">

**🎵 Studio Audio**
- **Wavelink v3 / Lavalink** lossless audio pipeline
- **Yuna UI Layout**: Dynamic canvas music cards (`music_card.png`)
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

**⚡ System Telemetry & Owner Suite**
- Live cluster telemetry, memory stats, and latency gauges (`>stats`, `>status`)
- Reaction time challenge mini-game (`>reaction`)
- Interactive CV2 help menu with clickable invite & support links (`>help`)
- Owner hot-reloader & safe threaded Git puller (`>gitpull`, `>reload`)

</td>
</tr>
</table>

---

## ✦ Getting Started

### Prerequisites
- Python 3.10+
- Java 17+ (for Lavalink)

### Setup & Run
1. Clone the repository:
   ```bash
   git clone https://github.com/nithishkumar717/zyuna.git
   cd zyuna
   ```

2. Setup virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate # Linux/macOS
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and configure your environment variables:
   ```env
   TOKEN=your_discord_bot_token
   LAVALINK_URI=http://localhost:2333
   LAVALINK_PASSWORD=youshallnotpass
   OWNER_IDS=your_discord_user_id
   ```

4. Launch the bot:
   ```bash
   python zyuna.py
   ```

---

## ✦ License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
