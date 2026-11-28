const { PermissionFlagsBits } = require('discord.js');
const { isMusicTrackUrl } = require('./musicTrackResolver');

function formatDuration(ms) {
    if (typeof ms !== 'number' || isNaN(ms) || ms < 0) return '0:00';
    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
}

function createProgressBar(player) {
    if (!player.currentTrack || !player.currentTrack.info.length) return '';
    if (player.currentTrack.info.isStream) return '`00:00|▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬🔴 LIVE`';

    const current = player.position;
    const total = player.currentTrack.info.length;
    const size = 25;

    let percent = Math.round((current / total) * size);
    if (percent < 0) percent = 0;
    if (percent > size) percent = size;

    const empty = size - percent;
    const safeEmpty = empty < 0 ? 0 : empty;

    const progress = '▬'.repeat(percent) + '🔵' + '▬'.repeat(safeEmpty);
    return `\`${formatDuration(current)}|${progress}|${formatDuration(total)}\``;
}

function hasControlPermission(interactionOrMessage, player) {
    if (!player.currentTrack) return false;
    
    const member = interactionOrMessage.member;
    const userId = interactionOrMessage.user?.id || interactionOrMessage.author?.id;
    
    if (member.permissions.has(PermissionFlagsBits.ManageGuild) ||
        member.permissions.has(PermissionFlagsBits.Administrator)) {
        return true;
    }

    const requesterId = player.currentTrack.info.requester?.id;
    if (userId === requesterId) return true;

    return false;
}

const UNSUPPORTED_URL_MESSAGE =
    'Currently we only support direct search, Spotify playlist URLs, JioSaavn URLs, or Yuna Music Archive URLs.';

/**
 * Validates whether a play query is a direct text search, a Spotify playlist URL,
 * a JioSaavn URL, or a musictrack.yunabot.xyz URL. Rejects all other URLs.
 * @param {string} query
 * @returns {{ valid: boolean, isUrl: boolean, isSpotifyPlaylist: boolean, isJioSaavn: boolean, isMusicTrack: boolean, message?: string }}
 */
function validatePlayQuery(query) {
    const trimmed = (query || '').trim();
    const isUrl = /^https?:\/\//i.test(trimmed);
    const isSpotifyPlaylist = /^https?:\/\/open\.spotify\.com\/playlist\/[a-zA-Z0-9]+/i.test(trimmed);
    const isJioSaavn = /^https?:\/\/(?:www\.)?jiosaavn\.com\//i.test(trimmed);
    const isMusicTrack = isMusicTrackUrl(trimmed);

    if (isUrl && !isSpotifyPlaylist && !isJioSaavn && !isMusicTrack) {
        return {
            valid: false,
            isUrl: true,
            isSpotifyPlaylist: false,
            isJioSaavn: false,
            isMusicTrack: false,
            message: UNSUPPORTED_URL_MESSAGE,
        };
    }

    return {
        valid: true,
        isUrl,
        isSpotifyPlaylist,
        isJioSaavn,
        isMusicTrack,
    };
}

module.exports = {
    formatDuration,
    createProgressBar,
    hasControlPermission,
    validatePlayQuery,
    UNSUPPORTED_URL_MESSAGE
};

