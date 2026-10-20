from __future__ import annotations
import os
import json
import time
import asyncio
import logging
from typing import Optional, Dict, Any, List
import aiosqlite

logger = logging.getLogger("zyuna.telemetry")

class MusicTelemetryEvent:
    """Canonical behavioral, search, and operational events for Zyuna Music."""
    PLAY_REQUEST = "PLAY_REQUEST"
    SEARCH_IMPRESSION = "SEARCH_IMPRESSION"
    TRACK_RESOLVED = "TRACK_RESOLVED"
    PLAY_STARTED = "PLAY_STARTED"
    PLAY_COMPLETED = "PLAY_COMPLETED"
    PLAY_DURATION = "PLAY_DURATION"
    SKIP = "SKIP"
    MANUAL_NEXT = "MANUAL_NEXT"
    REPLAY = "REPLAY"
    LIKE = "LIKE"
    QUEUE_ADD = "QUEUE_ADD"
    RECOMMENDATION_ACCEPTED = "RECOMMENDATION_ACCEPTED"
    RECOMMENDATION_SKIPPED = "RECOMMENDATION_SKIPPED"


class InteractionLogger:
    """Non-blocking, asynchronous dual-plane interaction logging for Zyuna's ML Recommender.
    Records behavioral events into SQLite WAL for offline ranking.
    Zero playback blocking: events are queued in-memory and batch-written in background.
    """

    _instance: Optional[InteractionLogger] = None
    DB_PATH = "db/ml_interactions.db"

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=20000)
        self._worker_task: Optional[asyncio.Task] = None
        self._is_running: bool = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @classmethod
    def get_instance(cls, db_path: str = DB_PATH) -> InteractionLogger:
        if cls._instance is None:
            cls._instance = InteractionLogger(db_path=db_path)
        return cls._instance

    async def initialize(self):
        """Initializes SQLite WAL database with schema and starts worker."""
        if self._is_running:
            return

        try:
            self._loop = asyncio.get_running_loop()
            os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA journal_mode=WAL;")
                await db.execute("PRAGMA synchronous=NORMAL;")
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS interactions (
                        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        guild_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        session_id TEXT,
                        event_type TEXT NOT NULL,
                        track_id TEXT,
                        title TEXT,
                        artist TEXT,
                        album TEXT,
                        language TEXT,
                        mood TEXT,
                        queue_mode TEXT,
                        source TEXT,
                        position INTEGER DEFAULT 0,
                        played_seconds REAL DEFAULT 0.0,
                        track_duration REAL DEFAULT 0.0,
                        completion_ratio REAL DEFAULT 0.0,
                        latency_ms REAL DEFAULT 0.0,
                        metadata TEXT
                    )
                """)
                await db.execute("CREATE INDEX IF NOT EXISTS idx_interactions_user ON interactions(user_id);")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_interactions_event ON interactions(event_type);")
                await db.commit()

            self._is_running = True
            self._worker_task = asyncio.create_task(self._batch_worker())
            logger.info("[ML TELEMETRY] Initialized SQLite WAL logger.")
        except Exception as e:
            logger.error(f"[ML TELEMETRY INIT ERROR] {e}")

    async def log_event(
        self,
        event_type: str,
        guild_id: int = 0,
        user_id: int = 0,
        track_id: str = "",
        title: str = "",
        artist: str = "",
        album: str = "",
        language: str = "",
        mood: str = "",
        queue_mode: str = "track",
        source: str = "",
        position: int = 0,
        played_seconds: float = 0.0,
        track_duration: float = 0.0,
        latency_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Enqueues an interaction event for asynchronous background persistence."""
        if not self._is_running:
            return

        ratio = (played_seconds / track_duration) if track_duration > 0 else 0.0
        event = (
            time.time(),
            guild_id,
            user_id,
            f"{guild_id}_{int(time.time() // 3600)}",
            event_type,
            track_id or "",
            title or "",
            artist or "",
            album or "",
            language or "",
            mood or "",
            queue_mode or "track",
            source or "",
            position,
            float(played_seconds),
            float(track_duration),
            float(ratio),
            float(latency_ms),
            json.dumps(metadata or {})
        )

        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            pass

    async def _batch_worker(self):
        """Background worker that flushes queued events to SQLite in batches."""
        batch: List[tuple] = []
        while self._is_running:
            try:
                try:
                    event = await asyncio.wait_for(self._queue.get(), timeout=2.0)
                    batch.append(event)
                    self._queue.task_done()
                except asyncio.TimeoutError:
                    pass

                while len(batch) < 100 and not self._queue.empty():
                    batch.append(self._queue.get_nowait())
                    self._queue.task_done()

                if batch:
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.executemany("""
                            INSERT INTO interactions (
                                timestamp, guild_id, user_id, session_id, event_type,
                                track_id, title, artist, album, language, mood,
                                queue_mode, source, position, played_seconds,
                                track_duration, completion_ratio, latency_ms, metadata
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, batch)
                        await db.commit()
                    batch.clear()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ML TELEMETRY WORKER ERROR] {e}")
                batch.clear()
                await asyncio.sleep(1.0)

    async def get_user_artist_affinity(self, user_id: int) -> Dict[str, Dict[str, int]]:
        """Queries historical interaction statistics for a user to personalize ranking."""
        stats: Dict[str, Dict[str, int]] = {}
        if not os.path.isfile(self.db_path):
            return stats

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT LOWER(artist), event_type, COUNT(*) 
                    FROM interactions 
                    WHERE user_id = ? AND artist != ''
                    GROUP BY LOWER(artist), event_type
                """, (user_id,))
                rows = await cursor.fetchall()
                for artist, event, count in rows:
                    if artist not in stats:
                        stats[artist] = {"plays": 0, "skips": 0}
                    if event in (MusicTelemetryEvent.PLAY_STARTED, MusicTelemetryEvent.PLAY_COMPLETED):
                        stats[artist]["plays"] += count
                    elif event == MusicTelemetryEvent.SKIP:
                        stats[artist]["skips"] += count
        except Exception as e:
            logger.error(f"[ML AFFINITY QUERY ERROR] {e}")

        return stats

    async def shutdown(self):
        """Clean shutdown of background worker."""
        self._is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
