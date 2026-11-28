const { ChannelType, PermissionFlagsBits } = require('discord.js');
const config = require('../config');

const CACHE_TTL_MS = 15 * 60 * 1000; // 15 minutes
let cachedUrl = null;
let cachedAt = 0;
let pendingPromise = null;

/**
 * Resolves a permanent invite URL for the configured support server ID,
 * caching it in memory and falling back to config.SUPPORT_INVITE_URL.
 */
async function getSupportServerUrl(client) {
    const fallback = config.SUPPORT_INVITE_URL || 'https://discord.gg/wn4yDS8Bj';
    const guildId = config.SUPPORT_SERVER_ID;

    if (!client || !guildId) {
        return fallback;
    }

    const now = Date.now();
    if (cachedUrl && now - cachedAt < CACHE_TTL_MS) {
        return cachedUrl;
    }

    if (pendingPromise) {
        return pendingPromise;
    }

    pendingPromise = (async () => {
        try {
            const guild = client.guilds?.cache?.get(guildId) || (await client.guilds?.fetch?.(guildId).catch(() => null));
            if (!guild) {
                return cachedUrl || fallback;
            }

            if (guild.vanityURLCode) {
                cachedUrl = `https://discord.gg/${guild.vanityURLCode}`;
                cachedAt = Date.now();
                return cachedUrl;
            }

            const me = guild.members?.me || (await guild.members?.fetchMe?.().catch(() => null));

            if (me?.permissions?.has(PermissionFlagsBits.ManageGuild)) {
                const invites = await guild.invites.fetch().catch(() => null);
                if (invites && invites.size > 0) {
                    const permanent = invites.find((inv) => inv.maxAge === 0 && inv.maxUses === 0);
                    const picked = permanent || invites.first();
                    if (picked?.url) {
                        cachedUrl = picked.url;
                        cachedAt = Date.now();
                        return cachedUrl;
                    }
                }
            }

            const targetChannel =
                guild.systemChannel ||
                guild.rulesChannel ||
                guild.channels?.cache?.find((ch) => {
                    if (!ch || (ch.type !== ChannelType.GuildText && ch.type !== ChannelType.GuildAnnouncement)) {
                        return false;
                    }
                    if (!me) return false;
                    const perms = ch.permissionsFor(me);
                    return perms?.has(PermissionFlagsBits.ViewChannel) && perms?.has(PermissionFlagsBits.CreateInstantInvite);
                });

            if (targetChannel && me) {
                const perms = targetChannel.permissionsFor(me);
                if (perms?.has(PermissionFlagsBits.CreateInstantInvite)) {
                    const created = await targetChannel
                        .createInvite({
                            maxAge: 0,
                            maxUses: 0,
                            unique: false,
                            reason: 'Zyuna dynamic support server invite'
                        })
                        .catch(() => null);
                    if (created?.url) {
                        cachedUrl = created.url;
                        cachedAt = Date.now();
                        return cachedUrl;
                    }
                }
            }
        } catch {
            // Fall back cleanly if permissions or API calls fail
        } finally {
            pendingPromise = null;
        }

        return cachedUrl || fallback;
    })();

    return pendingPromise;
}

module.exports = { getSupportServerUrl };
