# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                  ║
# ║   ░█▄░█░█▀▀░█▀▄░█▀▄   ░█░█   ░█░░░▀█▀░█░█░█▀▀                 ║
# ║   ░█░▀█░█▀▀░█▀▄░█░█   ░▄▀▄   ░█░░░░█░░▀▄▀░█▀▀                 ║
# ║   ░▀░░▀░▀▀▀░▀░▀░▀▀░   ░▀░▀   ░▀▀▀░▀█▀░░▀░░▀▀▀                 ║
# ║                                                                  ║
# ║            © 2026 Nerd X Live — All Rights Reserved             ║
# ║                                                                  ║
# ║   discord  ──  https://discord.gg/YzHCx5yQXv                    ║
# ║   github   ──  https://github.com/nithishkumar717/zyuna         ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

"""
Next-generation Discord Components V2 (CV2) interactive Help System.
Features:
- Premium Neon Crimson Accent Container styling
- Organized Multi-Tier Select Menus (Core Systems vs Community & Extra Modules)
- Fast-action Navigation Bar (Overview, Prev, Next, Close)
- One-Click Quick Links (Dashboard, Support Server)
- Clean, parsed command matrices with inline pills and syntax
- Real-time responsive pagination and user-lock protection
"""

import discord
import re
from typing import List, Dict, Any, Optional
from discord.ui import LayoutView, TextDisplay, Separator, ActionRow, Button, Select
from utils.cv2 import build_container
from utils.config import serverLink, websiteLink, BotName, BRAND_NAME

# Vibrant Neon Crimson Accent for Zyuna CV2 Container
ACCENT_COLOR = 0xFF2A4D

CORE_LABELS = {
    "Music Commands", "Verification Commands", "Ticket",
    "Welcomer Commands", "Joindm"
}


def clean_command_block(raw_text: str, prefix: str = ">") -> str:
    """Format raw comma-separated command dumps into clean modern pill sections."""
    lines = raw_text.strip().split("\n")
    formatted_sections = []
    
    current_title = None
    current_cmds = []

    def flush_section():
        nonlocal current_title, current_cmds
        if current_cmds:
            pills = []
            for cmd in current_cmds:
                clean_cmd = cmd.strip().strip("`").strip()
                if not clean_cmd:
                    continue
                if not clean_cmd.startswith(prefix):
                    clean_cmd = f"{prefix}{clean_cmd}"
                pills.append(f"`{clean_cmd}`")
            if pills:
                body = " • ".join(pills)
                if current_title:
                    formatted_sections.append(f"### {current_title}\n{body}")
                else:
                    formatted_sections.append(body)
        current_title = None
        current_cmds = []

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        # Section header detection (e.g. __**Blacklistword Commands**__)
        if line_str.startswith("__**") or line_str.startswith("**__") or line_str.startswith("###"):
            flush_section()
            clean_title = re.sub(r"[_*#]", "", line_str).strip()
            current_title = f"⚙️ {clean_title}" if not clean_title.startswith(("⚙️", "🛡️", "⚔️", "📌", "📜")) else clean_title
        elif "," in line_str or "`" in line_str:
            parts = line_str.split(",")
            current_cmds.extend(parts)
        else:
            if current_cmds:
                flush_section()
            formatted_sections.append(f"> {line_str}")

    flush_section()
    return "\n\n".join(formatted_sections) if formatted_sections else raw_text


class CategorySelect(Select):
    """Interactive category selector dropdown."""
    def __init__(self, ctx, options: List[discord.SelectOption], placeholder: str = "Select a Category"):
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options[:25]
        )
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                f"❌ Only {self.ctx.author.mention} can interact with this help session.",
                ephemeral=True
            )
        
        selected = self.values[0]
        page_idx = getattr(self.view, "label_to_page", {}).get(selected, 0)
        await self.view.set_page(page_idx, interaction)


