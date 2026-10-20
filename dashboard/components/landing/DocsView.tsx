"use client";

import React, { useState } from 'react';
import { 
  BookOpen, 
  Headphones, 
  Sliders, 
  Bell, 
  ShieldCheck, 
  Wrench, 
  RefreshCw, 
  ChevronRight
} from 'lucide-react';

interface DocsViewProps {
  onOpenLogin: () => void;
  onOpenInvite: () => void;
}

export const DocsView: React.FC<DocsViewProps> = ({ onOpenLogin, onOpenInvite }) => {
  const [activeTab, setActiveTab] = useState<string>('getting-started');
  const botName = process.env.NEXT_PUBLIC_BRAND_NAME || "ZYUNA";

  const topics = [
    { id: 'getting-started', title: 'Getting Started', icon: BookOpen },
    { id: 'music', title: 'Studio Audio Engine', icon: Headphones },
    { id: 'filters', title: 'DSP Audio Filters', icon: Sliders },
    { id: 'alerts', title: 'Social Stream Alerts', icon: Bell },
    { id: 'safety', title: 'Chat Safety & Moderation', icon: ShieldCheck },
    { id: 'utilities', title: 'Server Utilities', icon: Wrench },
    { id: 'recovery', title: 'Session Persistence', icon: RefreshCw }
  ];

  return (
    <div className="pt-28 pb-20 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      
      {/* Top Header */}
      <div className="text-center max-w-3xl mx-auto mb-12">
        <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-white font-sans">
          Documentation
        </h1>
        <p className="mt-3 text-sm sm:text-base text-slate-400">
          Complete guide to setting up and optimizing {botName} for your Discord server
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Sidebar Navigation */}
        <div className="lg:col-span-4 space-y-1.5 bg-[#0b0d14] p-3 rounded-2xl border border-slate-800/80 h-fit">
          <span className="px-3 py-2 text-[10px] font-black uppercase tracking-widest text-slate-500 block">
            Navigation Topics
          </span>

          {topics.map((t) => {
            const Icon = t.icon;
            const isSelected = activeTab === t.id;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setActiveTab(t.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  isSelected 
                    ? 'bg-red-500/20 text-red-400 border border-red-500/30' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4" />
                  <span>{t.title}</span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 opacity-60" />
              </button>
            );
          })}

          <div className="pt-4 mt-4 border-t border-slate-800 space-y-2">
            <button
              onClick={onOpenInvite}
              className="w-full py-2 bg-gradient-to-r from-red-600 to-rose-600 text-white text-xs font-bold rounded-lg shadow cursor-pointer font-sans"
            >
              Add {botName} Bot
            </button>
            <button
              onClick={onOpenLogin}
              className="w-full py-2 bg-[#141620] hover:bg-[#1c202e] border border-slate-700 text-slate-200 text-xs font-bold rounded-lg cursor-pointer font-sans"
            >
              Open Dashboard
            </button>
          </div>
        </div>

        {/* Right Content Body */}
        <div className="lg:col-span-8 bg-[#0e1017] border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
          {activeTab === 'getting-started' && (
            <div className="space-y-4">
              <h2 className="text-2xl font-black text-white">Getting Started with {botName}</h2>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                {botName} is engineered to deliver high-fidelity audio, DSP filters, and essential server tools with zero friction.
              </p>

              <div className="space-y-3 pt-2">
                <div className="p-4 rounded-xl bg-[#08090e] border border-slate-800 space-y-1">
                  <span className="text-xs font-bold text-red-400 uppercase">Step 1: Invite Bot</span>
                  <p className="text-xs text-slate-300">
                    Invite {botName} to your server and join a voice channel.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-[#08090e] border border-slate-800 space-y-1">
                  <span className="text-xs font-bold text-red-400 uppercase">Step 2: Stream Music</span>
                  <p className="text-xs text-slate-300">
                    Type <code className="text-amber-300 font-mono text-[11px]">&gt;play &lt;song&gt;</code> to start playback with our custom Yuna UI player card.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-[#08090e] border border-slate-800 space-y-1">
                  <span className="text-xs font-bold text-red-400 uppercase">Step 3: Apply Audio Filters</span>
                  <p className="text-xs text-slate-300">
                    Use <code className="text-amber-300 font-mono text-[11px]">&gt;8d</code>, <code className="text-amber-300 font-mono text-[11px]">&gt;bassboost</code>, or <code className="text-amber-300 font-mono text-[11px]">&gt;nightcore</code> to enhance audio live.
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'music' && (
            <div className="space-y-4">
              <h2 className="text-2xl font-black text-white">Studio Audio Engine</h2>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Integrated with Lavalink/Wavelink v3, featuring dynamic music card rendering, automated playback recovery, AI recommendations, and 4-row interactive CV2 components.
              </p>
              <div className="p-4 rounded-xl bg-[#08090e] border border-slate-800 font-mono text-xs text-red-400 space-y-1">
                <p>&gt;play &lt;song name or link&gt;</p>
                <p>&gt;queue</p>
                <p>&gt;loop track | queue | off</p>
                <p>&gt;autoplay</p>
              </div>
            </div>
          )}

          {activeTab === 'filters' && (
            <div className="space-y-4">
              <h2 className="text-2xl font-black text-white">DSP Audio Equalizer</h2>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Transform any voice channel stream with 15+ real-time hardware audio filters without stream stutter or audio lag.
              </p>
              <div className="p-4 rounded-xl bg-[#08090e] border border-slate-800 font-mono text-xs text-red-400 space-y-1">
                <p>&gt;8d (rotating surround sound)</p>
                <p>&gt;bassboost soft | hard | extreme</p>
                <p>&gt;nightcore | vaporwave</p>
                <p>&gt;clearfilters</p>
              </div>
            </div>
          )}

          {activeTab === 'alerts' && (
            <div className="space-y-4">
              <h2 className="text-2xl font-black text-white">Social Stream Alerts</h2>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Automated background monitors notify your community the second video uploads or Twitch livestreams launch.
              </p>
              <div className="p-4 rounded-xl bg-[#08090e] border border-slate-800 font-mono text-xs text-red-400 space-y-1">
                <p>&gt;setnotif youtube @StreamRole #announcements</p>
                <p>&gt;setnotif twitch @StreamRole #announcements</p>
                <p>&gt;setnotif list</p>
              </div>
            </div>
          )}

          {activeTab === 'safety' && (
            <div className="space-y-4">
              <h2 className="text-2xl font-black text-white">Chat Safety & Staff Dispatch</h2>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Instant keyword blocklist with administrator bypass and a direct staff DM alert channel.
              </p>
              <div className="p-4 rounded-xl bg-[#08090e] border border-slate-800 font-mono text-xs text-red-400 space-y-1">
                <p>&gt;blacklistword add &lt;word&gt;</p>
                <p>&gt;blacklistword bypass add &lt;@role&gt;</p>
                <p>&gt;dm_staff &lt;urgent report&gt;</p>
              </div>
            </div>
          )}

          {activeTab === 'utilities' && (
            <div className="space-y-4">
              <h2 className="text-2xl font-black text-white">Server Utilities</h2>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Visual modal embed designer, natural colloquial Hinglish translator, and interactive satellite imagery.
              </p>
              <div className="p-4 rounded-xl bg-[#08090e] border border-slate-800 font-mono text-xs text-red-400 space-y-1">
                <p>&gt;embed</p>
                <p>&gt;hinglish kya haal chal bhai</p>
                <p>&gt;map Tokyo</p>
              </div>
            </div>
          )}

          {activeTab === 'recovery' && (
            <div className="space-y-4">
              <h2 className="text-2xl font-black text-white">Uninterrupted Session Recovery</h2>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                {botName} persists live playback positions, queued tracks, voice channel sessions, loop modes, and filters across host restarts. Playback seamlessly resumes right where it left off.
              </p>
            </div>
          )}
        </div>

      </div>

    </div>
  );
};
