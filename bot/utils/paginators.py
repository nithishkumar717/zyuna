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

from __future__ import annotations
import os 
from typing import Any, Optional, List, Dict
import discord
from utils.config import BotName

try:
    from discord.ext import menus
    from discord.ext import commands
except (ImportError, ModuleNotFoundError):
    class _MenusFallback:
        class PageSource:
            pass

        class ListPageSource:
            def __init__(self, entries: list[Any], *, per_page: int = 10):
                self.entries = entries
                self.per_page = per_page

            def is_paginating(self) -> bool:
                return len(self.entries) > self.per_page

            def get_max_pages(self) -> int:
                pages, left_over = divmod(len(self.entries), self.per_page)
                if left_over:
                    pages += 1
                return max(1, pages)

            async def _prepare_once(self):
                pass

            async def get_page(self, page_number: int) -> list[Any]:
                base = page_number * self.per_page
                return self.entries[base:base + self.per_page]

    menus = _MenusFallback()
    from discord.ext import commands

from .paginator import Paginator as EmbedPaginator
from discord.ext.commands import Context, Paginator as CmdPaginator
from typing import Any, List


class FieldPagePaginator(menus.ListPageSource):

    def __init__(self,
                 entries: list[tuple[Any, Any]],
                 *,
                 per_page: int = 10,
                 inline: bool = False,
                 **kwargs) -> None:
        super().__init__(entries, per_page=per_page)
        self.embed: discord.Embed = discord.Embed(
            title=kwargs.get('title'),
            description=kwargs.get('description'),
            color=0xFF0000)
        self.inline: bool = inline

    async def format_page(self, menu: EmbedPaginator,
                          entries: list[tuple[Any, Any]]) -> discord.Embed:
        self.embed.clear_fields()

        for key, value in entries:
            self.embed.add_field(name=key, value=value, inline=self.inline)

        maximum = self.get_max_pages()
        if maximum > 1:
            text = f'• Page {menu.current_page + 1}/{maximum} | Requested by {menu.ctx.author.display_name}'
            self.embed.set_footer(
                text=text,
                icon_url=menu.ctx.me.display_avatar.url if hasattr(menu, "ctx") and hasattr(menu.ctx, "me") else None
            )
        return self.embed


class TextPaginator(menus.ListPageSource):

    def __init__(self, text, *, prefix='```', suffix='```', max_size=2000):
        pages = CmdPaginator(prefix=prefix,
                             suffix=suffix,
                             max_size=max_size - 200)
        for line in text.split('\n'):
            pages.add_line(line)

        super().__init__(entries=pages.pages, per_page=1)

    async def format_page(self, menu, content):
        maximum = self.get_max_pages()
        if maximum > 1:
            return f'{content} {BotName} • Page {menu.current_page + 1}/{maximum}'
        return content


class DescriptionEmbedPaginator(menus.ListPageSource):

    def __init__(self,
                 entries: list[Any],
                 *,
                 per_page: int = 10,
                 **kwargs) -> None:
        super().__init__(entries, per_page=per_page)
        self.embed: discord.Embed = discord.Embed(
            title=kwargs.get('title'),
            color=0xFF0000,
        )

    async def format_page(self, menu: EmbedPaginator,
                          entries: list[tuple[Any, Any]]) -> discord.Embed:
        self.embed.clear_fields()

        self.embed.description = '\n'.join(entries)
        maximum = self.get_max_pages()
        if maximum > 1:
            text = f'• Page {menu.current_page + 1}/{maximum} | Requested by {menu.ctx.author.display_name}'
            self.embed.set_footer(
                text=text,
                icon_url=menu.ctx.me.display_avatar.url if hasattr(menu, "ctx") and hasattr(menu.ctx, "me") else None
            )

        return self.embed
