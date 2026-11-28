const axios = require('axios');

const MUSICTRACK_URL_REGEX = /^https?:\/\/musictrack\.yunabot\.xyz\/track\/[A-Za-z0-9_-]+(?:\?.*)?$/i;

function decodeHtmlEntities(str = '') {
    return String(str)
        .replace(/&quot;/g, '"')
        .replace(/&#39;|&apos;/g, "'")
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .trim();
}

function extractMetaTag(html, propertyName) {
    const escaped = propertyName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex1 = new RegExp(`<meta[^>]+property=["']${escaped}["'][^>]+content=["']([^"']+)["']`, 'i');
    const regex2 = new RegExp(`<meta[^>]+content=["']([^"']+)["'][^>]+property=["']${escaped}["']`, 'i');
    const match = regex1.exec(html) || regex2.exec(html);
    return match ? decodeHtmlEntities(match[1]) : null;
}

function isMusicTrackUrl(query) {
    return MUSICTRACK_URL_REGEX.test(String(query || '').trim());
}

async function fetchMusicTrackMeta(url) {
    const response = await axios.get(url.trim(), {
        timeout: 8000,
        headers: { 'User-Agent': 'Zyuna-Bot/1.0' },
        responseType: 'text',
    });
    const html = String(response.data || '');
    const ogTitle = extractMetaTag(html, 'og:title');
    const ogImage = extractMetaTag(html, 'og:image');

    if (!ogTitle) {
        throw new Error('Could not read track metadata from musictrack.yunabot.xyz');
    }

    const searchQuery = ogTitle.replace(/\s*[—–-]\s*/g, ' ').replace(/\s+/g, ' ').trim();
    return { ogTitle, ogImage, searchQuery };
}

/**
 * Resolves a query through Poru, transparently handling musictrack.yunabot.xyz/track/... URLs
 * by extracting OpenGraph metadata and injecting fallback artwork if Lavalink returns null.
 */
async function resolveMusicQuery(client, query, requester) {
    const trimmed = String(query || '').trim();
    if (!isMusicTrackUrl(trimmed)) {
        return client.poru.resolve({ query, requester });
    }

    const meta = await fetchMusicTrackMeta(trimmed);
    const res = await client.poru.resolve({ query: meta.searchQuery, requester });

    if (res && Array.isArray(res.tracks)) {
        for (const track of res.tracks) {
            if (track?.info) {
                if (!track.info.artworkUrl && meta.ogImage) {
                    track.info.artworkUrl = meta.ogImage;
                }
                if (!track.info.uri) {
                    track.info.uri = trimmed;
                }
            }
        }
    }

    return res;
}

module.exports = {
    isMusicTrackUrl,
    fetchMusicTrackMeta,
    resolveMusicQuery,
};
