const SUPPORTED_LANGUAGES = [
    'auto',
    'tamil',
    'hindi',
    'malayalam',
    'telugu',
    'kannada',
    'punjabi',
    'english',
];

const UNOFFICIAL_KEYWORDS = [
    'slowed',
    'reverb',
    '8d',
    'bass boosted',
    'karaoke',
    'ringtone',
    'teaser',
    'trailer',
    'dialogue',
    'interval',
    'mashup',
    'lofi',
    'nightcore',
    'brazilian',
    'unplugged',
    'orchestral',
    'instrumental',
];

const ARTIST_LANGUAGE_HINTS = {
    tamil: ['anirudh', 'yuvan', 'gv prakash', 'g.v. prakash', 'santhosh narayanan', 'harris jayaraj', 'imman', 'hiphop tamizha', 'ilaiyaraaja', 'vijay antony', 'sai abhyankkar', 'dhanush', 'sid sriram'],
    hindi: ['arijit singh', 'pritam', 'shreya ghoshal', 'vishal-shekhar', 'vishal mishra', 'amit trivedi', 'sachin-jigar', 'badshah', 'jubin nautiyal', 'atif aslam', 'tanishk bagchi', 'sachet-parampara'],
    malayalam: ['sushin shyam', 'rex vijayan', 'jakes bejoy', 'heshem abdul wahab', 'hesham abdul wahab', 'vineeth sreenivasan', 'govind vasantha', 'shaan rahman', 'justin varghese'],
    telugu: ['thaman', 'devi sri prasad', 'dsp', 'keeravani', 'anup rubens', 'bheems ceciroleo', 'mickey j meyer'],
    kannada: ['arjun janya', 'charan raj', 'ajaneesh loknath', 'ravi basrur', 'raghu dixit', 'v harikrishna'],
    punjabi: ['diljit dosanjh', 'ap dhillon', 'karan aujla', 'sidhu moose wala', 'shubh', 'guru randhawa', 'ammy virk'],
};

