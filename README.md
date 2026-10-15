# AeroX CV2 Music Bot

A modern Discord music bot built with Components V2, designed for reliable playback, queue management, playlists, and music controls.

[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![Discord.js](https://img.shields.io/badge/Discord.js-v14-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discord.js.org/)
[![License](https://img.shields.io/badge/License-ISC-blue?style=flat-square)](LICENSE)

## Overview

This bot supports:

- Music playback from YouTube and Spotify
- Queue controls and playback management
- Playlist and favorites saving
- Audio filters and autoplay
- Lyrics lookup
- Slash commands and prefix commands

## Requirements

- Node.js 18 or later
- A Discord bot token
- A LavaLink server
- Optional: Spotify API credentials and Genius API key for enhanced features

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/itsfizys/AeroX-CV2-Music-Bot.git
   cd AeroX-CV2-Music-Bot
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Create a `.env` file in the project root:

   ```env
   BOT_TOKEN=your_discord_bot_token
   CLIENT_ID=your_bot_client_id

   LAVALINK_HOSTS=your.lavalink.host
   LAVALINK_PORTS=2333
   LAVALINK_PASSWORDS=youshallnotpass
   LAVALINK_SECURES=false

   GENIUS_API_KEY=your_genius_api_key
   ```

4. Start the bot:

   ```bash
   npm start
   ```

## LavaLink

AeroX Music requires a LavaLink server to stream audio.

Options:

- Use a public LavaLink server
- Host your own LavaLink instance

For self-hosting, download Lavalink from the official releases page and configure your `application.yml` before updating your environment variables.

## Commands

### Music

- `/play`
- `/pause`
- `/resume`
- `/skip`
- `/stop`
- `/nowplaying`
- `/queue`

### Queue management

- `/shuffle`
- `/clear`
- `/remove`
- `/move`
- `/back`
- `/seek`

### Playlists and favorites

- `/playlist-save`
- `/playlist-load`
- `/playlist-list`
- `/playlist-delete`
- `/favorite-add`
- `/favorite-remove`
- `/favorite-list`

### Settings and info

- `/volume`
- `/filter`
- `/loop`
- `/autoplay`
- `/help`
- `/ping`
- `/lyrics`

## Project structure

```text
AeroX-CV2-Music-Bot/
├── commands/
├── pCommands/
├── music/
├── helpers/
├── utils/
├── database/
├── assets/
├── config.js
├── index.js
├── .env.example
├── package.json
├── README.md
└── LICENSE
```

## Usage terms

This project is intended for personal or private server use. Please keep credit to the original developer and do not redistribute or publicly showcase the project without permission.

## Contributing

Contributions are welcome. To contribute:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a pull request

## Support

- Discord: `itsfizys`
- Portfolio: https://itsfiizys.com
- Community server: https://discord.gg/8wfT8SfB5Z

## License

This project is licensed under the ISC License.
