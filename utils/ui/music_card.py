import io
import time
import math
import asyncio
import urllib.request
import re
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageSequence, ImageChops
import aiohttp
import discord

import os

# Cache for downloaded thumbnails to avoid re-fetching on song transitions
_THUMBNAIL_CACHE: Dict[str, Image.Image] = {}
_MAX_CACHE_SIZE = 60
_UTILS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from concurrent.futures import ThreadPoolExecutor

# In-memory cache for extracted & keyed audio beat animation frames
_AUDIOBEAT_CACHE: Dict[str, Tuple[List[Image.Image], List[int]]] = {}

# Performance caches to avoid repeated allocations and decoding
_PLATFORM_ICON_CACHE: Dict[Tuple[str, int], Image.Image] = {}
_FADE_MASK_CACHE: Dict[Tuple[int, int, int, int], Image.Image] = {}
_STATIC_MASK_CACHE: Dict[Tuple[int, int, int], Image.Image] = {}
_QUANTIZE_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix='yuna-quant')
_BASE_CANVAS_CACHE: Dict[Tuple[int, str, str], Image.Image] = {}

def _get_rounded_mask(w: int, h: int, radius: int) -> Image.Image:
    key = (w, h, radius)
    if key not in _STATIC_MASK_CACHE:
        mask = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(mask)
        d.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
        _STATIC_MASK_CACHE[key] = mask
    return _STATIC_MASK_CACHE[key]

def _get_fade_mask(w: int, h: int, left_fade: int, right_fade: int) -> Image.Image:
    key = (w, h, left_fade, right_fade)
    if key not in _FADE_MASK_CACHE:
        mask = Image.new("L", (w, h), 255)
        d = ImageDraw.Draw(mask)
        if left_fade > 0:
            for x in range(left_fade):
                d.line([(x, 0), (x, h)], fill=int(255 * (x / left_fade)))
        if right_fade > 0:
            for x in range(right_fade):
                d.line([(w - 1 - x, 0), (w - 1 - x, h)], fill=int(255 * (x / right_fade)))
        _FADE_MASK_CACHE[key] = mask
    return _FADE_MASK_CACHE[key]

def _find_audiobeat_asset(filename: str) -> Optional[str]:
    search_dirs = [
        os.path.join(os.path.dirname(_UTILS_DIR), "assets", "audiobeat"),
        os.path.join(_UTILS_DIR, "assets", "audiobeat"),
        os.path.join(os.getcwd(), "assets", "audiobeat"),
    ]
    for d in search_dirs:
        p = os.path.join(d, filename)
        if os.path.isfile(p):
            return p
    return None

def _get_audiobeat_frames(style: str = "beat1") -> Tuple[List[Image.Image], List[int]]:
    if style in _AUDIOBEAT_CACHE:
        return _AUDIOBEAT_CACHE[style]

    filename = "audiobeat.gif" if style == "beat1" else "audiobeat2.gif"
    path = _find_audiobeat_asset(filename)
    if not path or not os.path.isfile(path):
        other_fn = "audiobeat2.gif" if style == "beat1" else "audiobeat.gif"
        path = _find_audiobeat_asset(other_fn)

    if not path or not os.path.isfile(path):
        return [], []

    try:
        im = Image.open(path)
        raw_frames = [f.copy() for f in ImageSequence.Iterator(im)]

        target_w = 445
        target_h = 100
        processed_frames: List[Image.Image] = []

        if style == "beat1" or "audiobeat.gif" in path:
            # Style 1: Audio equalizer wave pulse (audiobeat.gif) - Razor-sharp vector curve
            durations = [36] * len(raw_frames)
            for rf in raw_frames:
                f_crop = rf.convert("RGB").crop((12, 20, 190, 64))
                pts = []
                for x in range(f_crop.width):
                    bright_ys = [y for y in range(f_crop.height) if f_crop.getpixel((x, y)) != (0, 0, 0)]
                    if bright_ys:
                        pts.append((x, sum(bright_ys) / len(bright_ys)))

                scaled_pts = []
                for x, y in pts:
                    sx = (x / max(1, f_crop.width - 1)) * (target_w - 1)
                    sy = 50.0 + (y - 25.0) * 3.5
                    scaled_pts.append((sx, min(target_h - 2, max(2, sy))))

                f_res = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
                d = ImageDraw.Draw(f_res)
                if len(scaled_pts) > 1:
                    # Luminous neon cyan glow line
                    d.line(scaled_pts, fill=(0, 240, 255, 255), width=4, joint="curve")
                    # Razor-sharp pure white center core (100% solid, zero blur)
                    d.line(scaled_pts, fill=(255, 255, 255, 255), width=2, joint="curve")
                processed_frames.append(f_res)
        else:
            # Style 2: Sound waveform pulse (audiobeat2.gif) - Exact authentic animation from shared asset
            # Prominent, larger 360x112 size with high-fidelity LANCZOS scaling and edge sharpening
            target_w = 360
            target_h = 112
            durations = [36] * len(raw_frames)
            for rf in raw_frames:
                rf_rgba = rf.convert("RGBA")
                # Cleanly key out dark background (RGB ~ 4..12) while preserving all antialiased wave edges
                gray = ImageOps.grayscale(rf_rgba)
                alpha = gray.point(lambda p: 0 if p <= 16 else min(255, int((p - 16) * (255 / 239) * 1.30)))
                rf_rgba.putalpha(alpha)
                # High-fidelity LANCZOS enlargement with edge sharpening for razor-sharp visual clarity
                f_res = rf_rgba.resize((target_w, target_h), Image.Resampling.LANCZOS)
                f_sharp = f_res.filter(ImageFilter.UnsharpMask(radius=1.0, percent=125, threshold=2))
                processed_frames.append(f_sharp)

        _AUDIOBEAT_CACHE[style] = (processed_frames, durations)
        return _AUDIOBEAT_CACHE[style]
    except Exception as e:
        print(f"[AUDIOBEAT CACHE ERROR] Failed to load {filename}: {e}")
        return [], []

