from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import time
from typing import Callable, Iterator

import numpy as np

from .cache_models import (
    ANSWER_CACHE_SCHEMA_VERSION,
    CACHE_TTL_SECONDS,
    MODERATION_VERSION,
    PROMPT_VERSION,
    AnswerCacheMetrics,
    CacheContext,
    CachedAnswerSummary,
    CachedResponse,
    DEFAULT_SEMANTIC_THRESHOLD,
)
from .local_embeddings import EmbeddingProvider
from .models import Evidence
from .retrieval import normalize


_QUESTION_PREVIEW_LIMIT = 96


class AnswerCache:
    def __init__(
        self,
        db_path: str | Path,
        embedder: EmbeddingProvider,
        now: Callable[[], float] = time.time,
        ttl_seconds: int = CACHE_TTL_SECONDS,
        semantic_threshold: float = DEFAULT_SEMANTIC_THRESHOLD,
    ):
        if not 0.90 <= semantic_threshold <= 1.0:
            raise ValueError("El umbral semantico debe estar entre 0.90 y 1.0")
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedder = embedder
        self.now = now
        self.ttl_seconds = ttl_seconds
        self.semantic_threshold = semantic_threshold
        self._ensure_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.db_path)
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _ensure_schema(self) -> None:
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS cache_meta "
                "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            version_row = db.execute(
                "SELECT value FROM cache_meta WHERE key='answer_schema_version'"
            ).fetchone()
            if version_row and int(version_row[0]) > ANSWER_CACHE_SCHEMA_VERSION:
                raise RuntimeError("Version de respuestas incompatible")
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS answers (
                    id INTEGER PRIMARY KEY,
                    profile_hash TEXT NOT NULL,
                    cv_hash TEXT NOT NULL,
                    response_route TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    moderation_version TEXT NOT NULL,
                    question_norm TEXT NOT NULL,
                    question_vector BLOB NOT NULL,
                    vector_dim INTEGER NOT NULL,
                    answer TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    exact_hit_count INTEGER NOT NULL DEFAULT 0,
                    semantic_hit_count INTEGER NOT NULL DEFAULT 0,
                    last_hit_at REAL,
                    last_match_type TEXT,
                    UNIQUE(
                        profile_hash, cv_hash, response_route, prompt_version,
                        moderation_version, question_norm
                    )
                )
                """
            )
            columns = {
                str(row[1]) for row in db.execute("PRAGMA table_info(answers)").fetchall()
            }
            migrations = {
                "exact_hit_count": "INTEGER NOT NULL DEFAULT 0",
                "semantic_hit_count": "INTEGER NOT NULL DEFAULT 0",
                "last_hit_at": "REAL",
                "last_match_type": "TEXT",
            }
            for column, declaration in migrations.items():
                if column not in columns:
                    db.execute(f"ALTER TABLE answers ADD COLUMN {column} {declaration}")
            db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_answers_active_context
                ON answers(
                    profile_hash, cv_hash, prompt_version,
                    moderation_version, expires_at
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS answer_cache_metrics (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    exact_hits INTEGER NOT NULL DEFAULT 0 CHECK(exact_hits >= 0),
                    semantic_hits INTEGER NOT NULL DEFAULT 0 CHECK(semantic_hits >= 0),
                    misses INTEGER NOT NULL DEFAULT 0 CHECK(misses >= 0)
                )
                """
            )
            db.execute(
                "INSERT OR IGNORE INTO answer_cache_metrics(id) VALUES (1)"
            )
            db.execute(
                """
                INSERT INTO cache_meta(key, value)
                VALUES ('answer_schema_version', ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (str(ANSWER_CACHE_SCHEMA_VERSION),),
            )

    def cleanup_expired(self) -> int:
        cutoff = self.now()
        with self._connect() as db:
            count = int(
                db.execute(
                    "SELECT COUNT(*) FROM answers WHERE expires_at <= ?", (cutoff,)
                ).fetchone()[0]
            )
            db.execute("DELETE FROM answers WHERE expires_at <= ?", (cutoff,))
        return count

    @staticmethod
    def _serialize_evidence(evidence: list[Evidence]) -> str:
        return json.dumps(
            [
                {"page": int(item.page), "text": item.text[:10000], "score": float(item.score)}
                for item in evidence[:16]
            ],
            ensure_ascii=False,
        )

    @staticmethod
    def _deserialize_evidence(raw: str) -> tuple[Evidence, ...]:
        data = json.loads(raw)
        if not isinstance(data, list) or len(data) > 16:
            raise ValueError("Evidencia cacheada invalida")
        items: list[Evidence] = []
        for value in data:
            if not isinstance(value, dict):
                raise ValueError("Evidencia cacheada invalida")
            page = int(value["page"])
            text = str(value["text"])
            score = float(value.get("score", 0.0))
            if page < 1 or len(text) > 10000:
                raise ValueError("Evidencia cacheada fuera de limites")
            items.append(Evidence(page=page, text=text, score=score))
        return tuple(items)

    @staticmethod
    def _question_preview(question_norm: str) -> str:
        compact = " ".join(str(question_norm).split())
        if len(compact) <= _QUESTION_PREVIEW_LIMIT:
            return compact
        return compact[: _QUESTION_PREVIEW_LIMIT - 1].rstrip() + "…"

    def get(self, context: CacheContext, question: str) -> CachedResponse | None:
        self.cleanup_expired()
        question_norm = normalize(question)
        scope = (
            context.profile_hash,
            context.cv_hash,
            context.response_route,
            context.prompt_version,
            context.moderation_version,
            self.now(),
        )
        with self._connect() as db:
            exact = db.execute(
                """
                SELECT id, answer, evidence_json FROM answers
                WHERE profile_hash=? AND cv_hash=? AND response_route=?
                  AND prompt_version=? AND moderation_version=? AND expires_at>?
                  AND question_norm=?
                """,
                scope + (question_norm,),
            ).fetchone()
            if exact:
                try:
                    return CachedResponse(
                        answer=exact[1],
                        evidence=self._deserialize_evidence(exact[2]),
                        match_type="exact",
                        similarity=1.0,
                        entry_id=int(exact[0]),
                    )
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    return None
            rows = db.execute(
                """
                SELECT id, question_vector, vector_dim, answer, evidence_json
                FROM answers
                WHERE profile_hash=? AND cv_hash=? AND response_route=?
                  AND prompt_version=? AND moderation_version=? AND expires_at>?
                """,
                scope,
            ).fetchall()
        if not rows:
            return None
        try:
            query = np.asarray(self.embedder.embed_query(question), dtype=np.float32)
        except (OSError, RuntimeError, ValueError):
            return None
        best = None
        best_similarity = -1.0
        for entry_id, raw_vector, dimension, answer, evidence_json in rows:
            vector = np.frombuffer(raw_vector, dtype=np.float32)
            if len(vector) != int(dimension) or len(vector) != len(query):
                continue
            similarity = float(np.dot(query, vector))
            if similarity > best_similarity:
                best = (entry_id, answer, evidence_json)
                best_similarity = similarity
        if best is None or best_similarity < self.semantic_threshold:
            return None
        try:
            return CachedResponse(
                answer=best[1],
                evidence=self._deserialize_evidence(best[2]),
                match_type="semantic",
                similarity=best_similarity,
                entry_id=int(best[0]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    def put(
        self,
        context: CacheContext,
        question: str,
        answer: str,
        evidence: list[Evidence],
    ) -> bool:
        if not answer.strip() or not evidence:
            return False
        try:
            vector = np.asarray(self.embedder.embed_query(question), dtype=np.float32)
            if vector.ndim != 1 or vector.size <= 0:
                return False
            created_at = self.now()
            with self._connect() as db:
                db.execute(
                    """
                    INSERT INTO answers(
                        profile_hash, cv_hash, response_route, prompt_version,
                        moderation_version, question_norm, question_vector, vector_dim,
                        answer, evidence_json, created_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(
                        profile_hash, cv_hash, response_route, prompt_version,
                        moderation_version, question_norm
                    ) DO UPDATE SET
                        question_vector=excluded.question_vector,
                        vector_dim=excluded.vector_dim,
                        answer=excluded.answer,
                        evidence_json=excluded.evidence_json,
                        created_at=excluded.created_at,
                        expires_at=excluded.expires_at
                    """,
                    (
                        context.profile_hash,
                        context.cv_hash,
                        context.response_route,
                        context.prompt_version,
                        context.moderation_version,
                        normalize(question),
                        np.ascontiguousarray(vector, dtype=np.float32).tobytes(),
                        int(vector.size),
                        answer,
                        self._serialize_evidence(evidence),
                        created_at,
                        created_at + self.ttl_seconds,
                    ),
                )
            return True
        except (OSError, RuntimeError, sqlite3.Error, ValueError):
            return False

    def list_active(
        self,
        profile_hash: str,
        cv_hash: str,
        prompt_version: str = PROMPT_VERSION,
        moderation_version: str = MODERATION_VERSION,
        limit: int = 50,
    ) -> list[CachedAnswerSummary]:
        self.cleanup_expired()
        safe_limit = max(1, min(int(limit), 50))
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT id, question_norm, response_route, created_at, expires_at,
                       exact_hit_count, semantic_hit_count
                FROM answers
                WHERE profile_hash=? AND cv_hash=?
                  AND prompt_version=? AND moderation_version=? AND expires_at>?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (
                    profile_hash,
                    cv_hash,
                    prompt_version,
                    moderation_version,
                    self.now(),
                    safe_limit,
                ),
            ).fetchall()
        return [
            CachedAnswerSummary(
                entry_id=int(row[0]),
                question_preview=self._question_preview(row[1]),
                response_route=str(row[2]),
                created_at=float(row[3]),
                expires_at=float(row[4]),
                exact_hit_count=int(row[5]),
                semantic_hit_count=int(row[6]),
            )
            for row in rows
        ]

    def record_hit(self, entry_id: int, context: CacheContext, match_type: str) -> bool:
        columns = {
            "exact": ("exact_hit_count", "exact_hits"),
            "semantic": ("semantic_hit_count", "semantic_hits"),
        }
        if match_type not in columns:
            return False
        answer_column, metric_column = columns[match_type]
        hit_at = self.now()
        with self._connect() as db:
            cursor = db.execute(
                f"""
                UPDATE answers
                SET {answer_column}={answer_column}+1,
                    last_hit_at=?, last_match_type=?
                WHERE id=? AND profile_hash=? AND cv_hash=? AND response_route=?
                  AND prompt_version=? AND moderation_version=? AND expires_at>?
                """,
                (
                    hit_at,
                    match_type,
                    int(entry_id),
                    context.profile_hash,
                    context.cv_hash,
                    context.response_route,
                    context.prompt_version,
                    context.moderation_version,
                    hit_at,
                ),
            )
            if cursor.rowcount != 1:
                return False
            db.execute(
                f"UPDATE answer_cache_metrics SET {metric_column}={metric_column}+1 WHERE id=1"
            )
        return True

    def record_miss(self) -> None:
        with self._connect() as db:
            db.execute(
                "UPDATE answer_cache_metrics SET misses=misses+1 WHERE id=1"
            )

    def metrics(self) -> AnswerCacheMetrics:
        with self._connect() as db:
            row = db.execute(
                "SELECT exact_hits, semantic_hits, misses "
                "FROM answer_cache_metrics WHERE id=1"
            ).fetchone()
        return AnswerCacheMetrics(
            exact_hits=int(row[0]),
            semantic_hits=int(row[1]),
            misses=int(row[2]),
        )

    def delete_entry(self, entry_id: int, profile_hash: str, cv_hash: str) -> bool:
        self.cleanup_expired()
        with self._connect() as db:
            cursor = db.execute(
                "DELETE FROM answers WHERE id=? AND profile_hash=? AND cv_hash=?",
                (int(entry_id), profile_hash, cv_hash),
            )
        return cursor.rowcount == 1

    def clear(self) -> int:
        with self._connect() as db:
            count = int(db.execute("SELECT COUNT(*) FROM answers").fetchone()[0])
            db.execute("DELETE FROM answers")
            db.execute(
                """
                UPDATE answer_cache_metrics
                SET exact_hits=0, semantic_hits=0, misses=0
                WHERE id=1
                """
            )
        return count

    def count(self) -> int:
        with self._connect() as db:
            return int(db.execute("SELECT COUNT(*) FROM answers").fetchone()[0])
