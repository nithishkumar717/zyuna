from __future__ import annotations
import re
import random
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from .constants import LANGUAGES, MOODS, normalize_title

@dataclass
class LanguageResult:
    language: str = "unknown"
    confidence: float = 0.0
    source: str = "unknown"
    scores: Dict[str, float] = field(default_factory=dict)

    @property
    def is_confident(self) -> bool:
        return self.confidence >= 0.70

    def __str__(self) -> str:
        return f"{self.language} ({self.confidence:.2f}, {self.source})"


class MusicSessionState:
    """Session Memory Context for Intelligent Music Recommendations.
    Tracks user intent, language lock, mood fatigue/transitions, artist frequency, and skip signals.
    """

    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.original_request: str = ""

        # Explicit user constraints / Language Lock
        self.hard_language: Optional[str] = None
        self.user_locked_language: Optional[str] = None
        self.user_locked_language_source: Optional[str] = None
        self.target_mood: str = "auto"

        # Automatic language state
        self.active_language: str = "unknown"
        self.active_language_confidence: float = 0.0
        self.active_language_source: Optional[str] = None
        self.language_established: bool = False
        self.language_switch_candidates: Dict[str, int] = {}

        self.recent_tracks: List[dict] = []
        self.recent_artists: List[str] = []
        self.recent_moods: List[str] = []
        self.skipped_history: List[str] = []
        self.mood_counts: Dict[str, int] = {}

    def set_hard_constraints_from_query(self, query: str):
        q_low = query.lower()
        self.original_request = query

        # 1. Parse Language Hard Filter
        found_lang = False
        for lang_key, info in LANGUAGES.items():
            if info["name"].lower() in q_low or lang_key in q_low:
                self.hard_language = lang_key
                self.user_locked_language = lang_key
                self.active_language = lang_key
                self.active_language_confidence = 1.0
                self.active_language_source = "hard_user_query"
                self.language_established = True
                found_lang = True
                break
        if not found_lang and self.hard_language and self.active_language_source == "hard_user_query":
            self.hard_language = None

        # 2. Parse Initial Mood Target
        for mood_key, info in MOODS.items():
            if info["name"].lower() in q_low or mood_key in q_low or any(k in q_low for k in info["keywords"]):
                self.target_mood = mood_key
                break

    def lock_user_language(self, language: str, source: str = "manual_play"):
        """Strictly locks the session language when a user manually starts or switches a track."""
        if not language or language in ("unknown", "auto"):
            return
        self.user_locked_language = language
        self.active_language = language
        self.active_language_confidence = 1.0
        self.active_language_source = source
        self.language_established = True
        self.language_switch_candidates.clear()

    def establish_initial_language(self, result: LanguageResult) -> bool:
        """Establishes session language from initial track if confidence >= 0.70."""
        if self.hard_language:
            self.user_locked_language = self.hard_language
            return True
        if result and result.language not in ("unknown", "auto") and result.confidence >= 0.70:
            self.user_locked_language = result.language
            self.active_language = result.language
            self.active_language_confidence = result.confidence
            self.active_language_source = result.source
            self.language_established = True
            self.language_switch_candidates.clear()
            return True
        else:
            self.active_language = "unknown"
            self.active_language_confidence = getattr(result, "confidence", 0.0)
            self.active_language_source = getattr(result, "source", None)
            self.language_established = False
            return False

    def update_language_from_track(self, result: LanguageResult, is_first_track: bool = False, is_manual: bool = False):
        """Updates session language state.
        - First track (or manual play) establishes or locks the language.
        - Autoplay is never allowed to drift across languages.
        - Only manual play by a user can switch the active language!
        """
        if not is_manual and not is_first_track:
            return

        if not result or result.language in ("unknown", "auto"):
            return

        if is_manual and (getattr(result, "is_confident", False) or result.confidence >= 0.70):
            if self.active_language_source == "hard_user_query":
                self.hard_language = None
            self.lock_user_language(result.language, source=f"user_manual_{result.source}")
            return

        if self.hard_language:
            self.user_locked_language = self.hard_language
            return

        if is_first_track or not self.language_established:
            self.establish_initial_language(result)
            return

        if result.language == self.active_language:
            self.language_switch_candidates.clear()
            return

    def record_track(self, track: dict, mood: str | None = None, is_manual: bool | None = None):
        """Convenience wrapper for record_played_track."""
        self.record_played_track(track, mood=mood, is_manual=is_manual)

    def record_played_track(self, track: dict, mood: str | None = None, is_manual: bool | None = None):
        if not track:
            return

        from .autoplay_engine import AutoplayEngine

        if mood is None or mood == "auto":
            mood = AutoplayEngine.detect_mood(track.get('title', ''), track.get('uploader') or track.get('artist', ''))

        if is_manual is None:
            is_autoplay = (
                track.get('is_autoplay') is True or
                track.get('is_recommendation') is True or
                'Autoplay' in str(track.get('requested_by', '')) or
                'Trending' in str(track.get('requested_by', ''))
            )
            is_manual = not is_autoplay

        # Deduplicate consecutive identical track recording
        already_last = bool(
            self.recent_tracks and (
                self.recent_tracks[-1] is track or
                (track.get('url') and self.recent_tracks[-1].get('url') == track.get('url')) or
                (track.get('id') and self.recent_tracks[-1].get('id') == track.get('id')) or
                (track.get('title') and self.recent_tracks[-1].get('title') == track.get('title') and track.get('uploader') == self.recent_tracks[-1].get('uploader'))
            )
        )
        if already_last:
            return

        is_first_track = (len(self.recent_tracks) == 0)
        raw_artist = track.get('uploader') or track.get('artist') or ''
        artist = raw_artist.replace(' - Topic', '').replace('VEVO', '').strip()
        self.recent_tracks.append(track)
        if len(self.recent_tracks) > 30:
            self.recent_tracks.pop(0)

        # Detect track language with multi-signal context
        fallback = None if is_manual else (self.user_locked_language or (self.active_language if self.language_established else None))
        req_query = track.get('request_query') or (self.original_request if is_manual else "")
        result = AutoplayEngine.detect_language(
            title=track.get('title', ''),
            uploader=raw_artist,
            fallback_lang=fallback,
            album=track.get('album_name', '') or track.get('album', ''),
            query=req_query,
            track=track
        )

        self.update_language_from_track(result, is_first_track=is_first_track, is_manual=is_manual)

        if artist:
            self.recent_artists.append(artist.lower())
            if len(self.recent_artists) > 15:
                self.recent_artists.pop(0)

        self.recent_moods.append(mood)
        if len(self.recent_moods) > 10:
            self.recent_moods.pop(0)

        self.mood_counts[mood] = self.mood_counts.get(mood, 0) + 1

    def record_skip(self, title: str):
        self.skipped_history.append(normalize_title(title))
        if len(self.skipped_history) > 10:
            self.skipped_history.pop(0)

    def get_next_balanced_mood(self) -> str:
        """Dynamic Mood State Machine (Prevents mood fatigue e.g. Breakup x3 -> Emotional -> Love)."""
        if self.target_mood == "auto" or not self.recent_moods:
            return self.target_mood

        last_3 = self.recent_moods[-3:]
        if len(last_3) >= 3 and all(m == "breakup" for m in last_3):
            return "emotional" if random.random() > 0.5 else "love"
        if len(last_3) >= 3 and all(m == "sad" for m in last_3):
            return "melody"
        if len(last_3) >= 3 and all(m == "mass" for m in last_3):
            return "party"

        return self.target_mood