class View(LayoutView):
    """
    Premium Discord Components V2 (CV2) Help View.
    Renders modular pages, category dropdowns, and navigation controls.
    """
    def __init__(self, mapping: dict, ctx, homeembed, ui: int = 2):
        super().__init__(timeout=300)
        self.mapping = mapping
        self.ctx = ctx
        self.index = 0
        self.current_page = 0
        self.ui = ui
        self.prefix = getattr(ctx, "prefix", ">") or ">"

        self.label_to_page: Dict[str, int] = {}
        self.core_options: List[discord.SelectOption] = []
        self.extra_options: List[discord.SelectOption] = []
        self.pages: List[Dict[str, Any]] = []

        self.gen_pages(homeembed)
        self.total_pages = len(self.pages)
        self._rebuild()

    def _rebuild(self):
        self.clear_items()
        page = self.pages[self.index]
        page_num = self.index + 1
        total = self.total_pages

        items = []

        # 1. Header Title
        if page.get("title"):
            items.append(TextDisplay(f"{page['title']}"))

        # 2. Description Box
        if page.get("description"):
            if items:
                items.append(Separator(visible=True))
            items.append(TextDisplay(page["description"]))

        # 3. Formatted Command Fields
        for name, value in page.get("fields", []):
            items.append(Separator(visible=True))
            if name.startswith("###") or name.startswith("#"):
                items.append(TextDisplay(f"{name}\n{value}"))
            else:
                items.append(TextDisplay(f"### {name}\n{value}"))

        # 4. Status Footer
        footer_text = page.get("footer") or f"Page {page_num} of {total} • Requested by: {self.ctx.author.display_name}"
        items.append(Separator(visible=True))
        items.append(TextDisplay(f"-# {footer_text}"))

        # 5. ActionRow 1: Navigation Controls
        is_first = (self.index == 0)
        is_last = (self.index >= total - 1)

        home_btn = Button(label="Overview", emoji="🏠", style=discord.ButtonStyle.primary, disabled=is_first)
        prev_btn = Button(label="Prev", emoji="◀️", style=discord.ButtonStyle.secondary, disabled=is_first)
        next_btn = Button(label="Next", emoji="▶️", style=discord.ButtonStyle.secondary, disabled=is_last)
        close_btn = Button(label="Close", emoji="🗑️", style=discord.ButtonStyle.danger)

        home_btn.callback = self._home_cb
        prev_btn.callback = self._prev_cb
        next_btn.callback = self._next_cb
        close_btn.callback = self._close_cb

        items.append(ActionRow(home_btn, prev_btn, next_btn, close_btn))

        # 6. ActionRow 2: Quick Links
        dash_url = websiteLink or "https://zyuna.vercel.app"
        support_url = serverLink or "https://discord.gg/YzHCx5yQXv"
        dash_btn = Button(label="Dashboard", emoji="🌐", url=dash_url, style=discord.ButtonStyle.link)
        support_btn = Button(label="Support Server", emoji="💬", url=support_url, style=discord.ButtonStyle.link)
        items.append(ActionRow(dash_btn, support_btn))

        # 7. ActionRow 3 & 4: Dropdowns
        if self.core_options:
            items.append(ActionRow(CategorySelect(ctx=self.ctx, options=self.core_options, placeholder="🛡️ Core Systems & Defense Modules...")))
        if self.extra_options:
            items.append(ActionRow(CategorySelect(ctx=self.ctx, options=self.extra_options, placeholder="⚡ Community & Extra Features...")))

        # 8. Assemble CV2 Container with Accent Color
        container = build_container(*items, accent_color=ACCENT_COLOR)
        self.add_item(container)

    async def _check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                f"❌ Only {self.ctx.author.mention} can interact with this help session.",
                ephemeral=True
            )
            return False
        return True

    async def _home_cb(self, interaction: discord.Interaction):
        if await self._check(interaction):
            await self.set_page(0, interaction)

    async def _prev_cb(self, interaction: discord.Interaction):
        if await self._check(interaction):
            new_idx = self.index - 1 if self.index > 0 else self.total_pages - 1
            await self.set_page(new_idx, interaction)

    async def _next_cb(self, interaction: discord.Interaction):
        if await self._check(interaction):
            new_idx = self.index + 1 if self.index < self.total_pages - 1 else 0
            await self.set_page(new_idx, interaction)

    async def _close_cb(self, interaction: discord.Interaction):
        if await self._check(interaction):
            await interaction.response.defer()
            try:
                await interaction.delete_original_response()
            except Exception:
                pass

    def get_cogs(self):
        return list(self.mapping.keys())

    def gen_pages(self, homeembed):
        self.pages = []
        self.label_to_page = {}
        used_labels = set()
        core_list: List[discord.SelectOption] = []
        extra_list: List[discord.SelectOption] = []

        # Page 0: Home Overview
        if hasattr(homeembed, "_title"):
            title = homeembed._title
            desc = homeembed._description
            fields = list(homeembed._fields) if hasattr(homeembed, "_fields") else []
        else:
            title = getattr(homeembed, "title", "") or ""
            desc = getattr(homeembed, "description", "") or ""
            fields = [(f.name, f.value) for f in homeembed.fields] if hasattr(homeembed, "fields") and homeembed.fields else []

        self.pages.append({
            "title": title or f"# ✨ {BRAND_NAME} System Operations • Command Center",
            "description": desc,
            "fields": fields,
            "footer": None
        })
        self.label_to_page["Home"] = 0
        used_labels.add("Home")

        # Build Category Pages
        for cog in self.get_cogs():
            if cog.__class__.__name__ in ["Roleplay", "Help"]:
                continue
            if not hasattr(cog, "help_custom"):
                continue

            try:
                emoji, label, description = cog.help_custom()
            except Exception:
                continue

            original_label = label
            counter = 1
            while label in used_labels:
                label = f"{original_label} {counter}"
                counter += 1
            used_labels.add(label)

            formatted_sections = []
            for cmd in cog.get_commands():
                raw_help = cmd.help or ""
                if raw_help:
                    formatted = clean_command_block(raw_help, prefix=self.prefix)
                    clean_name = cmd.name.strip("_").replace("_", " ").title()
                    if clean_name.lower() in ["antinuke", "automod", "general", "extra"]:
                        clean_name = f"{clean_name} Controls"
                    formatted_sections.append((clean_name, formatted))
                else:
                    params = ""
                    for param in cmd.clean_params:
                        if param not in ["self", "ctx"]:
                            params += f" <{param}>"
                    formatted_sections.append((f"`{self.prefix}{cmd.name}{params}`", cmd.short_doc or "No description provided."))

            page_index = len(self.pages)
            self.label_to_page[label] = page_index

            select_desc = (description or "")[:95]
            option = discord.SelectOption(label=label, emoji=emoji, description=select_desc)

            if original_label in CORE_LABELS:
                core_list.append(option)
            else:
                extra_list.append(option)

            self.pages.append({
                "title": f"# {emoji} {original_label}",
                "description": f"> {description}\n\n-# 💡 **Pro Tip:** Type `{self.prefix}help <command>` for detailed syntax, subcommands & permissions.",
                "fields": formatted_sections,
                "footer": None
            })

        self.core_options = core_list
        self.extra_options = extra_list

    async def set_page(self, page: int, interaction: discord.Interaction):
        self.index = max(0, min(page, self.total_pages - 1))
        self.current_page = self.index
        self._rebuild()
        await interaction.response.edit_message(view=self)