# Warm up audiobeat frames into memory on import
try:
    _get_audiobeat_frames("beat1")
    _get_audiobeat_frames("beat2")
except Exception:
    pass

def _get_font(font_name: str, size: int):
    candidates = [
        font_name,
        os.path.join(_UTILS_DIR, os.path.basename(font_name)),
        os.path.join(_UTILS_DIR, "arial.ttf"),
        "arial.ttf"
    ]
    for p in candidates:
        try:
            if os.path.isfile(p):
                return ImageFont.truetype(p, size)
        except Exception:
            pass
    try:
        return ImageFont.truetype(font_name, size)
    except Exception:
        return ImageFont.load_default()

def format_time_str(seconds: int) -> str:
    if seconds <= 0:
        return "00:00"
    m = seconds // 60
    s = seconds % 60
    if m >= 60:
        h = m // 60
        m = m % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

from dataclasses import dataclass

@dataclass(frozen=True)
class MusicCardThemeConfig:
    key: str
    display_name: str
    bg_style: str  # "blurred_artwork" or "gradient"
    bg_color: Tuple[int, int, int, int]
    bg_top_color: Optional[Tuple[int, int, int, int]] = None
    bg_bottom_color: Optional[Tuple[int, int, int, int]] = None
    border_color: Optional[Tuple[int, int, int, int]] = None
    border_width: int = 1
    title_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    artist_color: Tuple[int, int, int, int] = (160, 165, 180, 255)
    bar_unplayed_color: Tuple[int, int, int, int] = (60, 62, 72, 255)
    bar_played_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    knob_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    knob_inner_color: Optional[Tuple[int, int, int, int]] = None
    time_color: Tuple[int, int, int, int] = (140, 145, 160, 255)
    thumb_border_color: Optional[Tuple[int, int, int, int]] = None
    ph_bg: Tuple[int, int, int, int] = (14, 14, 16, 255)
    ph_border: Tuple[int, int, int, int] = (255, 255, 255, 80)
    ph_icon: Tuple[int, int, int, int] = (255, 255, 255, 255)

THEME_ORIGINAL = MusicCardThemeConfig(
    key="original",
    display_name="Original",
    bg_style="blurred_artwork",
    bg_color=(20, 21, 26, 255),
    bg_top_color=(24, 26, 32, 255),
    bg_bottom_color=(16, 17, 22, 255),
    border_color=None,
    border_width=0,
    title_color=(255, 255, 255, 255),
    artist_color=(160, 165, 180, 255),
    bar_unplayed_color=(60, 62, 72, 255),
    bar_played_color=(255, 255, 255, 255),
    knob_color=(255, 255, 255, 255),
    knob_inner_color=None,
    time_color=(140, 145, 160, 255),
    thumb_border_color=None,
    ph_bg=(14, 14, 16, 255),
    ph_border=(255, 255, 255, 80),
    ph_icon=(255, 255, 255, 255)
)

THEME_MIDNIGHT_GOLD = MusicCardThemeConfig(
    key="midnight_gold",
    display_name="Midnight Gold",
    bg_style="gradient",
    bg_color=(8, 8, 8, 255),              # #080808
    bg_top_color=(16, 15, 12, 255),
    bg_bottom_color=(8, 8, 8, 255),
    border_color=(212, 175, 55, 110),       # #D4AF37 at ~43% opacity
    border_width=1,
    title_color=(255, 255, 255, 255),       # #FFFFFF
    artist_color=(161, 161, 170, 255),      # #A1A1AA
    bar_unplayed_color=(38, 36, 30, 255),   # deep charcoal
    bar_played_color=(212, 175, 55, 255),   # #D4AF37
    knob_color=(212, 175, 55, 255),         # #D4AF37
    knob_inner_color=(255, 255, 255, 255),  # #FFFFFF
    time_color=(161, 161, 170, 255),        # #A1A1AA
    thumb_border_color=(212, 175, 55, 70),
    ph_bg=(14, 14, 14, 255),
    ph_border=(212, 175, 55, 90),
    ph_icon=(212, 175, 55, 255)
)

THEME_CYBER_NEON = MusicCardThemeConfig(
    key="cyber_neon",
    display_name="Cyber Neon",
    bg_style="gradient",
    bg_color=(9, 13, 24, 255),             # #090D18
    bg_top_color=(15, 21, 38, 255),
    bg_bottom_color=(9, 13, 24, 255),
    border_color=(0, 229, 255, 110),        # #00E5FF
    border_width=1,
    title_color=(255, 255, 255, 255),       # #FFFFFF
    artist_color=(168, 85, 247, 255),       # #A855F7
    bar_unplayed_color=(20, 28, 48, 255),
    bar_played_color=(0, 229, 255, 255),    # #00E5FF
    knob_color=(0, 229, 255, 255),          # #00E5FF
    knob_inner_color=(255, 255, 255, 255),  # #FFFFFF
    time_color=(148, 163, 184, 255),        # soft cyber slate
    thumb_border_color=(0, 229, 255, 60),
    ph_bg=(12, 17, 32, 255),
    ph_border=(0, 229, 255, 90),
    ph_icon=(0, 229, 255, 255)
)

THEME_EMERALD_ELITE = MusicCardThemeConfig(
    key="emerald_elite",
    display_name="Emerald Elite",
    bg_style="gradient",
    bg_color=(7, 17, 13, 255),              # #07110D
    bg_top_color=(12, 28, 21, 255),
    bg_bottom_color=(7, 17, 13, 255),
    border_color=(214, 184, 117, 110),      # #D6B875 champagne gold
    border_width=1,
    title_color=(245, 255, 249, 255),       # #F5FFF9
    artist_color=(214, 184, 117, 255),      # #D6B875
    bar_unplayed_color=(17, 37, 28, 255),   # deep forest pine
    bar_played_color=(0, 201, 135, 255),    # #00C987
    knob_color=(214, 184, 117, 255),        # #D6B875
    knob_inner_color=(0, 201, 135, 255),    # #00C987
    time_color=(140, 168, 153, 255),        # soft sage
    thumb_border_color=(214, 184, 117, 60),
    ph_bg=(9, 22, 17, 255),
    ph_border=(0, 201, 135, 90),
    ph_icon=(0, 201, 135, 255)
)


