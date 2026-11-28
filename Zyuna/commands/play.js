const { SlashCommandBuilder, ContainerBuilder, TextDisplayBuilder, SeparatorBuilder, SeparatorSpacingSize, MessageFlags } = require('discord.js');
const { formatDuration, validatePlayQuery } = require('../helpers/musicHelpers');
const { hexToDecimal } = require('../helpers/colorHelper');
const { isMusicTrackUrl, resolveMusicQuery } = require('../helpers/musicTrackResolver');
const config = require('../config');
const emojis = require('../emojis.json');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('play')
        .setDescription('Play a song or add it to the queue')
        .addStringOption(option =>
            option.setName('search')
                .setDescription('Song title, Spotify playlist URL, or JioSaavn URL')
                .setRequired(true)
                .setAutocomplete(true)
        ),
    
    async autocomplete(interaction) {
        const { client } = interaction;
        const focusedValue = interaction.options.getFocused();

        if (/^https?:\/\/open\.spotify\.com\/playlist\/[a-zA-Z0-9]+/i.test(focusedValue.trim())) {
            const truncatedUrl = focusedValue.length > 60 ? focusedValue.slice(0, 57) + '...' : focusedValue;
            return interaction.respond([{ 
                name: `Play Spotify Playlist: ${truncatedUrl}`, 
                value: focusedValue 
            }]);
        } else if (/^https?:\/\/(?:www\.)?jiosaavn\.com\//i.test(focusedValue.trim())) {
            const truncatedUrl = focusedValue.length > 60 ? focusedValue.slice(0, 57) + '...' : focusedValue;
            return interaction.respond([{ 
                name: `Play JioSaavn: ${truncatedUrl}`, 
                value: focusedValue 
            }]);
        } else if (isMusicTrackUrl(focusedValue.trim())) {
            const truncatedUrl = focusedValue.length > 60 ? focusedValue.slice(0, 57) + '...' : focusedValue;
            return interaction.respond([{ 
                name: `Play Yuna Archive: ${truncatedUrl}`, 
                value: focusedValue 
            }]);
        } else if (/^https?:\/\//i.test(focusedValue.trim())) {
            return interaction.respond([{ 
                name: 'Unsupported URL (use direct search, Spotify playlist, or JioSaavn URL)', 
                value: focusedValue 
            }]);
        }

        if (!client._musicAutocompleteCache) client._musicAutocompleteCache = new Map();
        const searchCache = client._musicAutocompleteCache;

        if (searchCache.has(focusedValue)) {
            return interaction.respond(searchCache.get(focusedValue));
        }

        if (!focusedValue || focusedValue.trim().length === 0) {
            return interaction.respond([]);
        }

        if (!client.poru || typeof client.poru.resolve !== 'function') {
            return interaction.respond([]);
        }

        try {
            let source = config.MUSIC.DEFAULT_PLATFORM || 'ytsearch';
            const res = await client.poru.resolve({ query: focusedValue, source: source, requester: interaction.user });
            if (!res || !res.tracks || !Array.isArray(res.tracks) || res.tracks.length === 0) {
                return interaction.respond([]);
            }
            const choices = res.tracks.slice(0, config.MUSIC.AUTOCOMPLETE_LIMIT).map((choice) => ({
                name: `${choice.info.title.length > 85 ? choice.info.title.slice(0, 82) + '…' : choice.info.title} [${formatDuration(choice.info.length)}]`,
                value: choice.info.uri,
            }));
            searchCache.set(focusedValue, choices);
            return interaction.respond(choices);
        } catch (e) {
            return interaction.respond([]);
        }
    },

    async execute(interaction) {
        const { client, member, guild, options, channel } = interaction;
        
        if (!member.voice.channel) {
            const container = new ContainerBuilder()
                .addTextDisplayComponents(
                    new TextDisplayBuilder().setContent(`${emojis.error} You need to be in a voice channel to play music!`)
                );
            return interaction.reply({ 
                components: [container], 
                flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2, 
                ephemeral: true 
            });
        }

        await interaction.deferReply();
        let query = interaction.options.getString('search');

        const queryValidation = validatePlayQuery(query);
        if (!queryValidation.valid) {
            const container = new ContainerBuilder()
                .addTextDisplayComponents(
                    new TextDisplayBuilder().setContent(`${emojis.error} ${queryValidation.message}`)
                );
            return interaction.editReply({
                components: [container],
                flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2
            });
        }
        query = queryValidation.cleanQuery;

        let res;
        try {
            res = await resolveMusicQuery(client, query, interaction.user);
        } catch (e) {
            console.error('Poru resolve error:', e);
            const errMsg = String(e?.message || 'Unknown error').slice(0, 1500);
            const container = new ContainerBuilder()
                .addTextDisplayComponents(
                    new TextDisplayBuilder().setContent(`${emojis.error} Failed to search: ${errMsg}`)
                );
            return interaction.editReply({ 
                components: [container], 
                flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 
            });
        }

        const isSpotifyPlaylist = queryValidation.isSpotifyPlaylist;
        if (isSpotifyPlaylist) {
            if (!res || (res.loadType !== 'PLAYLIST_LOADED' && res.loadType !== 'playlist') || !Array.isArray(res.tracks) || res.tracks.length === 0) {
                const container = new ContainerBuilder()
                    .addTextDisplayComponents(
                        new TextDisplayBuilder().setContent(`${emojis.error} No results found or invalid playlist.`)
                    );
                return interaction.editReply({ 
                    components: [container], 
                    flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 
                });
            }

            const player = client.poru.createConnection({
                guildId: guild.id,
                voiceChannel: member.voice.channel.id,
                textChannel: channel.id,
                deaf: true,
            });

            if (player.autoplayEnabled === undefined) player.autoplayEnabled = false;

            for (const track of res.tracks) {
                track.info.requester = interaction.user;
                player.queue.add(track);
            }

            if (!player.isPlaying && player.isConnected) player.play();

            const container = new ContainerBuilder()
                .addTextDisplayComponents(
                    new TextDisplayBuilder().setContent(
                        `## ${emojis.music} Playlist ${res.playlistInfo?.name || 'Spotify Playlist'}\nAdded **${res.tracks.length}** tracks to the queue!`
                    )
                );
            
            return interaction.editReply({ 
                components: [container], 
                flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 
            });
        }

        if (res.loadType === 'search') {
            const filteredTracks = res.tracks.filter((track) => !track.info.isStream && track.info.length > 70000);
            if (!filteredTracks.length) {
                const container = new ContainerBuilder()
                    .addTextDisplayComponents(
                        new TextDisplayBuilder().setContent(`${emojis.error} No results found (filtered out shorts).`)
                    );
                return interaction.editReply({ 
                    components: [container], 
                    flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 
                });
            }
            res.tracks = filteredTracks;
        }

        if (res.loadType === 'error') {
            const container = new ContainerBuilder()
                .addTextDisplayComponents(
                    new TextDisplayBuilder().setContent(`${emojis.error} Failed to load: ${res.exception?.message || 'Unknown error'}`)
                );
            return interaction.editReply({ 
                components: [container], 
                flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 
            });
        }

        if (res.loadType === 'empty') {
            const container = new ContainerBuilder()
                .addTextDisplayComponents(
                    new TextDisplayBuilder().setContent(`${emojis.error} No results found.`)
                );
            return interaction.editReply({ 
                components: [container], 
                flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 
            });
        }

        const player = client.poru.createConnection({
            guildId: guild.id,
            voiceChannel: member.voice.channel.id,
            textChannel: channel.id,
            deaf: true,
        });

        if (player.autoplayEnabled === undefined) player.autoplayEnabled = false;

        if (res.loadType === 'playlist' || res.loadType === 'PLAYLIST_LOADED') {
            for (const track of res.tracks) {
                track.info.requester = interaction.user;
                player.queue.add(track);
            }

            if (!player.isPlaying && player.isConnected) player.play();

            const container = new ContainerBuilder()
                .addTextDisplayComponents(
                    new TextDisplayBuilder().setContent(
                        `## ${emojis.music} Playlist ${res.playlistInfo?.name || 'Playlist'}\nAdded **${res.tracks.length}** tracks to the queue!`
                    )
                );

            return interaction.editReply({ 
                components: [container], 
                flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 
            });
        } else {
            const track = res.tracks[0];
            track.info.requester = interaction.user;
            player.queue.add(track);

            if (!player.isPlaying && player.isConnected) player.play();

            const container = new ContainerBuilder()
                .addTextDisplayComponents(
                    new TextDisplayBuilder().setContent(
                        `${emojis.success} Added **[${track.info.title}](${track.info.uri})** to the queue!`
                    )
                );

            return interaction.editReply({ 
                components: [container], 
                flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2 
            });
        }
    },
};

