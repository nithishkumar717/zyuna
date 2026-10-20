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

import { 
  BotInfo, 
  BotStatus, 
  GuildSummary, 
  GuildDetails,
  PrefixConfig, 
  DiscordChannel, 
  DiscordRole,
  MusicPlayerState,
  MusicControlAction,
  SafetyConfig,
  SafetyUpdate,
  AlertsConfig,
  AlertsUpdate,
  AdminStats, 
  AdminConfig, 
  AdminConfigUpdate 
} from "@/types/api";

const getBaseUrl = (): string => {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== "undefined") {
    if (!envUrl || (window.location.protocol === "https:" && envUrl.startsWith("http://"))) {
      return "/api/v1";
    }
    return envUrl;
  }
  return process.env.BOT_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
};

const API_KEY = process.env.NEXT_PUBLIC_DASHBOARD_API_KEY;

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit & { next?: { revalidate?: number } } = {}
): Promise<T> {
  const baseUrl = getBaseUrl().replace(/\/+$/, "");
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${cleanEndpoint}`;
  
  const headers = new Headers(options.headers);
  if (API_KEY) {
    headers.set("Authorization", `Bearer ${API_KEY}`);
  }
  headers.set("Content-Type", "application/json");
  try {
    const response = await fetch(url, {
      ...options,
      headers,
      next: options.next || { revalidate: 0 },
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { detail: "An unknown error occurred" };
      }
      console.error(`[API HTTP Error] Status ${response.status} for ${url}:`, errorData);
      throw new ApiError(response.status, errorData.detail || response.statusText);
    }

    return response.json();
  } catch (error) {
    console.error(`[API Network/Fetch Error] Failed to fetch ${url}:`, error);
    throw error;
  }
}

export const api = {
  // Bot Status & Info
  getBotStatus: () => request<BotStatus>("/bot/status"),
  getBotInfo: () => request<BotInfo>("/bot/info"),

  // Guilds
  listGuilds: () => request<GuildSummary[]>("/guilds/"),
  getGuildDetails: (guildId: string) => request<GuildDetails>(`/guilds/${guildId}`),
  getChannels: (guildId: string) => request<DiscordChannel[]>(`/guilds/${guildId}/channels`),
  getRoles: (guildId: string) => request<DiscordRole[]>(`/guilds/${guildId}/roles`),
  
  // Prefix
  getPrefix: (guildId: string) => request<PrefixConfig>(`/guilds/${guildId}/prefix`),
  updatePrefix: (guildId: string, prefix: string) => 
    request<{ status: string; new_prefix: string }>(`/guilds/${guildId}/prefix`, {
      method: "POST",
      body: JSON.stringify({ prefix }),
    }),

  // Studio Audio
  getMusicState: (guildId: string) => request<MusicPlayerState>(`/guilds/${guildId}/music`),
  controlMusic: (guildId: string, data: MusicControlAction) =>
    request<{ status: string; detail?: string }>(`/guilds/${guildId}/music/control`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Chat Safety & Moderation
  getSafetyConfig: (guildId: string) => request<SafetyConfig>(`/guilds/${guildId}/safety`),
  updateSafetyConfig: (guildId: string, data: SafetyUpdate) =>
    request<{ status: string }>(`/guilds/${guildId}/safety`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  // Social Stream Alerts
  getAlertsConfig: (guildId: string) => request<AlertsConfig>(`/guilds/${guildId}/alerts`),
  updateAlertsConfig: (guildId: string, data: AlertsUpdate) =>
    request<{ status: string }>(`/guilds/${guildId}/alerts`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  // Admin Telemetry & Control
  getAdminStats: () => request<AdminStats>("/admin/stats"),
  getAdminConfig: () => request<AdminConfig>("/admin/config"),
  updateAdminConfig: (data: AdminConfigUpdate) => 
    request<{ status: string }>("/admin/config", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};