THEME_BLACK = MusicCardThemeConfig(
    key="black",
    display_name="Dark High-Contrast",
    bg_style="solid",
    bg_color=(0, 0, 0, 255),
    border_color=(255, 255, 255, 255),
    border_width=1,
    title_color=(255, 255, 255, 255),
    artist_color=(255, 255, 255, 255),
    bar_unplayed_color=(60, 60, 65, 255),
    bar_played_color=(255, 255, 255, 255),
    knob_color=(255, 255, 255, 255),
    knob_inner_color=None,
    time_color=(255, 255, 255, 255),
    thumb_border_color=None,
    ph_bg=(14, 14, 16, 255),
    ph_border=(255, 255, 255, 80),
    ph_icon=(255, 255, 255, 255)
)

THEME_WHITE = MusicCardThemeConfig(
    key="white",
    display_name="Light Inverted",
    bg_style="solid",
    bg_color=(255, 255, 255, 255),
    border_color=(0, 0, 0, 255),
    border_width=1,
    title_color=(0, 0, 0, 255),
    artist_color=(0, 0, 0, 255),
    bar_unplayed_color=(210, 210, 215, 255),
    bar_played_color=(0, 0, 0, 255),
    knob_color=(0, 0, 0, 255),
    knob_inner_color=None,
    time_color=(0, 0, 0, 255),
    thumb_border_color=None,
    ph_bg=(240, 240, 245, 255),
    ph_border=(0, 0, 0, 80),
    ph_icon=(0, 0, 0, 255)
)


THEME_CRIMSON = MusicCardThemeConfig(
    key="crimson",
    display_name="Blood Noir",
    bg_style="solid",
    bg_color=(10, 10, 10, 255),
    border_color=(255, 42, 77, 255),
    border_width=1,
    title_color=(255, 255, 255, 255),
    artist_color=(255, 42, 77, 255),
    bar_unplayed_color=(46, 20, 25, 255),
    bar_played_color=(255, 42, 77, 255),
    knob_color=(255, 42, 77, 255),
    knob_inner_color=(255, 255, 255, 255),
    time_color=(255, 163, 177, 255),
    thumb_border_color=(255, 42, 77, 60),
    ph_bg=(16, 12, 14, 255),
    ph_border=(255, 42, 77, 90),
    ph_icon=(255, 42, 77, 255)
)

THEME_CRIMSON_LIGHT = MusicCardThemeConfig(
    key="crimson_light",
    display_name="Crimson Pure (Inverted)",
    bg_style="solid",
    bg_color=(255, 255, 255, 255),
    border_color=(217, 4, 41, 255),
    border_width=1,
    title_color=(17, 17, 17, 255),
    artist_color=(217, 4, 41, 255),
    bar_unplayed_color=(242, 214, 220, 255),
    bar_played_color=(217, 4, 41, 255),
    knob_color=(217, 4, 41, 255),
    knob_inner_color=None,
    time_color=(122, 30, 46, 255),
    thumb_border_color=(217, 4, 41, 60),
    ph_bg=(250, 240, 242, 255),
    ph_border=(217, 4, 41, 90),
    ph_icon=(217, 4, 41, 255)
)

THEME_ABYSS = MusicCardThemeConfig(
    key="abyss",
    display_name="Deep Abyss",
    bg_style="solid",
    bg_color=(6, 13, 26, 255),
    border_color=(56, 189, 248, 255),
    border_width=1,
    title_color=(255, 255, 255, 255),
    artist_color=(56, 189, 248, 255),
    bar_unplayed_color=(17, 34, 61, 255),
    bar_played_color=(56, 189, 248, 255),
    knob_color=(56, 189, 248, 255),
    knob_inner_color=(255, 255, 255, 255),
    time_color=(186, 230, 253, 255),
    thumb_border_color=(56, 189, 248, 60),
    ph_bg=(10, 18, 32, 255),
    ph_border=(56, 189, 248, 90),
    ph_icon=(56, 189, 248, 255)
)

THEME_GLACIER = MusicCardThemeConfig(
    key="glacier",
    display_name="Glacier Ice (Inverted)",
    bg_style="solid",
    bg_color=(240, 249, 255, 255),
    border_color=(8, 47, 73, 255),
    border_width=1,
    title_color=(8, 47, 73, 255),
    artist_color=(2, 132, 199, 255),
    bar_unplayed_color=(186, 230, 253, 255),
    bar_played_color=(8, 47, 73, 255),
    knob_color=(8, 47, 73, 255),
    knob_inner_color=None,
    time_color=(3, 105, 161, 255),
    thumb_border_color=(8, 47, 73, 60),
    ph_bg=(225, 242, 254, 255),
    ph_border=(8, 47, 73, 90),
    ph_icon=(8, 47, 73, 255)
)

THEME_ESPRESSO = MusicCardThemeConfig(
    key="espresso",
    display_name="Dark Roast Espresso",
    bg_style="solid",
    bg_color=(20, 15, 13, 255),
    border_color=(253, 246, 226, 255),
    border_width=1,
    title_color=(253, 246, 226, 255),
    artist_color=(212, 197, 169, 255),
    bar_unplayed_color=(53, 41, 36, 255),
    bar_played_color=(253, 246, 226, 255),
    knob_color=(253, 246, 226, 255),
    knob_inner_color=None,
    time_color=(212, 197, 169, 255),
    thumb_border_color=(253, 246, 226, 60),
    ph_bg=(26, 20, 17, 255),
    ph_border=(253, 246, 226, 90),
    ph_icon=(253, 246, 226, 255)
)