function normalizeTitle(title = '') {
    return String(title)
        .toLowerCase()
        .replace(/\s*\(.*?\)\s*/g, ' ')
        .replace(/\s*\[.*?\]\s*/g, ' ')
        .replace(/[^\w\s]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

function detectTrackLanguage(track, preferredLanguage = 'auto') {
    const pref = String(preferredLanguage || 'auto').toLowerCase();
    if (pref !== 'auto' && SUPPORTED_LANGUAGES.includes(pref)) {
        return pref;
    }

    const haystack = `${track?.info?.title || ''} ${track?.info?.author || ''} ${track?.info?.uri || ''}`.toLowerCase();
    for (const [lang, hints] of Object.entries(ARTIST_LANGUAGE_HINTS)) {
        if (hints.some((hint) => haystack.includes(hint))) {
            return lang;
        }
    }

    for (const lang of SUPPORTED_LANGUAGES) {
        if (lang !== 'auto' && haystack.includes(lang)) {
            return lang;
        }
    }

    return 'tamil';
}

function buildTrendingQueries(language) {
    const year = new Date().getFullYear();
    const lang = language === 'auto' ? 'tamil' : language;

    const queries = [
        `latest ${lang} songs ${year}`,
        `new ${lang} hits ${year}`,
        `${lang} trending songs`,
        `${lang} new releases`,
        `${lang} top 20 songs`,
        `${lang} viral hits`,
    ];

    // Fisher-Yates shuffle for fresh rotation each cycle
    for (let i = queries.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [queries[i], queries[j]] = [queries[j], queries[i]];
    }

    return queries;
}

function isQualityTrack(track, originalTitleNormalized, historySet) {
    if (!track || !track.info) return false;
    if (track.info.isStream) return false;
    if ((track.info.length || 0) < 60000) return false;

    const rawTitle = String(track.info.title || '');
    const lowerTitle = rawTitle.toLowerCase();
    if (UNOFFICIAL_KEYWORDS.some((kw) => lowerTitle.includes(kw))) {
        return false;
    }

    const norm = normalizeTitle(rawTitle);
    if (!norm || norm === originalTitleNormalized) return false;

    const id = track.info.identifier;
    if (id && historySet.has(`id:${id}`)) return false;
    if (historySet.has(`title:${norm}`)) return false;

    return true;
}

async function resolveAutoplayTracks(client, player, lastTrack, preferredLanguage = 'auto', maxTracks = 4) {
    const requester = lastTrack?.info?.requester || client.user;
    const trackTitle = lastTrack?.info?.title || '';
    const trackUri = lastTrack?.info?.uri || '';
    const trackId = lastTrack?.info?.identifier || '';
    const sourceName = String(lastTrack?.info?.sourceName || '').toLowerCase();

    const activeLanguage = detectTrackLanguage(lastTrack, preferredLanguage);
    const originalTitleNormalized = normalizeTitle(trackTitle);

    if (!player._autoplayHistory) {
        player._autoplayHistory = new Set();
    }
    if (trackId) player._autoplayHistory.add(`id:${trackId}`);
    if (originalTitleNormalized) player._autoplayHistory.add(`title:${originalTitleNormalized}`);

    const candidates = [];

    // 1. Future-ready YouTube Mix support if track is from YouTube
    if (trackUri.includes('youtube.com') || trackUri.includes('youtu.be')) {
        try {
            const ytRes = await client.poru.resolve({
                query: `https://music.youtube.com/watch?v=${trackId}&list=RD${trackId}`,
                source: 'ytmsearch',
                requester,
            });
            if (ytRes?.tracks?.length) {
                candidates.push(...ytRes.tracks);
            }
        } catch {
            // Fall through to JioSaavn engine
        }
    }

    // 2. JioSaavn native recommendation radio (jsrec:<id>) when track is from JioSaavn
    if ((sourceName === 'jiosaavn' || trackUri.includes('jiosaavn.com')) && trackId) {
        try {
            const recRes = await client.poru.resolve({
                query: `jsrec:${trackId}`,
                requester,
            });
            if (recRes?.tracks?.length) {
                candidates.push(...recRes.tracks);
            }
        } catch {
            // Fall through to trending queries
        }
    }

    // 3. Language-based Latest Trending & New Launch queries on JioSaavn (jssearch)
    const trendingQueries = buildTrendingQueries(activeLanguage);
    for (const q of trendingQueries.slice(0, 2)) {
        try {
            const searchRes = await client.poru.resolve({
                query: q,
                source: 'jssearch',
                requester,
            });
            if (searchRes?.tracks?.length) {
                candidates.push(...searchRes.tracks);
            }
        } catch {
            // Continue to next trending query
        }
    }

    // Filter, deduplicate, and pick up to maxTracks
    const picked = [];
    const cycleSeen = new Set();

    for (const track of candidates) {
        if (picked.length >= maxTracks) break;
        if (!isQualityTrack(track, originalTitleNormalized, player._autoplayHistory)) continue;

        const norm = normalizeTitle(track.info.title);
        const id = track.info.identifier;
        if (cycleSeen.has(norm) || (id && cycleSeen.has(id))) continue;

        cycleSeen.add(norm);
        if (id) cycleSeen.add(id);

        track.info.requester = requester;
        picked.push(track);
    }

    // Relax unofficial-keyword filter only if strict pass found nothing at all
    if (picked.length === 0) {
        for (const track of candidates) {
            if (picked.length >= maxTracks) break;
            if (!track?.info || track.info.isStream || (track.info.length || 0) < 45000) continue;
            const norm = normalizeTitle(track.info.title || '');
            const id = track.info.identifier;
            if (!norm || norm === originalTitleNormalized) continue;
            if ((id && player._autoplayHistory.has(`id:${id}`)) || player._autoplayHistory.has(`title:${norm}`)) continue;
            if (cycleSeen.has(norm) || (id && cycleSeen.has(id))) continue;

            cycleSeen.add(norm);
            if (id) cycleSeen.add(id);
            track.info.requester = requester;
            picked.push(track);
        }
    }

    return {
        tracks: picked,
        language: activeLanguage,
        configuredLanguage: String(preferredLanguage || 'auto').toLowerCase(),
    };
}

module.exports = {
    SUPPORTED_LANGUAGES,
    normalizeTitle,
    detectTrackLanguage,
    buildTrendingQueries,
    resolveAutoplayTracks,
};
