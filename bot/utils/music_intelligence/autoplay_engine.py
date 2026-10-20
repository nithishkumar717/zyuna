from __future__ import annotations
import re
import datetime
from typing import Optional, List, Dict, Any, Set
from .constants import (
    LANGUAGES,
    MOODS,
    LANGUAGE_VERSION_PATTERNS,
    REGIONAL_CHANNEL_PATTERNS,
    SOUTH_MULTI_REGIONAL_LABELS,
    PAN_INDIAN_ARTISTS,
    PRIMARY_ARTIST_BASE_LANGUAGE,
    TAMIL_EXCLUSIVE_MARKERS,
    TELUGU_EXCLUSIVE_MARKERS,
    HINDI_EXCLUSIVE_MARKERS,
    MALAYALAM_EXCLUSIVE_MARKERS,
    KANNADA_EXCLUSIVE_MARKERS,
    normalize_title
)
from .session_state import LanguageResult, MusicSessionState

class AutoplayEngine:
    """Intelligent Autoplay & Recommendation Engine with Language & Mood analysis."""

    @classmethod
    def detect_language(
        cls,
        title: str = "",
        uploader: str = "",
        fallback_lang: Optional[str] = None,
        album: str = "",
        query: str = "",
        track: Optional[dict] = None,
        *args, **kwargs
    ) -> LanguageResult:
        title_lower = (title or "").lower()
        uploader_lower = (uploader or "").lower()
        album_lower = (album or "").lower()
        query_lower = (query or "").lower()

        scores: Dict[str, float] = {k: 0.0 for k in LANGUAGES}

        # 1. Explicit Version Tag Match (highest priority: 0.999)
        for lang_key, pattern in LANGUAGE_VERSION_PATTERNS.items():
            if pattern.search(title_lower) or pattern.search(album_lower) or pattern.search(query_lower):
                scores[lang_key] = 0.999
                return LanguageResult(
                    language=lang_key,
                    confidence=0.999,
                    source="explicit_version_tag",
                    scores=scores
                )

        # 2. Unicode script detection (highest reliability: 0.99)
        for char in f"{title} {uploader} {album}":
            code = ord(char)
            for lang_key, info in LANGUAGES.items():
                if info.get("unicode"):
                    start, end = info["unicode"]
                    if start <= code <= end:
                        scores[lang_key] = 0.99
                        return LanguageResult(
                            language=lang_key,
                            confidence=0.99,
                            source="unicode_script",
                            scores=scores
                        )

        # 3. Explicit Western Pop Artists / Channels
        western_markers = [
            "taylor swift", "ed sheeran", "drake", "the weeknd", "billie eilish",
            "justin bieber", "dua lipa", "dualipa", "eminem", "coldplay",
            "alan walker", "post malone", "rihanna", "adele", "maroon 5",
            "charlie puth", "shawn mendes", "olivia rodrigo", "sabrina carpenter",
            "travis scott", "kendrick lamar", "sza", "ariana grande", "katy perry",
            "bruno mars", "brunomars", "lady gaga", "beyonce", "shakira", "imagine dragons",
            "daft punk", "the beatles", "queen", "michael jackson", "avicii",
            "marshmello", "chainsmokers", "david guetta", "calvin harris", "one direction",
            "harry styles", "zayn", "selena gomez", "camila cabello", "cardi b", "nicki minaj"
        ]
        is_explicit_western = any(wm in uploader_lower or wm in title_lower for wm in western_markers)
        if is_explicit_western:
            scores["english"] = 0.95
            return LanguageResult(
                language="english",
                confidence=0.95,
                source="explicit_western_artist",
                scores=scores
            )

        # 4. Regional Marker Matching across title, album, uploader
        regional_marker_map = [
            ("tamil", TAMIL_EXCLUSIVE_MARKERS),
            ("telugu", TELUGU_EXCLUSIVE_MARKERS),
            ("hindi", HINDI_EXCLUSIVE_MARKERS),
            ("malayalam", MALAYALAM_EXCLUSIVE_MARKERS),
            ("kannada", KANNADA_EXCLUSIVE_MARKERS),
        ]
        target_fields = [title_lower, album_lower, uploader_lower]

        for lang_key, markers in regional_marker_map:
            for m in markers:
                pat = r'\b' + re.escape(m) + r'\b'
                matched = False
                for fld in target_fields:
                    if fld and re.search(pat, fld):
                        scores[lang_key] = max(scores.get(lang_key, 0.0), 0.95)
                        matched = True
                        break
                if matched:
                    break

        # Regional phonetic suffixes
        if re.search(r'\b[a-z]+(male|aamale|aaga|oodu|ukku|ikku|aanen|aadha|vaya|vayaa|kulla|kulle|kooda|thanae|dhaane)\b', title_lower):
            scores["tamil"] = max(scores.get("tamil", 0.0), 0.92)
        if re.search(r'\b[a-z]+(gadu|thodu|amma|ayya|kalu|gunde|lone|thoone)\b', title_lower):
            scores["telugu"] = max(scores.get("telugu", 0.0), 0.92)

        best_linguistic = max(scores, key=scores.get) if any(v > 0 for v in scores.values()) else None
        if best_linguistic and scores[best_linguistic] >= 0.90:
            return LanguageResult(
                language=best_linguistic,
                confidence=scores[best_linguistic],
                source="regional_linguistic_match",
                scores=scores
            )

        # 5. Dedicated Regional Channels
        for lang_key, pat in REGIONAL_CHANNEL_PATTERNS.items():
            if pat.search(uploader_lower):
                scores[lang_key] = max(scores.get(lang_key, 0.0), 0.96)
                if lang_key in ("tamil", "telugu", "malayalam", "kannada", "punjabi"):
                    return LanguageResult(
                        language=lang_key,
                        confidence=0.96,
                        source="regional_channel",
                        scores=scores
                    )

        # 6. South Indian Multi-Language Labels
        if SOUTH_MULTI_REGIONAL_LABELS.search(uploader_lower):
            for south_l in ("tamil", "telugu", "malayalam", "kannada"):
                if scores.get(south_l, 0.0) > 0.0:
                    scores[south_l] = min(scores[south_l] + 0.10, 0.99)

        # 7. Check Primary Artist Base Language
        for artist_name, base_lang in PRIMARY_ARTIST_BASE_LANGUAGE.items():
            if artist_name in uploader_lower or artist_name in title_lower:
                scores[base_lang] = max(scores.get(base_lang, 0.0), 0.85)

        # 8. General Regional Keywords from LANGUAGES dictionary
        for lang_key, info in LANGUAGES.items():
            if lang_key == "english":
                continue
            for kw in info["keywords"]:
                if re.search(r'\b' + re.escape(kw) + r'\b', title_lower) or re.search(r'\b' + re.escape(kw) + r'\b', uploader_lower):
                    scores[lang_key] = max(scores.get(lang_key, 0.0), 0.80)
                    break

        best_candidate = max(scores, key=scores.get) if any(v > 0 for v in scores.values()) else None
        if best_candidate and scores[best_candidate] >= 0.70:
            return LanguageResult(
                language=best_candidate,
                confidence=scores[best_candidate],
                source="regional_keyword",
                scores=scores
            )

        # 9. Fallback if established in session
        if fallback_lang and fallback_lang in LANGUAGES:
            scores[fallback_lang] = 0.50
            return LanguageResult(
                language=fallback_lang,
                confidence=0.50,
                source="session_fallback",
                scores=scores
            )

        return LanguageResult(
            language="english",
            confidence=0.30,
            source="default",
            scores=scores
        )

    @classmethod
    def detect_mood(cls, title: str, uploader: str) -> str:
        text = f"{title} {uploader}".lower()
        for mood_key, info in MOODS.items():
            for kw in info["keywords"]:
                if re.search(r'\b' + re.escape(kw) + r'\b', text):
                    return mood_key
        if any(w in text for w in ["gana", "kuthu", "mass", "fight", "bgm", "theme", "beat", "power", "energy"]):
            return "mass"
        if any(w in text for w in ["love", "melody", "duet", "kadhal", "pyar", "ishq", "crush"]):
            return "love"
        if any(w in text for w in ["sad", "soga", "tears", "crying", "alone", "pain", "broken"]):
            return "sad"
        return "melody"

    @classmethod
    def generate_smart_queries(cls, current_song: dict, lang_pref: str = "auto", mood_pref: str = "auto") -> list[str]:
        current_title = current_song.get('title', '')
        current_uploader = current_song.get('uploader') or current_song.get('artist', '')

        if lang_pref not in ("auto", "unknown"):
            lang_key = lang_pref
        else:
            lang_key = cls.detect_language(current_title, current_uploader).language

        if mood_pref != "auto":
            mood_key = mood_pref
        else:
            mood_key = cls.detect_mood(current_title, current_uploader)

        lang_name = LANGUAGES.get(lang_key, {}).get("name", "English")
        mood_info = MOODS.get(mood_key, {})
        mood_name = mood_info.get("name", "Melody")

        clean_title = re.sub(r'[\(\[].*?[\)\]]', '', current_title).strip()
        artist = current_uploader.replace(' - Topic', '').replace('VEVO', '').replace('Official', '').strip()
        if not artist or artist.lower() in ['youtube uploader', 'artist / web', 'artist', 'spotify']:
            if '-' in current_title:
                artist = current_title.split('-')[0].strip()
            else:
                artist = clean_title

        current_year = datetime.datetime.now().year
        queries = []

        if artist and clean_title and artist.lower() not in clean_title.lower():
            if lang_key and lang_key not in ("english", "auto", "unknown"):
                queries.append(f"{clean_title} {artist}")
                queries.append(f"{artist} {lang_name} songs official audio")
                queries.append(f"{artist} {lang_name} hits")
                queries.append(f"songs like {clean_title} {lang_name}")
            else:
                queries.append(f"songs like {clean_title} {artist}")
                queries.append(f"{artist} latest song official")
                queries.append(f"{artist} radio")
                queries.append(f"{artist} trending songs {current_year}")
                queries.append(f"{artist} top tracks official")
        elif clean_title:
            if lang_key and lang_key not in ("english", "auto", "unknown"):
                queries.append(f"songs like {clean_title} {lang_name}")
                queries.append(f"{clean_title} {lang_name} radio")
            else:
                queries.append(f"songs like {clean_title}")
                queries.append(f"{clean_title} radio")

        if lang_key and lang_key not in ("english", "auto", "unknown"):
            queries.append(f"{lang_name} trending songs {current_year} official audio")
            queries.append(f"latest {lang_name} new releases {current_year}")
            queries.append(f"{lang_name} {mood_name} hit songs official audio")
            queries.append(f"top viral {lang_name} songs {current_year}")
            queries.append(f"{lang_name} top songs official audio")
        elif lang_key == "english":
            queries.append(f"trending music {current_year} official audio")
            queries.append(f"billboard hot 100 new hits official")
            queries.append(f"latest popular songs {current_year}")
            queries.append(f"{mood_name} hit songs official audio")
            queries.append(f"top indie pop official audio")
        else:
            if clean_title:
                queries.append(f"songs like {clean_title}")
            if artist:
                queries.append(f"{artist} top songs official audio")
                queries.append(f"{artist} trending songs {current_year}")

        return queries

    @classmethod
    def language_compatible(cls, session: MusicSessionState, candidate_lang: LanguageResult | str | dict) -> bool:
        """Enforces that candidate matches session locked/active language."""
        if isinstance(candidate_lang, LanguageResult):
            c_lang = candidate_lang.language
        elif isinstance(candidate_lang, dict):
            c_lang = candidate_lang.get('language', 'unknown')
        else:
            c_lang = str(candidate_lang)

        target = session.user_locked_language or session.hard_language
        if not target and session.language_established:
            target = session.active_language

        if not target or target in ("unknown", "auto", "english"):
            return True

        return c_lang == target

    @classmethod
    def is_fuzzy_duplicate(cls, candidate: Any, played_history_set: set) -> bool:
        """Checks if track or similar title was recently played."""
        if not candidate or not played_history_set:
            return False

        if isinstance(candidate, dict):
            t_id = candidate.get('id') or candidate.get('yt_video_id') or candidate.get('url') or ''
            title = candidate.get('title', '')
        else:
            t_id = getattr(candidate, 'identifier', '') or getattr(candidate, 'uri', '')
            title = getattr(candidate, 'title', '')

        if t_id and t_id in played_history_set:
            return True

        norm = normalize_title(title)
        if norm and norm in played_history_set:
            return True

        return False