THEME_CREAM = MusicCardThemeConfig(
    key="cream",
    display_name="Vanilla Cream (Inverted)",
    bg_style="solid",
    bg_color=(253, 246, 226, 255),
    border_color=(20, 15, 13, 255),
    border_width=1,
    title_color=(20, 15, 13, 255),
    artist_color=(74, 59, 50, 255),
    bar_unplayed_color=(227, 216, 189, 255),
    bar_played_color=(20, 15, 13, 255),
    knob_color=(20, 15, 13, 255),
    knob_inner_color=None,
    time_color=(99, 80, 67, 255),
    thumb_border_color=(20, 15, 13, 60),
    ph_bg=(245, 236, 214, 255),
    ph_border=(20, 15, 13, 90),
    ph_icon=(20, 15, 13, 255)
)

THEME_VIOLET = MusicCardThemeConfig(
    key="violet",
    display_name="Midnight Violet",
    bg_style="solid",
    bg_color=(13, 8, 20, 255),
    border_color=(233, 213, 255, 255),
    border_width=1,
    title_color=(255, 255, 255, 255),
    artist_color=(192, 132, 252, 255),
    bar_unplayed_color=(40, 27, 61, 255),
    bar_played_color=(192, 132, 252, 255),
    knob_color=(233, 213, 255, 255),
    knob_inner_color=(255, 255, 255, 255),
    time_color=(216, 180, 254, 255),
    thumb_border_color=(233, 213, 255, 60),
    ph_bg=(20, 14, 30, 255),
    ph_border=(233, 213, 255, 90),
    ph_icon=(233, 213, 255, 255)
)

THEME_LAVENDER = MusicCardThemeConfig(
    key="lavender",
    display_name="Soft Lavender (Inverted)",
    bg_style="solid",
    bg_color=(250, 245, 255, 255),
    border_color=(46, 16, 101, 255),
    border_width=1,
    title_color=(46, 16, 101, 255),
    artist_color=(126, 34, 206, 255),
    bar_unplayed_color=(233, 213, 255, 255),
    bar_played_color=(46, 16, 101, 255),
    knob_color=(46, 16, 101, 255),
    knob_inner_color=None,
    time_color=(88, 28, 135, 255),
    thumb_border_color=(46, 16, 101, 60),
    ph_bg=(242, 233, 250, 255),
    ph_border=(46, 16, 101, 90),
    ph_icon=(46, 16, 101, 255)
)

THEME_MINT = MusicCardThemeConfig(
    key="mint",
    display_name="Terminal Mint",
    bg_style="solid",
    bg_color=(10, 15, 13, 255),
    border_color=(0, 255, 163, 255),
    border_width=1,
    title_color=(255, 255, 255, 255),
    artist_color=(0, 255, 163, 255),
    bar_unplayed_color=(20, 36, 30, 255),
    bar_played_color=(0, 255, 163, 255),
    knob_color=(0, 255, 163, 255),
    knob_inner_color=(255, 255, 255, 255),
    time_color=(150, 255, 215, 255),
    thumb_border_color=(0, 255, 163, 60),
    ph_bg=(14, 20, 18, 255),
    ph_border=(0, 255, 163, 90),
    ph_icon=(0, 255, 163, 255)
)

THEME_MINT_LIGHT = MusicCardThemeConfig(
    key="mint_light",
    display_name="Mint Milk (Inverted)",
    bg_style="solid",
    bg_color=(240, 253, 244, 255),
    border_color=(6, 78, 59, 255),
    border_width=1,
    title_color=(6, 78, 59, 255),
    artist_color=(5, 150, 105, 255),
    bar_unplayed_color=(187, 247, 208, 255),
    bar_played_color=(6, 78, 59, 255),
    knob_color=(6, 78, 59, 255),
    knob_inner_color=None,
    time_color=(4, 120, 87, 255),
    thumb_border_color=(6, 78, 59, 60),
    ph_bg=(230, 248, 236, 255),
    ph_border=(6, 78, 59, 90),
    ph_icon=(6, 78, 59, 255)
)

THEME_AMBER = MusicCardThemeConfig(
    key="amber",
    display_name="Black Amber",
    bg_style="solid",
    bg_color=(8, 8, 8, 255),
    border_color=(255, 140, 0, 255),
    border_width=1,
    title_color=(255, 255, 255, 255),
    artist_color=(255, 140, 0, 255),
    bar_unplayed_color=(45, 28, 12, 255),
    bar_played_color=(255, 140, 0, 255),
    knob_color=(255, 140, 0, 255),
    knob_inner_color=(255, 255, 255, 255),
    time_color=(255, 185, 95, 255),
    thumb_border_color=(255, 140, 0, 60),
    ph_bg=(18, 14, 10, 255),
    ph_border=(255, 140, 0, 90),
    ph_icon=(255, 140, 0, 255)
)

THEME_AMBER_LIGHT = MusicCardThemeConfig(
    key="amber_light",
    display_name="Amber Light (Inverted)",
    bg_style="solid",
    bg_color=(255, 251, 235, 255),
    border_color=(120, 53, 15, 255),
    border_width=1,
    title_color=(120, 53, 15, 255),
    artist_color=(217, 119, 6, 255),
    bar_unplayed_color=(254, 230, 199, 255),
    bar_played_color=(120, 53, 15, 255),
    knob_color=(120, 53, 15, 255),
    knob_inner_color=None,
    time_color=(180, 83, 9, 255),
    thumb_border_color=(120, 53, 15, 60),
    ph_bg=(252, 244, 222, 255),
    ph_border=(120, 53, 15, 90),
    ph_icon=(120, 53, 15, 255)
)

