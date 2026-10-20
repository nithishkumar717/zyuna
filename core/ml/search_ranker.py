from __future__ import annotations

import os
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    lgb = None
    HAS_LIGHTGBM = False

from utils.music_intelligence.language_match import (
    best_similarity,
    contains_tamil_script,
    is_tamil_context,
    matching_forms,
    normalize_search_text,
    token_recall,
)


class SearchFeatureExtractor:
    """Features for matching a text search query to one playable song candidate."""

    QUERY_NOISE = {
        "play", "please", "listen", "to", "the", "youtube", "yt", "music",
        "song", "songs", "track", "audio", "video", "full", "original",
        "official", "by", "on", "from", "in", "of",
    }

    FEATURE_NAMES = [
        "query_title_recall",
        "query_artist_recall",
        "query_identity_recall",
        "query_title_precision",
        "query_title_similarity",
        "title_exact_match",
        "artist_exact_match",
        "artist_match_score",
        "duration_match_score",
        "duration_available",
        "heuristic_match_score",
        "heuristic_high_confidence",
        "candidate_rank_norm",
        "title_token_count",
        "title_has_audio_marker",
        "channel_looks_official",
        "source_is_youtube_music",
        "source_is_youtube",
        "query_has_tamil_script",
        "candidate_has_tamil_script",
        "query_has_tamil_context",
        "candidate_has_tamil_context",
        "tamil_phonetic_similarity",
        "romanized_exact_match",
    ]

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {token for token in normalize_search_text(text).split() if len(token) > 1}

    @classmethod
    def extract(cls, query: str, candidate: dict, source_rank: int = 0,
                target_artist: str = "", expected_duration: int = 0) -> List[float]:
        from utils.music_intelligence.validator import SongValidator

        title = str(candidate.get("song_name") or candidate.get("title") or "")
        artist = str(candidate.get("artists") or candidate.get("artist") or candidate.get("uploader") or "")
        uploader = str(candidate.get("uploader") or candidate.get("channel") or "")
        identity = f"{title} {artist} {uploader}"
        title_tokens = cls._tokens(title)

        query_recall = token_recall(query, title, ignored=cls.QUERY_NOISE)
        query_artist_recall = token_recall(target_artist, identity)
        query_identity_recall = token_recall(query, identity, ignored=cls.QUERY_NOISE)
        title_precision = token_recall(title, query, ignored=cls.QUERY_NOISE)
        tamil_context = is_tamil_context(query, [candidate])
        exact_title = any(
            left == right
            for left in matching_forms(query, tamil_aware=tamil_context)
            for right in matching_forms(title, tamil_aware=tamil_context)
        )
        exact_artist = bool(target_artist) and any(
            left == right
            for left in matching_forms(target_artist, tamil_aware=tamil_context)
            for right in matching_forms(artist, tamil_aware=tamil_context)
        )

        duration = float(candidate.get("duration") or 0.0)
        heuristic_score, confidence = SongValidator.validate_and_score(
            candidate,
            target_title=query,
            target_artist=target_artist,
            expected_duration=expected_duration,
        )
        duration_score = 0.0
        if expected_duration > 0 and duration > 0:
            duration_score = max(0.0, 1.0 - abs(duration - expected_duration) / max(expected_duration, 1.0))

        clean_query = normalize_search_text(query)
        clean_title = normalize_search_text(title)
        clean_artist = normalize_search_text(artist)
        q_artist = normalize_search_text(target_artist)
        uploader_text = normalize_search_text(uploader)
        source = str(candidate.get("source") or "").casefold()
        audio_markers = ("official audio", "audio song", "lyric video", "lyrics video", "topic")
        official_markers = ("vevo", "records", "music", "entertainment", "topic", "official")

        candidate_is_tamil = is_tamil_context("", [candidate])
        query_is_tamil = is_tamil_context(query)
        phonetic_similarity = best_similarity(query, title, tamil_aware=tamil_context)
        romanized_exact = any(
            left == right
            for left in matching_forms(query, tamil_aware=tamil_context)
            for right in matching_forms(title, tamil_aware=tamil_context)
        )

        return [
            query_recall,
            query_artist_recall,
            query_identity_recall,
            title_precision,
            max(phonetic_similarity, SequenceMatcher(None, clean_query, clean_title).ratio() if clean_query and clean_title else 0.0),
            float(exact_title),
            float(exact_artist),
            token_recall(target_artist, identity),
            duration_score,
            float(duration > 0),
            float(heuristic_score) / 100.0,
            float(confidence == "HIGH"),
            1.0 / (1.0 + max(0, source_rank)),
            min(1.0, len(title_tokens) / 12.0),
            float(any(marker in clean_title for marker in audio_markers)),
            float(any(marker in uploader_text for marker in official_markers)),
            float("ytm" in source or "youtube music" in source),
            float(source == "youtube"),
            float(contains_tamil_script(query)),
            float(contains_tamil_script(identity)),
            float(query_is_tamil),
            float(candidate_is_tamil),
            phonetic_similarity,
            float(romanized_exact),
        ]

    @classmethod
    def extract_batch(cls, query: str, candidates: List[dict], target_artist: str = "",
                      expected_duration: int = 0, source_ranks: Optional[List[int]] = None) -> Any:
        ranks = source_ranks or list(range(len(candidates)))
        rows = [
            cls.extract(query, candidate, ranks[index], target_artist, expected_duration)
            for index, candidate in enumerate(candidates)
        ]
        if HAS_NUMPY and np is not None:
            return np.asarray(rows, dtype=np.float32)
        return rows


