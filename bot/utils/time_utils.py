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
Zyuna Central Time & Timezone Utilities.
Provides unified, robust Indian Standard Time (IST, UTC+05:30) logging and formatting.
Ensures all console prints, standard library logging, and discord logs display exact Date and Time in IST.
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional, Union
import logging
import sys
import builtins
import re

# Official Indian Standard Time (UTC+05:30)
IST = timezone(timedelta(hours=5, minutes=30), name="IST")
UTC = timezone.utc

__all__ = [
    "IST", "UTC", "now_ist", "now_utc", "utcnow", "to_ist",
    "format_ist_date", "format_ist_time", "format_ist_datetime",
    "format_ist_full", "today_ist_str", "get_epoch",
    "discord_timestamp", "ist_converter", "ZyunaLogFormatter",
    "setup_ist_logging", "install_ist_print_hook"
]


def now_ist() -> datetime:
    """Returns the current timezone-aware datetime in Indian Standard Time (IST, UTC+05:30)."""
    return datetime.now(IST)


def now_utc() -> datetime:
    """Returns current UTC datetime."""
    return datetime.now(UTC)


def utcnow() -> datetime:
    """Convenience alias for now_utc()."""
    return now_utc()


def today_ist_str() -> str:
    """Returns today's date in IST as 'YYYY-MM-DD'."""
    return format_ist_date()


def to_ist(dt: Optional[datetime] = None) -> datetime:
    """Converts any datetime (UTC or aware) into IST. If naive, assumes UTC."""
    if dt is None:
        return now_ist()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(IST)


def format_ist_date(dt: Optional[datetime] = None) -> str:
    """Returns formatted IST date string: 'YYYY-MM-DD' (e.g. '2026-10-20')."""
    return to_ist(dt).strftime("%Y-%m-%d")


def format_ist_time(dt: Optional[datetime] = None, include_seconds: bool = True) -> str:
    """Returns formatted IST time string: 'HH:MM:SS AM/PM IST'."""
    fmt = "%I:%M:%S %p IST" if include_seconds else "%I:%M %p IST"
    return to_ist(dt).strftime(fmt)


def format_ist_datetime(dt: Optional[datetime] = None) -> str:
    """Returns formatted IST date and time string: 'YYYY-MM-DD hh:mm:ss AM/PM IST'."""
    return to_ist(dt).strftime("%Y-%m-%d %I:%M:%S %p IST")


def format_ist_full(dt: Optional[datetime] = None) -> str:
    """Returns full human-friendly IST date & time: '20 October 2026, 12:30:00 AM IST'."""
    return to_ist(dt).strftime("%d %B %Y, %I:%M:%S %p IST")


def get_epoch(dt: Optional[datetime] = None) -> int:
    """Returns Unix epoch timestamp."""
    if dt is None:
        return int(now_utc().timestamp())
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return int(dt.timestamp())


def discord_timestamp(dt: Optional[datetime] = None, style: str = "F") -> str:
    """Returns Discord markdown timestamp: <t:epoch:style>."""
    return f"<t:{get_epoch(dt)}:{style}>"


def ist_converter(seconds: Optional[float] = None):
    """Converts unix timestamp seconds into a time.struct_time in IST."""
    if seconds is None:
        dt = datetime.now(IST)
    else:
        dt = datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone(IST)
    return dt.timetuple()


class ZyunaLogFormatter(logging.Formatter):
    """Logging formatter displaying timestamps with date, time, and explicit IST timezone."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("datefmt", "%Y-%m-%d %I:%M:%S %p IST")
        super().__init__(*args, **kwargs)
        self.datefmt = "%Y-%m-%d %I:%M:%S %p IST"

    def format(self, record):
        return super().format(record)


_orig_print = builtins.print
_ANSI_STRIP = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
_TS_REGEX = re.compile(r'^\[?\d{4}-\d{2}-\d{2}|^\[?\d{1,2}:\d{2}', re.IGNORECASE)


def install_ist_print_hook():
    """Wraps builtins.print to automatically prefix un-timestamped messages with Date and Time in IST."""
    if getattr(builtins.print, "_zyuna_hooked", False):
        return

    def zyuna_print(*args, **kwargs):
        file = kwargs.get("file", None)
        if (file is None or file in (sys.stdout, sys.stderr)) and args:
            first_arg = str(args[0])
            clean = _ANSI_STRIP.sub('', first_arg).strip()
            # Do not prefix empty lines, separator lines, banner art, or lines that already have a timestamp
            if clean and not (set(clean) <= {'*', '-', '=', '#', '_', ' '}) and '██' not in clean and not _TS_REGEX.match(clean):
                ts = datetime.now(IST).strftime("%Y-%m-%d %I:%M:%S %p IST")
        try:
            return _orig_print(*args, **kwargs)
        except UnicodeEncodeError:
            target = kwargs.get("file") or sys.stdout
            enc = getattr(target, "encoding", "ascii") or "ascii"
            safe_args = [
                str(a).encode(enc, errors="replace").decode(enc)
                for a in args
            ]
            return _orig_print(*safe_args, **kwargs)

    zyuna_print._zyuna_hooked = True
    builtins.print = zyuna_print


def setup_ist_logging():
    """Globally configures Python standard logging and print() to output in Date & Time IST."""
    # 1. Standard library logging converter (used by discord.py, uvicorn, aiohttp, etc.)
    logging.Formatter.converter = staticmethod(ist_converter)

    # 2. Configure root logger
    try:
        logging.basicConfig(
            level=logging.INFO,
            format="\x1b[36m[%(asctime)s]\x1b[0m [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %I:%M:%S %p IST",
        )
        for handler in logging.root.handlers:
            if handler.formatter:
                handler.formatter.datefmt = "%Y-%m-%d %I:%M:%S %p IST"
    except Exception:
        pass

    # 3. Global print hook
    install_ist_print_hook()


# Auto-configure standard logging converter and print hook on import
logging.Formatter.converter = staticmethod(ist_converter)
install_ist_print_hook()
