const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const axios = require('axios');
const { REST, Routes } = require('discord.js');
const emojis = require('../emojis.json');

const EMOJI_MENTION = /^<(?<animated>a?):(?<name>[A-Za-z0-9_]+):(?<id>\d+)>$/;
const MAX_EMOJI_SIZE = 256 * 1024;
const emojiDirectory = path.join(__dirname, '..', 'assets', 'emojis');
const syncCachePath = path.join(__dirname, '..', '..', 'database', '.emoji-sync-cache.json');

function loadSyncCache() {
    try {
        return JSON.parse(fs.readFileSync(syncCachePath, 'utf8'));
    } catch {
        return {};
    }
}

function saveSyncCache(cache) {
    try {
        fs.mkdirSync(path.dirname(syncCachePath), { recursive: true });
        fs.writeFileSync(syncCachePath, JSON.stringify(cache, null, 2));
    } catch {
        // Non-fatal if cache cannot be written
    }
}

function getApplicationEmojiName(name) {
    const normalized = name.toLowerCase();

    if (normalized === 'aerox') {
        return 'zyuna';
    }

    if (normalized.startsWith('aerox')) {
        return `zyuna_${normalized.slice('aerox'.length).replace(/^_+/, '')}`;
    }

    return normalized;
}

function getEmojiManifest() {
    const manifest = new Map();

    for (const mention of Object.values(emojis)) {
        const match = EMOJI_MENTION.exec(mention);
        if (!match) {
            throw new Error(`Invalid custom emoji mention in emojis.json: ${mention}`);
        }

        const entry = {
            id: match.groups.id,
            name: match.groups.name,
            animated: match.groups.animated === 'a'
        };
        const existing = manifest.get(entry.id);

        if (existing) {
            existing.animated ||= entry.animated;
        } else {
            manifest.set(entry.id, entry);
        }
    }

    return [...manifest.values()];
}

async function getEmojiAsset(entry) {
    const targetName = getApplicationEmojiName(entry.name);
    const extension = entry.animated ? 'gif' : 'png';
    const filename = `${targetName}-${entry.id}.${extension}`;
    const assetPath = path.join(emojiDirectory, filename);

    try {
        const image = await fs.promises.readFile(assetPath);
        validateImageSize(image, filename);
        return { image, assetPath, downloaded: false };
    } catch (error) {
        if (error.code !== 'ENOENT') {
            throw error;
        }
    }

    const url = `https://cdn.discordapp.com/emojis/${entry.id}.${extension}`;
    const response = await axios.get(url, {
        responseType: 'arraybuffer',
        timeout: 30000
    });
    const image = Buffer.from(response.data);
    validateImageSize(image, filename);

    await fs.promises.mkdir(emojiDirectory, { recursive: true });
    await fs.promises.writeFile(assetPath, image);

    return { image, assetPath, downloaded: true };
}

function validateImageSize(image, filename) {
    if (image.length === 0) {
        throw new Error(`Downloaded emoji asset is empty: ${filename}`);
    }

    if (image.length > MAX_EMOJI_SIZE) {
        throw new Error(`Emoji asset exceeds Discord's 256 KiB limit: ${filename}`);
    }
}

async function syncApplicationEmojis(applicationId, token) {
    const manifest = getEmojiManifest();
    const assets = new Map();
    let downloaded = 0;

    for (const entry of manifest) {
        const asset = await getEmojiAsset(entry);
        assets.set(entry.id, asset);
        if (asset.downloaded) {
            downloaded++;
        }
    }

    const rest = new REST({ version: '10' }).setToken(token);
    const response = await rest.get(Routes.applicationEmojis(applicationId));
    if (!response || !Array.isArray(response.items)) {
        throw new Error('Discord returned an invalid application emoji list');
    }

    const applicationEmojis = new Map(
        response.items.map(emoji => [emoji.name.toLowerCase(), emoji])
    );
    const applicationEmojisById = new Map(
        response.items.map(emoji => [emoji.id, emoji])
    );
    const syncCache = loadSyncCache();
    const uploadedBySourceId = new Map();
    let created = 0;
    let renamed = 0;
    let replaced = 0;

    for (const entry of manifest) {
        const targetName = getApplicationEmojiName(entry.name);
        const asset = assets.get(entry.id);
        const assetHash = crypto.createHash('sha256').update(asset.image).digest('hex');

        let applicationEmoji = applicationEmojisById.get(entry.id) || applicationEmojis.get(targetName.toLowerCase());
        const oldEmoji = applicationEmojis.get(entry.name.toLowerCase());

        if (!applicationEmoji && oldEmoji && oldEmoji.name !== targetName) {
            applicationEmoji = await rest.patch(
                Routes.applicationEmoji(applicationId, oldEmoji.id),
                { body: { name: targetName } }
            );
            applicationEmojis.delete(oldEmoji.name.toLowerCase());
            applicationEmojis.set(targetName.toLowerCase(), applicationEmoji);
            renamed++;
        }

        // Replace existing application emoji if its source asset/ID changed
        const cached = syncCache[targetName.toLowerCase()];
        const cacheChanged = cached && (cached.sourceId !== entry.id || cached.hash !== assetHash);
        const newerSnowflakeReplacement =
            applicationEmoji &&
            applicationEmoji.id !== entry.id &&
            targetName.toLowerCase() === 'white_next' &&
            BigInt(applicationEmoji.id) < BigInt(entry.id);

        if (applicationEmoji && (cacheChanged || newerSnowflakeReplacement)) {
            try {
                await rest.delete(Routes.applicationEmoji(applicationId, applicationEmoji.id));
                applicationEmojis.delete(applicationEmoji.name.toLowerCase());
                applicationEmojisById.delete(applicationEmoji.id);
                applicationEmoji = null;
                replaced++;
            } catch {
                // Keep existing if delete fails
            }
        }

        if (!applicationEmoji) {
            const mimeType = entry.animated ? 'image/gif' : 'image/png';
            const image = `data:${mimeType};base64,${asset.image.toString('base64')}`;

            applicationEmoji = await rest.post(
                Routes.applicationEmojis(applicationId),
                { body: { name: targetName, image } }
            );
            applicationEmojis.set(targetName.toLowerCase(), applicationEmoji);
            applicationEmojisById.set(applicationEmoji.id, applicationEmoji);
            created++;
        }

        syncCache[targetName.toLowerCase()] = {
            sourceId: entry.id,
            appEmojiId: applicationEmoji.id,
            hash: assetHash
        };
        uploadedBySourceId.set(entry.id, applicationEmoji);
    }

    saveSyncCache(syncCache);

    for (const [key, mention] of Object.entries(emojis)) {
        const match = EMOJI_MENTION.exec(mention);
        const applicationEmoji = uploadedBySourceId.get(match.groups.id);
        const animated = applicationEmoji.animated ?? match.groups.animated === 'a';
        emojis[key] = `<${animated ? 'a' : ''}:${applicationEmoji.name}:${applicationEmoji.id}>`;
    }

    return {
        total: manifest.length,
        downloaded,
        created,
        renamed,
        replaced
    };
}

module.exports = { syncApplicationEmojis };