THEMES: Dict[str, MusicCardThemeConfig] = {
    "original": THEME_ORIGINAL,
    "black": THEME_BLACK,
    "white": THEME_WHITE,
    "crimson": THEME_CRIMSON,
    "crimson_light": THEME_CRIMSON_LIGHT,
    "abyss": THEME_ABYSS,
    "glacier": THEME_GLACIER,
    "espresso": THEME_ESPRESSO,
    "cream": THEME_CREAM,
    "violet": THEME_VIOLET,
    "lavender": THEME_LAVENDER,
    "mint": THEME_MINT,
    "mint_light": THEME_MINT_LIGHT,
    "amber": THEME_AMBER,
    "amber_light": THEME_AMBER_LIGHT,
    "midnight_gold": THEME_MIDNIGHT_GOLD,
    "cyber_neon": THEME_CYBER_NEON,
    "emerald_elite": THEME_EMERALD_ELITE,
}

THEME_ALIASES: Dict[str, str] = {
    "default": "original",
    "classic": "original",
    "orig": "original",
    "transparent": "original",
    "blur": "original",
    "black": "black",
    "dark": "black",
    "white": "white",
    "light": "white",
    "inverted": "white",
    "crimson": "crimson",
    "blood": "crimson",
    "red": "crimson",
    "crimson_light": "crimson_light",
    "crimson_white": "crimson_light",
    "red_light": "crimson_light",
    "abyss": "abyss",
    "ocean": "abyss",
    "ice_dark": "abyss",
    "glacier": "glacier",
    "ice": "glacier",
    "ice_light": "glacier",
    "espresso": "espresso",
    "coffee": "espresso",
    "cream": "cream",
    "vanilla": "cream",
    "violet": "violet",
    "purple": "violet",
    "lavender": "lavender",
    "lilac": "lavender",
    "mint": "mint",
    "terminal": "mint",
    "mint_light": "mint_light",
    "amber": "amber",
    "orange": "amber",
    "amber_light": "amber_light",
    "gold": "midnight_gold",
    "midnight": "midnight_gold",
    "midnightgold": "midnight_gold",
    "neon": "cyber_neon",
    "cyber": "cyber_neon",
    "cyberneon": "cyber_neon",
    "emerald": "emerald_elite",
    "elite": "emerald_elite",
    "emeraldelite": "emerald_elite",
    "green": "emerald_elite",
}

ROTATING_THEME_KEYS = [
    "original",         # Transparent blurred album artwork
    "black",            # Pure Black & White
    "white",            # Pure White & Black
    "crimson",          # Blood Noir (Black & Electric Crimson)
    "crimson_light",    # Crimson Pure (White & Deep Crimson)
    "abyss",            # Deep Abyss (Dark Ocean Navy & Electric Ice Cyan)
    "glacier",          # Glacier Ice (Frosted Ice-White & Oceanic Navy)
    "espresso",         # Dark Roast Espresso (Dark Roast & Warm Silk Cream)
    "cream",            # Vanilla Cream (Warm Cream & Dark Espresso)
    "violet",           # Midnight Violet (Obsidian Plum & Soft Lavender)
    "lavender",         # Soft Lavender (Lavender-White & Deep Plum)
    "mint",             # Terminal Mint (Slate Charcoal & Toxic Mint)
    "mint_light",       # Mint Milk (Mint-White & Forest Slate)
    "amber",            # Black Amber (Pitch Black & Neon Amber)
    "amber_light",      # Amber Light (Sun-White & Burnt Amber)
    "midnight_gold",    # Luxury Midnight Gold
    "cyber_neon",       # Synthwave Cyber Neon
    "emerald_elite",    # Regal Emerald Elite
]

