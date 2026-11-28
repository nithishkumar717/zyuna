const { Events, ContainerBuilder, TextDisplayBuilder, MessageFlags } = require('discord.js');
const TwentyFourSeven = require('../../database/models/TwentyFourSeven');
const AutoplaySetting = require('../../database/models/AutoplaySetting');
const emojis = require('../emojis.json');

const aloneTimeouts = new Map();
const reconnectingGuilds = new Set();

module.exports = {
    name: Events.VoiceStateUpdate,
    async execute(oldState, newState) {
        const client = newState.client || oldState.client;
        const guild = newState.guild;
        const player = client.poru.players.get(guild.id);
        const setting247 = await TwentyFourSeven.getGuild247(guild.id);

        if (newState.id === client.user.id) {
            if (!newState.channelId) {
                if (aloneTimeouts.has(guild.id)) {
                    clearTimeout(aloneTimeouts.get(guild.id));
                    aloneTimeouts.delete(guild.id);
                }

                const wasManual = player?._manualDisconnect;

                if (player) {
                    if (player.updateInterval) clearInterval(player.updateInterval);
                    if (player.buttonCollector) {
                        try { player.buttonCollector.stop('botDisconnected'); } catch {}
                    }
                    if (player.filterCollector) {
                        try { player.filterCollector.stop('botDisconnected'); } catch {}
                    }
                    player.destroy();
                }

                if (setting247.enabled && !wasManual && !reconnectingGuilds.has(guild.id)) {
                    reconnectingGuilds.add(guild.id);
                    setTimeout(async () => {
                        try {
                            const latest = await TwentyFourSeven.getGuild247(guild.id);
                            if (!latest.enabled || !latest.voiceChannelId) return;
                            const vc = guild.channels.cache.get(latest.voiceChannelId);
                            if (!vc || client.poru.players.get(guild.id)) return;

                            const newPlayer = client.poru.createConnection({
                                guildId: guild.id,
                                voiceChannel: latest.voiceChannelId,
                                textChannel: latest.textChannelId || vc.id,
                                deaf: true,
                            });
                            const ap = await AutoplaySetting.getGuildSetting(guild.id);
                            newPlayer.autoplayEnabled = ap.enabled;
                            newPlayer.autoplayLanguage = ap.language;
                            newPlayer._autoplayLoaded = true;
                            console.log(`[24/7] Auto-reconnected to ${vc.name} in ${guild.name}`);
                        } catch (err) {
                            console.error(`[24/7] Auto-reconnect failed in ${guild.id}:`, err.message);
                        } finally {
                            reconnectingGuilds.delete(guild.id);
                        }
                    }, 2500);
                    return;
                }

                if (player && !wasManual) {
                    const channel = client.channels.cache.get(player.textChannel);
                    if (channel) {
                        const container = new ContainerBuilder()
                            .addTextDisplayComponents(
                                new TextDisplayBuilder().setContent(
                                    `${emojis.stop} I was disconnected from the voice channel. Clearing the queue.`
                                )
                            );
                        await channel.send({
                            components: [container],
                            flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2
                        }).catch(() => {});
                    }
                }
                return;
            }

            // If bot was moved to another VC while 24/7 is enabled, persist the new VC
            if (oldState.channelId && newState.channelId !== oldState.channelId && setting247.enabled) {
                await TwentyFourSeven.enable247(guild.id, newState.channelId, setting247.textChannelId);
            }
        }

        if (!player) return;

        // Skip 60s inactivity leave when 24/7 mode is active
        if (setting247.enabled) {
            if (aloneTimeouts.has(guild.id)) {
                clearTimeout(aloneTimeouts.get(guild.id));
                aloneTimeouts.delete(guild.id);
            }
            return;
        }

        const voiceChannel = guild.channels.cache.get(player.voiceChannel);
        if (!voiceChannel) return;

        const members = voiceChannel.members.filter(m => !m.user.bot);

        if (members.size === 0) {
            if (!aloneTimeouts.has(guild.id)) {
                const timeout = setTimeout(async () => {
                    const current247 = await TwentyFourSeven.getGuild247(guild.id);
                    if (current247.enabled) {
                        aloneTimeouts.delete(guild.id);
                        return;
                    }

                    const currentPlayer = client.poru.players.get(guild.id);
                    if (!currentPlayer) {
                        aloneTimeouts.delete(guild.id);
                        return;
                    }

                    const currentVoiceChannel = guild.channels.cache.get(currentPlayer.voiceChannel);
                    if (!currentVoiceChannel) {
                        aloneTimeouts.delete(guild.id);
                        return;
                    }

                    const currentMembers = currentVoiceChannel.members.filter(m => !m.user.bot);
                    if (currentMembers.size === 0) {
                        const channel = client.channels.cache.get(currentPlayer.textChannel);
                        if (channel) {
                            const container = new ContainerBuilder()
                                .addTextDisplayComponents(
                                    new TextDisplayBuilder().setContent(
                                        `${emojis.stop} Left the voice channel due to inactivity. No one was listening.`
                                    )
                                );
                            await channel.send({
                                components: [container],
                                flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2
                            }).catch(() => {});
                        }

                        if (currentPlayer.updateInterval) clearInterval(currentPlayer.updateInterval);
                        if (currentPlayer.buttonCollector) {
                            try { currentPlayer.buttonCollector.stop('aloneInChannel'); } catch {}
                        }
                        if (currentPlayer.filterCollector) {
                            try { currentPlayer.filterCollector.stop('aloneInChannel'); } catch {}
                        }

                        currentPlayer.destroy();
                    }

                    aloneTimeouts.delete(guild.id);
                }, 60000);

                aloneTimeouts.set(guild.id, timeout);
            }
        } else {
            if (aloneTimeouts.has(guild.id)) {
                clearTimeout(aloneTimeouts.get(guild.id));
                aloneTimeouts.delete(guild.id);
            }
        }
    },
};
