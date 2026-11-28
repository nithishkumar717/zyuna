module.exports = {
    BOT_TOKEN: process.env.BOT_TOKEN || '',
    CLIENT_ID: process.env.CLIENT_ID || '',
    OWNER_ID: process.env.OWNER_ID || '',
    SUPPORT_SERVER_ID: process.env.SUPPORT_SERVER_ID || '1525481611116806185',
    SUPPORT_INVITE_URL: process.env.SUPPORT_INVITE_URL || 'https://discord.gg/wn4yDS8Bj',
    PREFIX: ',',


    LAVALINK: {
        HOSTS: process.env.LAVALINK_HOSTS || 'lavalink.yunabot.xyz',
        PORTS: process.env.LAVALINK_PORTS || '26245',
        PASSWORDS: process.env.LAVALINK_PASSWORDS || 'nerdxlive',
        SECURES: process.env.LAVALINK_SECURES || 'false'
    },


    MUSIC: {
        DEFAULT_PLATFORM: 'ytsearch',
        AUTOCOMPLETE_LIMIT: 5,
        PLAYLIST_LIMIT: 3,
        ARTWORK_STYLE: 'MusicCard' // 'Banner' for MediaGallery or 'MusicCard' for custom image card
    },

    GENIUS: {
        API_KEY: process.env.GENIUS_API_KEY || ''
    }
};

