
const {
  Events,
  ContainerBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  MessageFlags,
  MediaGalleryBuilder,
  MediaGalleryItemBuilder,
  SeparatorSpacingSize,
} = require("discord.js");
const emojis = require('../emojis.json');
const { getSupportServerUrl } = require('../utils/supportLink');

module.exports = {
  name: Events.MessageCreate,
  async execute(message, client) {
    if (message.author.bot) return;
    if (!message.guild) return;
    
    
    if (!message.mentions.users.has(client.user.id)) return;
    if (message.type === 19) return; 
    
    const supportUrl = await getSupportServerUrl(client);
    const container = new ContainerBuilder();
    
    container.addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `# ${emojis.brand} Hey there!\n\n${emojis.dots} I'm **${client.user.username}** - Your music companion\n${emojis.dots} Use \`/help\` to explore all my commands\n${emojis.dots} Need support? Join our [server](${supportUrl})`
      )
    );
    
    container.addSeparatorComponents(new SeparatorBuilder());
    
    container.addMediaGalleryComponents(
      new MediaGalleryBuilder().addItems(
        new MediaGalleryItemBuilder().setURL(
          "https://cdn.discordapp.com/attachments/1557394348310536232/1576169340531769476/YUNA_SMOOTH_BEAT_1536x462_30FPS.gif?ex=6b0bf196&is=6b0aa016&hm=1a1dc8aec8ed3d188265cd1c57d0d686d578c483a346e80d814683003a8b5fde"
        )
      )
    );
    
    container.addSeparatorComponents(
      new SeparatorBuilder().setDivider(true).setSpacing(SeparatorSpacingSize.Small)
    );
    
    await message.reply({
      components: [container],
      flags: MessageFlags.IsPersistent | MessageFlags.IsComponentsV2,
    });
  },
};

