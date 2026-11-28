const { SlashCommandBuilder, ContainerBuilder, TextDisplayBuilder, MessageFlags } = require('discord.js');
const { hasControlPermission } = require('../helpers/musicHelpers');
const { SUPPORTED_LANGUAGES } = require('../helpers/autoplayEngine');
const AutoplaySetting = require('../../database/models/AutoplaySetting');
const emojis = require('../emojis.json');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('autoplay')
        .setDescription('Configure autoplay and trending language preferences')
        .addStringOption((option) =>
            option
                .setName('language')
                .setDescription('Preferred language for trending & new launch autoplay')
                .setRequired(false)
                .addChoices(
                    { name: 'Auto (Detect from song)', value: 'auto' },
                    { name: 'Tamil', value: 'tamil' },
                    { name: 'Hindi', value: 'hindi' },
                    { name: 'Malayalam', value: 'malayalam' },
                    { name: 'Telugu', value: 'telugu' },
                    { name: 'Kannada', value: 'kannada' },
                    { name: 'Punjabi', value: 'punjabi' },
                    { name: 'English', value: 'english' }
                )
        )
        .addBooleanOption((option) =>
            option
                .setName('enabled')
                .setDescription('Turn autoplay ON or OFF (leave empty to toggle)')
                .setRequired(false)
        ),

    async execute(interaction) {
        const { client, member, guild } = interaction;
        const requestedLang = interaction.options.getString('language');
        const requestedEnabled = interaction.options.getBoolean('enabled');
        const player = client.poru.players.get(guild.id);

        if (player) {
            if (!member.voice.channel || member.voice.channel.id !== player.voiceChannel) {
                const container = new ContainerBuilder()
                    .addTextDisplayComponents(new TextDisplayBuilder().setContent(`${emojis.error} You must be in the same voice channel as the bot!`));
                return interaction.reply({ components: [container], flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2, ephemeral: true });
            }

            if (!hasControlPermission(interaction, player)) {
                const container = new ContainerBuilder()
                    .addTextDisplayComponents(new TextDisplayBuilder().setContent(`${emojis.error} Only the requester, admins, or server managers can control the music!`));
                return interaction.reply({ components: [container], flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2, ephemeral: true });
            }
        }

        const currentSetting = await AutoplaySetting.getGuildSetting(guild.id);
        const currentEnabled = player && player.autoplayEnabled !== undefined ? player.autoplayEnabled : currentSetting.enabled;

        let nextEnabled = currentEnabled;
        if (requestedEnabled !== null) {
            nextEnabled = requestedEnabled;
        } else if (!requestedLang) {
            nextEnabled = !currentEnabled;
        } else {
            // Setting a language automatically enables autoplay if it wasn't explicitly turned off
            nextEnabled = true;
        }

        const nextLang = requestedLang && SUPPORTED_LANGUAGES.includes(requestedLang.toLowerCase())
            ? requestedLang.toLowerCase()
            : currentSetting.language;

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
                    `${emojis.dots} **Language:** \`${langLabel}\` *(Latest Trending & New Launches)*`
                )
            );

        return interaction.reply({ components: [container], flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 });
    },
};
