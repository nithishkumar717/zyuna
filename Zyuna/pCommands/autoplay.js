const { ContainerBuilder, TextDisplayBuilder, MessageFlags } = require('discord.js');
const { hasControlPermission } = require('../helpers/musicHelpers');
const { SUPPORTED_LANGUAGES } = require('../helpers/autoplayEngine');
const AutoplaySetting = require('../../database/models/AutoplaySetting');
const emojis = require('../emojis.json');

module.exports = {
    name: 'autoplay',
    aliases: ['ap'],
    description: 'Toggle autoplay or set trending language (e.g. ,autoplay tamil)',

    async execute(message, args = []) {
        const { client, member, guild } = message;
        const player = client.poru.players.get(guild.id);

        if (player) {
            if (!member.voice.channel || member.voice.channel.id !== player.voiceChannel) {
                const container = new ContainerBuilder()
                    .addTextDisplayComponents(new TextDisplayBuilder().setContent(`${emojis.error} You must be in the same voice channel as the bot!`));
                return message.reply({ components: [container], flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 });
            }

            if (!hasControlPermission(message, player)) {
                const container = new ContainerBuilder()
                    .addTextDisplayComponents(new TextDisplayBuilder().setContent(`${emojis.error} Only the requester, admins, or server managers can control the music!`));
                return message.reply({ components: [container], flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 });
            }
        }

        const currentSetting = await AutoplaySetting.getGuildSetting(guild.id);
        const currentEnabled = player && player.autoplayEnabled !== undefined ? player.autoplayEnabled : currentSetting.enabled;

        let nextEnabled = currentEnabled;
        let nextLang = currentSetting.language;

        const tokens = (args || []).map((a) => String(a).trim().toLowerCase()).filter(Boolean);
        let parsedAny = false;

        for (const token of tokens) {
            if (['on', 'enable', 'enabled', 'true'].includes(token)) {
                nextEnabled = true;
                parsedAny = true;
            } else if (['off', 'disable', 'disabled', 'false'].includes(token)) {
                nextEnabled = false;
                parsedAny = true;
            } else if (SUPPORTED_LANGUAGES.includes(token)) {
                nextLang = token;
                nextEnabled = true;
                parsedAny = true;
            }
        }

        if (!parsedAny) {
            nextEnabled = !currentEnabled;
        }

        const saved = await AutoplaySetting.setGuildSetting(guild.id, {
            enabled: nextEnabled,
            language: nextLang,
        });

        if (player) {
            player.autoplayEnabled = saved.enabled;
            player.autoplayLanguage = saved.language;
        }

        const langLabel = saved.language.charAt(0).toUpperCase() + saved.language.slice(1);
        const statusLabel = saved.enabled ? 'Enabled' : 'Disabled';

        const container = new ContainerBuilder()
            .addTextDisplayComponents(
                new TextDisplayBuilder().setContent(
                    `${emojis.autoplay} **Autoplay ${statusLabel}**\n` +
                    `${emojis.dots} **Language:** \`${langLabel}\` *(Latest Trending & New Launches)*\n` +
                    `${emojis.dots} *Tip: Use \`,autoplay <${SUPPORTED_LANGUAGES.join('/')}>\` or \`,autoplay on/off\`*`
                )
            );

        return message.reply({ components: [container], flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 });
    },
};
