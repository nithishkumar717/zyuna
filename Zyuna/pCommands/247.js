const { ContainerBuilder, TextDisplayBuilder, MessageFlags, PermissionFlagsBits } = require('discord.js');
const TwentyFourSeven = require('../../database/models/TwentyFourSeven');
const AutoplaySetting = require('../../database/models/AutoplaySetting');
const emojis = require('../emojis.json');

module.exports = {
    name: '247',
    aliases: ['24/7', 'vc247', 'vc24/7', 'stay'],
    description: 'Toggle 24/7 voice channel persistence (on/off)',

    async execute(message, args = []) {
        const { client, member, guild, channel } = message;

        if (!member.permissions.has(PermissionFlagsBits.ManageGuild) && !member.permissions.has(PermissionFlagsBits.Administrator)) {
            const container = new ContainerBuilder()
                .addTextDisplayComponents(
                    new TextDisplayBuilder().setContent(`${emojis.error} You need **Manage Server** or **Administrator** permission to toggle 24/7 mode!`)
                );
            return message.reply({ components: [container], flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 });
        }

        const arg = (args[0] || '').trim().toLowerCase();
        const current = await TwentyFourSeven.getGuild247(guild.id);

        let enable;
        if (['on', 'enable', 'enabled', 'true', '1'].includes(arg)) {
            enable = true;
        } else if (['off', 'disable', 'disabled', 'false', '0'].includes(arg)) {
            enable = false;
        } else {
            enable = !current.enabled;
        }

        if (enable) {
            if (!member.voice.channel) {
                const container = new ContainerBuilder()
                    .addTextDisplayComponents(
                        new TextDisplayBuilder().setContent(`${emojis.error} Join a voice channel first to enable 24/7 mode!`)
                    );
                return message.reply({ components: [container], flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 });
            }

            let player = client.poru.players.get(guild.id);
            if (!player) {
                player = client.poru.createConnection({
                    guildId: guild.id,
                    voiceChannel: member.voice.channel.id,
                    textChannel: channel.id,
                    deaf: true,
                });
                const apSetting = await AutoplaySetting.getGuildSetting(guild.id);
                player.autoplayEnabled = apSetting.enabled;
                player.autoplayLanguage = apSetting.language;
                player._autoplayLoaded = true;
            }

            await TwentyFourSeven.enable247(guild.id, member.voice.channel.id, channel.id);

            const container = new ContainerBuilder()
                .addTextDisplayComponents(
                    new TextDisplayBuilder().setContent(
                        `${emojis.enabled} **24/7 Mode Enabled**\n` +
                        `${emojis.dots} Staying connected in **${member.voice.channel.name}** and auto-reconnecting on restarts.`
                    )
                );
            return message.reply({ components: [container], flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 });
        } else {
            await TwentyFourSeven.disable247(guild.id);
            const container = new ContainerBuilder()
                .addTextDisplayComponents(
                    new TextDisplayBuilder().setContent(
                        `${emojis.disabled} **24/7 Mode Disabled**\n` +
                        `${emojis.dots} The bot will leave automatically after 60 seconds of inactivity.`
                    )
                );
            return message.reply({ components: [container], flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 });
        }
    },
};