class SearchRankingModel:
    """Search reranker ensuring official audio quality and identity match."""

    MODEL_PATH = "data/ml/zyuna_search_ranker.booster"

    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self._booster = None
        if HAS_LIGHTGBM and os.path.isfile(model_path):
            try:
                self._booster = lgb.Booster(model_file=model_path)
            except Exception as exc:
                print(f"[ML SEARCH MODEL LOAD ERROR] {exc}")

    @staticmethod
    def candidate_key(candidate: dict) -> str:
        for key in ("yt_video_id", "id", "spotify_id", "url"):
            value = str(candidate.get(key) or "").strip()
            if value:
                return value
        title = normalize_search_text(candidate.get("song_name") or candidate.get("title") or "")
        artist = normalize_search_text(candidate.get("artists") or candidate.get("artist") or candidate.get("uploader") or "")
        return f"{title}|{artist}" if title or artist else ""

    def rank_candidates(self, query: str, candidates: List[dict], target_artist: str = "",
                        expected_duration: int = 0) -> List[Tuple[float, dict]]:
        if not candidates:
            return []

        from utils.music_intelligence.validator import SongValidator

        valid: List[Tuple[float, dict, int]] = []
        for source_rank, candidate in enumerate(candidates):
            if not isinstance(candidate, dict) or not candidate.get("title"):
                continue
            baseline, confidence = SongValidator.validate_and_score(
                candidate,
                target_title=query,
                target_artist=target_artist,
                expected_duration=expected_duration,
            )
            if confidence in ("HIGH", "MEDIUM") and baseline > 0:
                valid.append((float(baseline), candidate, source_rank))

        if not valid:
            return []
        valid.sort(key=lambda item: item[0], reverse=True)

        if self._booster is None or not HAS_LIGHTGBM:
            return [(score, candidate) for score, candidate, _ in valid]

        try:
            features = SearchFeatureExtractor.extract_batch(
                query,
                [candidate for _, candidate, _ in valid],
                target_artist,
                expected_duration,
                source_ranks=[rank for _, _, rank in valid],
            )
            model_scores = [float(value) for value in self._booster.predict(features)]
            baselines = [score for score, _, _ in valid]
            low_base, high_base = min(baselines), max(baselines)
            reranked = []
            for (baseline, candidate, _), model_score in zip(valid, model_scores):
                base_norm = (baseline - low_base) / (high_base - low_base) if high_base - low_base > 1e-6 else 0.5
                model_probability = max(0.0, min(1.0, model_score))
                blended = 100.0 * (0.80 * base_norm + 0.20 * model_probability)
                reranked.append((blended, candidate))
            reranked.sort(key=lambda item: item[0], reverse=True)
            return reranked
        except Exception as exc:
            print(f"[ML SEARCH RANK ERROR] {exc}")
            return [(score, candidate) for score, candidate, _ in valid]
