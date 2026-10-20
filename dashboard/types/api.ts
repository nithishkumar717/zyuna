/**
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║                                                                  ║
 * ║   ░█▄░█░█▀▀░█▀▄░█▀▄   ░█░█   ░█░░░▀█▀░█░█░█▀▀                 ║
 * ║   ░█░▀█░█▀▀░█▀▄░█░█   ░▄▀▄   ░█░░░░█░░▀▄▀░█▀▀                 ║
 * ║   ░▀░░▀░▀▀▀░▀░▀░▀▀░   ░▀░▀   ░▀▀▀░▀█▀░░▀░░▀▀▀                 ║
 * ║                                                                  ║
 * ║           © 2026 Nerd X Live — All Rights Reserved              ║
 * ║                                                                  ║
 * ║   discord  ──  https://discord.gg/YzHCx5yQXv                    ║
 * ║   github   ──  https://github.com/nithishkumar717/zyuna         ║
 * ║                                                                  ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

export interface BotInfo {
  name: string;
  id: string | null;
  guilds: number;
  users: number;
  commands: number;
  latency: string;
}

export interface BotStatus {
  user: string;
  id: string | null;
  latency: number;
  guild_count: number;
  user_count: number;
  shards: number | null;
}

export interface GuildSummary {
  id: string;
  name: string;
  icon_url: string | null;
  owner_id: string;
  member_count: number;
}

export interface GuildDetails {
  id: string;
  name: string;
  icon: string | null;
  owner_id: string;
  member_count: number;
  role_count: number;
  channel_count: number;
}

export interface PrefixConfig {
  guild_id: number | string;
  prefix: string;
}

export interface PrefixUpdate {
  prefix: string;
}

export interface DiscordChannel {
  id: string;
  name: string;
  type: number;
}

export interface DiscordRole {
  id: string;
  name: string;
  color: number;
  position: number;
}

// Studio Audio
export interface MusicTrack {
  title: string;
  author: string;
  uri: string;
  duration: number;
  artwork?: string | null;
  requester?: string | null;
}

export interface MusicPlayerState {
  guild_id: string;
  is_connected: boolean;
  is_playing: boolean;
  is_paused: boolean;
  volume: number;
  current_track: MusicTrack | null;
  position: number;
  loop_mode: string;
  filter_preset: string;
  queue: MusicTrack[];
  voice_channel: string | null;
}

export interface MusicControlAction {
  action: "pause" | "resume" | "skip" | "stop" | "set_volume" | "set_filter" | "set_loop";
  value?: string | number;
}

// Chat Safety & Moderation
export interface SafetyConfig {
  guild_id: string;
  blacklisted_words: string[];
  bypass_roles: string[];
  bypass_users: string[];
}

export interface SafetyUpdate {
  add_word?: string;
  remove_word?: string;
  add_bypass_role?: string;
  remove_bypass_role?: string;
}

// Social Alerts
export interface SocialAlertItem {
  id: number;
  type: "youtube" | "twitch";
  role_id: string;
  channel_id: string;
}

export interface AlertsConfig {
  guild_id: string;
  alerts: SocialAlertItem[];
}

export interface AlertsUpdate {
  type: "youtube" | "twitch";
  channel_id: string;
  role_id: string;
}

// System Telemetry & Admin
export interface AdminNodeStatus {
  name: string;
  status: string;
  load: string;
  icon: string;
}

export interface AdminStats {
  total_users: string;
  active_servers: string;
  api_latency: string;
  db_size: string;
  uptime: string;
  cached_events: string;
  nodes: AdminNodeStatus[];
}

export interface AdminConfig {
  maintenance_mode: boolean;
  global_notification: string;
}

export interface AdminConfigUpdate {
  maintenance_mode?: boolean;
  global_notification?: string;
}
