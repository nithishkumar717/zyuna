"use client";

import React, { useState } from 'react';
import { 
  Search, 
  ChevronDown
} from 'lucide-react';

interface CommandsViewProps {
  onOpenLogin?: () => void;
}

interface CommandItem {
  name: string;
  aliases?: string;
  description: string;
  usage: string;
}

export const CommandsView: React.FC<CommandsViewProps> = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('Studio Audio');
  const [expandedCommand, setExpandedCommand] = useState<string | null>('play');

  const categories = [
    { name: 'Studio Audio', description: 'Wavelink music player, Yuna UI card generator, AI selections & queue controls.', count: 16 },
    { name: 'Audio FX Filters', description: '15+ real-time hardware-accelerated DSP audio equalizer filters.', count: 11 },
    { name: 'Server Utilities', description: 'Interactive embed builder, Hinglish translator, satellite map viewer & webhooks.', count: 7 },
    { name: 'Social Stream Alerts', description: 'Automated YouTube video and Twitch livestream push alert webhooks.', count: 4 },
    { name: 'Chat Safety & Stats', description: 'Word blacklist filter, bypass management, staff emergency dispatch & message tracking.', count: 9 },
    { name: 'Mini-Games', description: 'High-speed reaction time mini-game.', count: 1 },
    { name: 'System Telemetry', description: 'Cluster statistics, latency checks, bot status, and official links.', count: 5 }
  ];

  const commandsData: Record<string, CommandItem[]> = {
    'Studio Audio': [
      { name: 'play', aliases: 'p', description: 'Plays a track or playlist from YouTube, Spotify, or SoundCloud with automatic Yuna player card.', usage: '>play <query/url>' },
      { name: 'pause', aliases: 'None', description: 'Pauses currently playing studio audio stream.', usage: '>pause' },
      { name: 'resume', aliases: 'None', description: 'Resumes playback of paused audio stream.', usage: '>resume' },
      { name: 'skip', aliases: 's', description: 'Skips current track and starts playing the next song in queue.', usage: '>skip' },
      { name: 'stop', aliases: 'disconnect, dc', description: 'Stops playback, clears queue, and disconnects voice client.', usage: '>stop' },
      { name: 'queue', aliases: 'q', description: 'Displays paginated list of upcoming songs in the server queue.', usage: '>queue' },
      { name: 'nowplaying', aliases: 'np', description: 'Re-renders the dynamic Yuna music card and current track status.', usage: '>nowplaying' },
      { name: 'volume', aliases: 'vol', description: 'Adjusts playback volume between 0% and 150%.', usage: '>volume <1-150>' },
      { name: 'seek', aliases: 'None', description: 'Seeks to a specific timestamp in the current track.', usage: '>seek <mm:ss>' },
      { name: 'shuffle', aliases: 'shuff', description: 'Randomizes the order of all tracks currently queued.', usage: '>shuffle' },
      { name: 'loop', aliases: 'repeat', description: 'Toggles loop mode: Off, Current Track, or Whole Queue.', usage: '>loop <track/queue/off>' },
      { name: 'autoplay', aliases: 'ap', description: 'Toggles automatic recommendation queueing when queue finishes.', usage: '>autoplay' },
      { name: 'join', aliases: 'connect', description: 'Connects bot to your current voice channel.', usage: '>join' },
      { name: 'leave', aliases: 'dc', description: 'Leaves the active voice channel.', usage: '>leave' },
      { name: 'spotify', aliases: 'sp', description: 'Generates a rich canvas card showing what a user is listening to on Spotify.', usage: '>spotify [@user]' },
      { name: 'autonp', aliases: 'None', description: 'Configures automated Now Playing song alert messages in voice text channels.', usage: '>autonp <add/remove/list>' }
    ],
    'Audio FX Filters': [
      { name: '8d', aliases: 'None', description: 'Simulates 8-dimensional rotating binaural surround sound audio.', usage: '>8d' },
      { name: 'bassboost', aliases: 'bb', description: 'Boosts low frequencies for punchy bass.', usage: '>bassboost [soft/medium/hard/extreme]' },
      { name: 'nightcore', aliases: 'nc', description: 'Increases pitch and tempo for a high-energy anime style remix.', usage: '>nightcore' },
      { name: 'vaporwave', aliases: 'vw', description: 'Lowers pitch and tempo for a nostalgic, slowed-and-reverb sound.', usage: '>vaporwave' },
      { name: 'pop', aliases: 'None', description: 'Optimizes audio frequencies for vocals and pop music tracks.', usage: '>pop' },
      { name: 'soft', aliases: 'None', description: 'Applies gentle filtering to create relaxing, warm background music.', usage: '>soft' },
      { name: 'treblebass', aliases: 'tb', description: 'Simultaneously boosts high treble and deep low frequencies.', usage: '>treblebass' },
      { name: 'karaoke', aliases: 'None', description: 'Suppresses center-channel frequencies to reduce lead vocals.', usage: '>karaoke' },
      { name: 'vibrato', aliases: 'None', description: 'Applies pulsating frequency pitch modulation to the track.', usage: '>vibrato' },
      { name: 'tremolo', aliases: 'None', description: 'Applies rapid volume amplitude modulation.', usage: '>tremolo' },
      { name: 'clearfilters', aliases: 'resetfilters, flat', description: 'Clears all active DSP audio filters back to standard studio flat output.', usage: '>clearfilters' }
    ],
    'Server Utilities': [
      { name: 'embed', aliases: 'None', description: 'Interactive visual modal embed builder with custom titles, colors, images, and buttons.', usage: '>embed' },
      { name: 'hinglish', aliases: 'h2e', description: 'Translates colloquial Hinglish text to clear natural English.', usage: '>hinglish <text>' },
      { name: 'map', aliases: 'None', description: 'Fetches high-resolution satellite imagery or terrain map for a location.', usage: '>map <location>' },
      { name: 'search_youtube', aliases: 'ytsearch', description: 'Searches YouTube and returns top video results with thumbnails.', usage: '>search_youtube <query>' },
      { name: 'create_hook', aliases: 'mkhook', description: 'Creates a webhook in the designated channel.', usage: '>create_hook <#channel> <name>' },
      { name: 'delete_hook', aliases: 'rmhook', description: 'Deletes a webhook by its ID.', usage: '>delete_hook <hook_id>' },
      { name: 'list_hooks', aliases: 'hooks', description: 'Lists all active webhooks across the guild.', usage: '>list_hooks' }
    ],
    'Social Stream Alerts': [
      { name: 'setnotif youtube', aliases: 'None', description: 'Sets up instant webhook announcement for YouTube video uploads.', usage: '>setnotif youtube <@role> <#channel>' },
      { name: 'setnotif twitch', aliases: 'None', description: 'Sets up automated go-live announcement for Twitch streamers.', usage: '>setnotif twitch <@role> <#channel>' },
      { name: 'setnotif list', aliases: 'None', description: 'Displays currently configured notification streams.', usage: '>setnotif list' },
      { name: 'setnotif reset', aliases: 'None', description: 'Removes all stream notification channels and alert configs.', usage: '>setnotif reset' }
    ],
    'Chat Safety & Stats': [
      { name: 'blacklistword add', aliases: 'blword add', description: 'Adds forbidden word or phrase to automatic chat filter.', usage: '>blacklistword add <word>' },
      { name: 'blacklistword remove', aliases: 'blword remove', description: 'Removes a word from server blacklist.', usage: '>blacklistword remove <word>' },
      { name: 'blacklistword config', aliases: 'blword list', description: 'Lists all blacklisted terms configured for this server.', usage: '>blacklistword config' },
      { name: 'blacklistword reset', aliases: 'blword reset', description: 'Clears all blacklisted terms for this server.', usage: '>blacklistword reset' },
      { name: 'blacklistword bypass', aliases: 'blword bypass', description: 'Manages role exemptions from blacklist word filtering.', usage: '>blacklistword bypass <add/remove/list>' },
      { name: 'dm_staff', aliases: 'modmail', description: 'Sends a direct message alert to staff and administrators.', usage: '>dm_staff <message>' },
      { name: 'messages', aliases: 'msgstats', description: 'Shows today\'s and total message counts for a member.', usage: '>messages [@user]' },
      { name: 'addmessages', aliases: 'addmsg', description: 'Manually credits message count to a user.', usage: '>addmessages <@user> <amount>' },
      { name: 'removemessages', aliases: 'rmmsg', description: 'Deducts message count from a user.', usage: '>removemessages <@user> <amount>' }
    ],
    'Mini-Games': [
      { name: 'reaction', aliases: 'reactgame', description: 'Tests user reflexes in a high-speed reaction challenge.', usage: '>reaction' }
    ],
    'System Telemetry': [
      { name: 'help', aliases: 'h', description: 'Opens the interactive CV2 department help menu.', usage: '>help [category]' },
      { name: 'stats', aliases: 'bi, botinfo', description: 'Displays cluster hardware metrics, memory usage, and guild counts.', usage: '>stats' },
      { name: 'status', aliases: 'ping, latency', description: 'Checks WebSocket latency and gateway responsiveness.', usage: '>status' },
      { name: 'invite', aliases: 'None', description: 'Generates official bot invite link with recommended permissions.', usage: '>invite' },
      { name: 'gitpull', aliases: 'None', description: 'Checks for updates and hot-reloads the codebase from GitHub.', usage: '>gitpull' }
    ]
  };

  const currentCategoryData = commandsData[selectedCategory] || [];

  const filteredCommands = currentCategoryData.filter(cmd => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return cmd.name.toLowerCase().includes(query) || 
           cmd.description.toLowerCase().includes(query) ||
           (cmd.aliases && cmd.aliases.toLowerCase().includes(query));
  });

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Category Pills */}
      <div className="flex flex-wrap gap-2 mb-8 justify-center">
        {categories.map((cat) => (
          <button
            key={cat.name}
            onClick={() => setSelectedCategory(cat.name)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
              selectedCategory === cat.name
                ? 'bg-red-950/40 text-white border-red-500 shadow-lg shadow-red-950/50'
                : 'bg-[#0f1118] text-slate-400 border-slate-800 hover:border-slate-700 hover:text-white'
            }`}
          >
            <span>{cat.name}</span>
            <span className="ml-1.5 opacity-60 text-[10px]">({cat.count})</span>
          </button>
        ))}
      </div>

      {/* Search Input */}
      <div className="relative max-w-xl mx-auto mb-10">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
        <input
          type="text"
          placeholder={`Search ${selectedCategory} commands...`}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-11 pr-4 py-3 bg-[#0f1118] border border-slate-800 rounded-2xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition-all"
        />
      </div>

      {/* Commands List */}
      <div className="space-y-3">
        {filteredCommands.map((cmd) => {
          const isExpanded = expandedCommand === cmd.name;
          return (
            <div 
              key={cmd.name}
              className="bg-[#0f1118] border border-slate-800/80 rounded-2xl overflow-hidden transition-all duration-200"
            >
              <button
                type="button"
                onClick={() => setExpandedCommand(isExpanded ? null : cmd.name)}
                className="w-full px-5 py-3.5 flex items-center justify-between text-left cursor-pointer hover:bg-slate-900/40 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-white font-mono">&gt;{cmd.name}</span>
                </div>
                <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${isExpanded ? 'transform rotate-180 text-red-400' : ''}`} />
              </button>

              {isExpanded && (
                <div className="px-5 pb-5 pt-1 border-t border-slate-800/60 space-y-3 bg-[#0e1017]">
                  {cmd.aliases && cmd.aliases !== 'None' && (
                    <div className="text-xs">
                      <span className="text-slate-400 font-medium">Aliases: </span>
                      <span className="font-mono text-slate-300">{cmd.aliases}</span>
                    </div>
                  )}

                  <div className="text-xs">
                    <span className="text-slate-400 font-medium">Description: </span>
                    <span className="text-slate-300">{cmd.description}</span>
                  </div>

                  <div className="text-xs space-y-1">
                    <span className="text-slate-400 font-medium">Usage:</span>
                    <div className="p-2.5 rounded-lg bg-[#07080c] border border-slate-800 font-mono text-red-400 text-xs">
                      {cmd.usage}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {filteredCommands.length === 0 && (
          <div className="text-center py-12 text-slate-500 text-xs">
            No commands matched your query &ldquo;{searchQuery}&rdquo;.
          </div>
        )}
      </div>

    </div>
  );
};