class MusicCardGenerator:
    """High-performance, non-blocking PIL renderer for dynamic Discord music player cards."""

    @staticmethod
    async def fetch_thumbnail(url: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[Image.Image]:
        if not url or not str(url).startswith(("http://", "https://")):
            return None

        clean_url = str(url).strip()
        if clean_url in _THUMBNAIL_CACHE:
            return _THUMBNAIL_CACHE[clean_url]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
        }

        # 1. Primary: Async HTTP with 3.5s timeout (connect=2.0s to failover fast if DNS hangs)
        close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            close_session = True

        try:
            async with session.get(clean_url, headers=headers, timeout=aiohttp.ClientTimeout(total=3.5, connect=2.0)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 300:
                        img = await asyncio.to_thread(Image.open, io.BytesIO(data))
                        img = img.convert("RGBA")
                        if len(_THUMBNAIL_CACHE) >= _MAX_CACHE_SIZE:
                            _THUMBNAIL_CACHE.pop(next(iter(_THUMBNAIL_CACHE)))
                        _THUMBNAIL_CACHE[clean_url] = img
                        return img
        except Exception:
            pass
        finally:
            if close_session and not session.closed:
                try:
                    await session.close()
                except Exception:
                    pass

        # 2. Secondary fallback: Native OS socket fetch via urllib (bypasses aiohttp Windows DNS issues)
        def _sync_fetch():
            try:
                req = urllib.request.Request(clean_url, headers=headers)
                with urllib.request.urlopen(req, timeout=4.0) as r:
                    if r.status == 200:
                        raw = r.read()
                        if len(raw) > 300:
                            im = Image.open(io.BytesIO(raw)).convert("RGBA")
                            return im
            except Exception:
                return None

        img_fallback = await asyncio.to_thread(_sync_fetch)
        if img_fallback:
            if len(_THUMBNAIL_CACHE) >= _MAX_CACHE_SIZE:
                _THUMBNAIL_CACHE.pop(next(iter(_THUMBNAIL_CACHE)))
            _THUMBNAIL_CACHE[clean_url] = img_fallback
            return img_fallback

        return None

    @classmethod
    def render_platform_icon(cls, platform: str, size: int = 20) -> Image.Image:
        key = ((platform or "youtube").lower(), size)
        if key in _PLATFORM_ICON_CACHE:
            return _PLATFORM_ICON_CACHE[key]
        scale = 4
        s = size * scale
        icon = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(icon)
        p = (platform or "youtube").lower()

        if "spotify" in p:
            # Official Spotify green circle (#1DB954) with 3 curved soundwave lines
            d.ellipse((0, 0, s, s), fill=(29, 185, 84, 255))
            cx, cy = s * 0.5, s * 0.5
            d.arc((cx - s * 0.38, cy - s * 0.38, cx + s * 0.38, cy + s * 0.22), start=205, end=335, fill=(18, 18, 18, 255), width=max(2, int(s * 0.08)))
            d.arc((cx - s * 0.32, cy - s * 0.18, cx + s * 0.32, cy + s * 0.36), start=205, end=335, fill=(18, 18, 18, 255), width=max(2, int(s * 0.075)))
            d.arc((cx - s * 0.26, cy + s * 0.02, cx + s * 0.26, cy + s * 0.50), start=205, end=335, fill=(18, 18, 18, 255), width=max(2, int(s * 0.07)))
        elif "youtubemusic" in p or "ytm" in p or "music.youtube" in p:
            # YouTube Music: red circle with concentric white ring & play triangle
            d.ellipse((0, 0, s, s), fill=(255, 0, 0, 255))
            d.ellipse((s * 0.2, s * 0.2, s * 0.8, s * 0.8), outline=(255, 255, 255, 255), width=max(2, int(s * 0.06)))
            tri = [(s * 0.42, s * 0.35), (s * 0.42, s * 0.65), (s * 0.68, s * 0.50)]
            d.polygon(tri, fill=(255, 255, 255, 255))
        elif "jiosaavn" in p or "saavn" in p:
            # JioSaavn: emerald green/teal circle
            d.ellipse((0, 0, s, s), fill=(43, 194, 150, 255))
            d.ellipse((s * 0.25, s * 0.25, s * 0.75, s * 0.75), fill=(255, 255, 255, 255))
            d.ellipse((s * 0.40, s * 0.40, s * 0.60, s * 0.60), fill=(43, 194, 150, 255))
        elif "apple" in p:
            # Apple Music: vibrant pink/red rounded badge with music note
            d.rounded_rectangle((0, 0, s, s), radius=int(s * 0.22), fill=(252, 60, 68, 255))
            d.ellipse((s * 0.28, s * 0.55, s * 0.48, s * 0.75), fill=(255, 255, 255, 255))
            d.rectangle((s * 0.42, s * 0.25, s * 0.48, s * 0.65), fill=(255, 255, 255, 255))
            d.polygon([(s * 0.42, s * 0.25), (s * 0.75, s * 0.18), (s * 0.75, s * 0.32), (s * 0.42, s * 0.38)], fill=(255, 255, 255, 255))
            d.rectangle((s * 0.69, s * 0.25, s * 0.75, s * 0.65), fill=(255, 255, 255, 255))
            d.ellipse((s * 0.55, s * 0.52, s * 0.75, s * 0.72), fill=(255, 255, 255, 255))
        elif "soundcloud" in p:
            # SoundCloud: orange rounded badge
            d.rounded_rectangle((0, 0, s, s), radius=int(s * 0.22), fill=(255, 85, 0, 255))
            d.ellipse((s * 0.35, s * 0.35, s * 0.75, s * 0.65), fill=(255, 255, 255, 255))
            d.rectangle((s * 0.25, s * 0.45, s * 0.75, s * 0.70), fill=(255, 255, 255, 255))
        else:
            # Standard YouTube: red rounded rectangle with white play triangle
            d.rounded_rectangle((0, int(s * 0.08), s, int(s * 0.92)), radius=int(s * 0.24), fill=(255, 0, 0, 255))
            tri = [(s * 0.38, s * 0.32), (s * 0.38, s * 0.68), (s * 0.72, s * 0.50)]
            d.polygon(tri, fill=(255, 255, 255, 255))

        res_icon = icon.resize((size, size), Image.Resampling.LANCZOS)
        _PLATFORM_ICON_CACHE[key] = res_icon
        return res_icon
    @classmethod
    def get_theme_config(cls, theme: Optional[str] = None) -> MusicCardThemeConfig:
        """Returns the centralized MusicCardThemeConfig for a given theme name or alias.
        Defaults to THEME_ORIGINAL to preserve 100% backward compatibility."""
        if not theme:
            return THEME_ORIGINAL
        t_clean = str(theme).lower().strip().replace("-", "_").replace(" ", "_")
        key = THEME_ALIASES.get(t_clean, t_clean)
        return THEMES.get(key, THEME_ORIGINAL)

    @classmethod
    def get_theme_for_count(cls, count: int) -> str:
        """Cycles cleanly through all 4 themes every 3 songs."""
        return ROTATING_THEME_KEYS[(count // 3) % len(ROTATING_THEME_KEYS)]

    @classmethod
    def render_card(
        cls,
        title: str,
        artist: str,
        elapsed_sec: int = 0,
        duration_sec: int = 0,
        thumb_img: Optional[Image.Image] = None,
        platform: str = "youtube",
        style: str = "alternate",
        theme: Optional[str] = None
    ) -> io.BytesIO:
        cfg = cls.get_theme_config(theme or style)
        theme_key = cfg.key

        # High-definition Retina scale canvas (780x285 = 1.5x crisp modern proportion)
        W, H = 780, 285
        thumb_pad = 15
        thumb_size = H - (thumb_pad * 2)  # 255x255
        text_x = thumb_pad + thumb_size + 24  # 294px
        title_y = 54
        artist_y = 108
        bar_x = text_x
        bar_w = (W - 20) - bar_x  # 466px
        bar_y = 176
        time_y = 198

        clean_a = artist.strip()
        artist_max_w = W - text_x - 18
        font_artist = _get_font("utils/arial.ttf", 24)
        if font_artist.getlength(clean_a) > artist_max_w:
            while len(clean_a) > 3 and font_artist.getlength(clean_a + "...") > artist_max_w:
                clean_a = clean_a[:-1]
            clean_a = clean_a.rstrip() + "..."

        badge_size = 28
        badge_x = W - 20 - badge_size
        badge_y = 20

        # Re-use cached static base canvas (solid/gradient themed bg, border, thumbnail, badge, artist)
        base_key = (id(thumb_img) if thumb_img else 0, str(platform).lower(), clean_a, theme_key)
        if base_key in _BASE_CANVAS_CACHE:
            card = _BASE_CANVAS_CACHE[base_key].copy()
            draw = ImageDraw.Draw(card)
        else:
            card = Image.new("RGBA", (W, H), (0, 0, 0, 0))

            # 1. Background Surface
            if cfg.bg_style == "blurred_artwork":
                if thumb_img:
                    bg = ImageOps.fit(thumb_img, (W, H), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                    bg = bg.filter(ImageFilter.GaussianBlur(radius=32))
                    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                    o_draw = ImageDraw.Draw(overlay)
                    for x in range(W):
                        alpha = int(215 - (x / W) * 20)
                        o_draw.line([(x, 0), (x, H)], fill=(16, 17, 22, alpha))
                    bg = Image.alpha_composite(bg.convert("RGBA"), overlay)
                else:
                    bg = Image.new("RGBA", (W, H), cfg.bg_color)
                    bg_draw = ImageDraw.Draw(bg)
                    for y in range(H):
                        shade = int(24 - (y / H) * 8)
                        bg_draw.line([(0, y), (W, y)], fill=(shade, shade + 2, shade + 6, 255))
            else:
                bg = Image.new("RGBA", (W, H), cfg.bg_color)
                if cfg.bg_top_color and cfg.bg_bottom_color:
                    bg_draw = ImageDraw.Draw(bg)
                    tr, tg, tb, ta = cfg.bg_top_color
                    br, b_g, bb, ba = cfg.bg_bottom_color
                    for y in range(H):
                        f = y / max(1, H - 1)
                        r = int(tr + (br - tr) * f)
                        g = int(tg + (b_g - tg) * f)
                        b = int(tb + (bb - tb) * f)
                        a = int(ta + (ba - ta) * f)
                        bg_draw.line([(0, y), (W, y)], fill=(r, g, b, a))

            card_mask = _get_rounded_mask(W, H, 16)
            card.paste(bg, (0, 0), card_mask)
            draw = ImageDraw.Draw(card)

            # 2. Sleek Border Outline (if configured)
            if cfg.border_color and cfg.border_width > 0:
                draw.rounded_rectangle(
                    (1, 1, W - 2, H - 2),
                    radius=16,
                    outline=cfg.border_color,
                    width=cfg.border_width
                )

            # 3. Thumbnail on Left Side (Preserving original colors!)
            if thumb_img:
                t_square = ImageOps.fit(thumb_img, (thumb_size, thumb_size), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                t_mask = _get_rounded_mask(thumb_size, thumb_size, 14)
                card.paste(t_square, (thumb_pad, thumb_pad), t_mask)
                if cfg.thumb_border_color:
                    draw.rounded_rectangle(
                        (thumb_pad, thumb_pad, thumb_pad + thumb_size, thumb_pad + thumb_size),
                        radius=14,
                        outline=cfg.thumb_border_color,
                        width=1
                    )
            else:
                draw.rounded_rectangle(
                    (thumb_pad, thumb_pad, thumb_pad + thumb_size, thumb_pad + thumb_size),
                    radius=14,
                    fill=cfg.ph_bg,
                    outline=cfg.ph_border,
                    width=1
                )
                cx = thumb_pad + (thumb_size // 2)
                cy = thumb_pad + (thumb_size // 2)
                draw.ellipse((cx - 30, cy + 9, cx - 9, cy + 27), fill=cfg.ph_icon)
                draw.ellipse((cx + 12, cy + 2, cx + 33, cy + 20), fill=cfg.ph_icon)
                draw.rectangle((cx - 14, cy - 27, cx - 9, cy + 18), fill=cfg.ph_icon)
                draw.rectangle((cx + 28, cy - 34, cx + 33, cy + 11), fill=cfg.ph_icon)
                draw.polygon([(cx - 14, cy - 27), (cx + 33, cy - 34), (cx + 33, cy - 25), (cx - 14, cy - 18)], fill=cfg.ph_icon)

            # 4. Dynamic Platform Badge (Top Right)
            platform_icon = cls.render_platform_icon(platform, badge_size)
            card.paste(platform_icon, (badge_x, badge_y), platform_icon)

            # 5. Artist Text (Themed color)
            draw.text((text_x, artist_y), clean_a, font=font_artist, fill=cfg.artist_color)

            if len(_BASE_CANVAS_CACHE) >= 40:
                _BASE_CANVAS_CACHE.pop(next(iter(_BASE_CANVAS_CACHE)))
            _BASE_CANVAS_CACHE[base_key] = card.copy()

        # 6. Typography Fonts
        font_title = _get_font("utils/HelveticaNeuBold.ttf", 36)
        font_time = _get_font("utils/arial.ttf", 18)

        # 7. Progress Bar & Duration
        pct = min(1.0, max(0.0, elapsed_sec / duration_sec)) if duration_sec > 0 else 0.0
        active_w = int(bar_w * pct)

        # Base unplayed track (4px height)
        draw.rounded_rectangle((bar_x, bar_y - 2, bar_x + bar_w, bar_y + 2), radius=2, fill=cfg.bar_unplayed_color)
        # Active progress track (4px height)
        if active_w > 0:
            draw.rounded_rectangle((bar_x, bar_y - 2, bar_x + active_w, bar_y + 2), radius=2, fill=cfg.bar_played_color)

        # Scrubber Knob
        knob_x = bar_x + active_w
        knob_r = 6.0
        draw.ellipse((knob_x - knob_r, bar_y - knob_r, knob_x + knob_r, bar_y + knob_r), fill=cfg.knob_color)
        if cfg.knob_inner_color:
            inner_r = 2.5
            draw.ellipse((knob_x - inner_r, bar_y - inner_r, knob_x + inner_r, bar_y + inner_r), fill=cfg.knob_inner_color)

        # 8. Timestamps (Themed color)
        el_str = format_time_str(elapsed_sec)
        dur_str = format_time_str(duration_sec) if duration_sec > 0 else "LIVE"

        draw.text((bar_x, time_y), el_str, font=font_time, fill=cfg.time_color)
        dur_w = font_time.getlength(dur_str)
        draw.text((bar_x + bar_w - dur_w, time_y), dur_str, font=font_time, fill=cfg.time_color)

        # 9. Billboard Song Title Marquee Animation
        viewport_w = max(100, badge_x - text_x - 14)
        viewport_h = 46
        clean_t = title.strip() or "Unknown Track"
        title_len = font_title.getlength(clean_t)
        overflow = int(title_len - viewport_w + 14)

        buf = io.BytesIO()

        if overflow <= 0:
            # Title fits within viewport: render static at full crisp bold size as true 24-bit lossless PNG
            draw.text((text_x, title_y), clean_t, font=font_title, fill=cfg.title_color)
            card.save(buf, format="PNG")
        else:
            # Title is too large: render full title once onto RGBA strip for relaxed billboard glide
            title_strip_w = int(title_len) + 40
            title_strip = Image.new("RGBA", (title_strip_w, viewport_h), (0, 0, 0, 0))
            d_strip = ImageDraw.Draw(title_strip)
            d_strip.text((0, 0), clean_t, font=font_title, fill=cfg.title_color)


            # 90 frames @ 50ms (20 FPS, 4.5s cycle) - Ultra lightweight (~240 KB), fast to encode & upload
            N_FRAMES = 90
            frame_delay = 50

            # Precompute transparent corner mask indices once for fast transparent GIF quantization
            corner_mask = card.getchannel("A")
            corner_indices = [idx for idx, a in enumerate(corner_mask.tobytes()) if a < 128]

            frames: List[Image.Image] = []
            for i in range(N_FRAMES):
                f_card = card.copy()

                # Legibility Pacing Curve at 20 FPS (90 frames = 4.5s cycle):
                # 1. Frames 0..17 (0.90s): Hold motionless at start so user reads beginning
                # 2. Frames 18..63 (2.30s): Gentle, smooth ease-in-out forward glide (46 frames)
                # 3. Frames 64..75 (0.60s): Hold motionless at end so user reads features tag (12 frames)
                # 4. Frames 76..89 (0.70s): Smooth glide back to start (14 frames)
                if i < 18:
                    progress = 0.0
                elif i < 64:
                    t = (i - 18) / 45.0
                    progress = 0.5 * (1.0 - math.cos(math.pi * t))
                elif i < 76:
                    progress = 1.0
                else:
                    t = (i - 76) / 14.0
                    progress = 0.5 * (1.0 + math.cos(math.pi * t))

                offset = int(progress * overflow)
                view_frame = title_strip.crop((offset, 0, offset + viewport_w, viewport_h))

                # Dynamic edge fade: only fade edges that are overflowing (cached masks)
                left_fade = min(16, offset)
                right_fade = min(16, max(0, overflow - offset))
                if left_fade > 0 or right_fade > 0:
                    fade_mask = _get_fade_mask(viewport_w, viewport_h, left_fade, right_fade)
                    orig_a = view_frame.split()[3]
                    view_frame.putalpha(ImageChops.multiply(orig_a, fade_mask))

                # Alpha-composite title directly onto base frame
                f_card.paste(view_frame, (text_x, title_y), view_frame)
                frames.append(f_card)

            # Master palette generation from first frame RGB (reserve index 255 for transparency)
            f0_rgb = frames[0].convert("RGB")
            p_base = f0_rgb.convert("P", palette=Image.Palette.ADAPTIVE, colors=255)

            # Multi-core frame quantization with transparency index mapping
            def _quant_frame(img: Image.Image) -> Image.Image:
                p = img.convert("RGB").quantize(palette=p_base, dither=Image.Dither.NONE)
                if corner_indices:
                    p_bytes = bytearray(p.tobytes())
                    for c_idx in corner_indices:
                        p_bytes[c_idx] = 255
                    p.frombytes(bytes(p_bytes))
                return p

            frames_p = list(_QUANTIZE_POOL.map(_quant_frame, frames))

            # Fast direct GIF encoding with transparency
            frames_p[0].save(
                buf,
                format="GIF",
                save_all=True,
                append_images=frames_p[1:],
                loop=0,
                duration=[frame_delay] * N_FRAMES,
                transparency=255,
                disposal=2,
                optimize=False
            )

        buf.seek(0)
        return buf

    _SONG_STYLE_COUNTER: int = 0

    @classmethod
    def get_next_style(cls) -> str:
        """Alternates between beat1 (audiobeat.gif) and beat2 (audiobeat2.gif) per song."""
        style = "beat1" if (cls._SONG_STYLE_COUNTER % 2 == 0) else "beat2"
        cls._SONG_STYLE_COUNTER += 1
        return style

    @classmethod
    async def create_card_file(
        cls,
        title: str,
        artist: str,
        elapsed_sec: int = 0,
        duration_sec: int = 0,
        thumbnail_url: Optional[str] = None,
        platform: str = "youtube",
        session: Optional[aiohttp.ClientSession] = None,
        fallback_urls: Optional[List[str]] = None,
        style: str = "alternate",
        theme: Optional[str] = None
    ) -> discord.File:
        candidates: List[str] = []
        if thumbnail_url:
            candidates.append(thumbnail_url)
        if fallback_urls:
            for fu in fallback_urls:
                if fu and fu not in candidates:
                    candidates.append(fu)

        thumb_img = None
        for cand in candidates:
            try:
                thumb_img = await cls.fetch_thumbnail(cand, session=session)
                if thumb_img:
                    break
            except Exception:
                continue

        buf = await asyncio.to_thread(
            cls.render_card,
            title=title,
            artist=artist,
            elapsed_sec=elapsed_sec,
            duration_sec=duration_sec,
            thumb_img=thumb_img,
            platform=platform,
            style=style,
            theme=theme
        )
        is_gif = buf.getvalue().startswith(b"GIF")
        filename = "music_card.gif" if is_gif else "music_card.png"
        return discord.File(fp=buf, filename=filename)
