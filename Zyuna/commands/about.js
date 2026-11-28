const { 
  SlashCommandBuilder, 
  ContainerBuilder, 
  TextDisplayBuilder,
  SeparatorBuilder,
  MediaGalleryBuilder,
  MediaGalleryItemBuilder,
  ButtonBuilder,
  ButtonStyle,
  ActionRowBuilder,
  MessageFlags,
  SeparatorSpacingSize
} = require("discord.js");
const emojis = require('../emojis.json');
const { getSupportServerUrl } = require('../utils/supportLink');

module.exports = {
  data: new SlashCommandBuilder()
    .setName("about")
    .setDescription("Shows information about Zyuna Music"),
  
  async execute(interaction) {
    const client = interaction.client;
    const container = new ContainerBuilder();

    container.addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `# ${emojis.brand} About Zyuna Music`
      )
    );

    container.addSeparatorComponents(
      new SeparatorBuilder().setDivider(true).setSpacing(SeparatorSpacingSize.Small)
    );

    container.addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `${emojis.music} **Zyuna Music** - A powerful Discord music bot designed to bring high-quality music streaming to your server. Enjoy seamless playback, custom playlists, and a rich set of features to enhance your listening experience.`
      )
    );

    container.addSeparatorComponents(
      new SeparatorBuilder().setSpacing(SeparatorSpacingSize.Small)
    );

    container.addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `**Key Features**\n${emojis.reply} High-quality music streaming\n${emojis.reply} Custom playlists & favorites\n${emojis.reply} Advanced audio filters\n${emojis.reply} Queue management\n${emojis.reply} Lyrics support\n${emojis.reply} Spotify integration`
      )
    );

    container.addSeparatorComponents(
      new SeparatorBuilder().setSpacing(SeparatorSpacingSize.Small)
    );

    container.addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `**Built With**\n${emojis.dots} Discord.js v14\n${emojis.dots} Node.js\n${emojis.dots} Lavalink\n${emojis.dots} SQLite Database`
      )
    );

    container.addSeparatorComponents(
      new SeparatorBuilder().setSpacing(SeparatorSpacingSize.Small)
    );

    container.addMediaGalleryComponents(
      new MediaGalleryBuilder().addItems(
        new MediaGalleryItemBuilder().setURL("https://cdn.discordapp.com/attachments/1557394348310536232/1576169340531769476/YUNA_SMOOTH_BEAT_1536x462_30FPS.gif?ex=6b0bf196&is=6b0aa016&hm=1a1dc8aec8ed3d188265cd1c57d0d686d578c483a346e80d814683003a8b5fde")
      )
    );

    container.addSeparatorComponents(
      new SeparatorBuilder().setDivider(true).setSpacing(SeparatorSpacingSize.Small)
    );

    container.addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `*Developed with ❤️ by Zyuna Development*`
      )
    );

    container.addSeparatorComponents(
      new SeparatorBuilder().setSpacing(SeparatorSpacingSize.Small)
    );

    const supportUrl = await getSupportServerUrl(client);

    container.addActionRowComponents(
      new ActionRowBuilder().addComponents(
        new ButtonBuilder()
          .setURL(`https://discord.com/api/oauth2/authorize?client_id=${client.user.id}&permissions=303600576574&scope=bot%20applications.commands`)
          .setLabel(`Invite Bot`)
          .setStyle(ButtonStyle.Link),

        new ButtonBuilder()
          .setURL(supportUrl)
          .setLabel(`Zyuna Development`)
          .setStyle(ButtonStyle.Link)
      )
    );

    await interaction.reply({
      components: [container],
      flags: MessageFlags.IsComponentsV2,
    });
  }
};

