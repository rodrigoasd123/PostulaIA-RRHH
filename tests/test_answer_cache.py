from __future__ import annotations

import json
import sqlite3

import numpy as np

from backend.answer_cache import AnswerCache
from backend.cache_models import CACHE_TTL_SECONDS, CacheContext
from backend.local_embeddings import normalize_rows
from backend.models import Evidence


class Clock:
    def __init__(self, value: float = 0.0):
        self.value = value

    def __call__(self) -> float:
        return self.value


class SemanticEmbeddings:
    model_id = "semantic-fake-v1"

    def __init__(self):
        self.query_calls = 0

    def embed_passages(self, texts):
        return np.vstack([self.embed_query(text) for text in texts])

    def embed_query(self, text):
        self.query_calls += 1
        normalized = text.casefold()
        if "python" in normalized or "programacion" in normalized:
            return normalize_rows(np.array([1.0, 0.0], dtype=np.float32))[0]
        return normalize_rows(np.array([0.0, 1.0], dtype=np.float32))[0]


def context(cv_hash: str = "cv-a", route: str = "gemini:model-a") -> CacheContext:
    return CacheContext(profile_hash="profile", cv_hash=cv_hash, response_route=route)


def test_exact_hit_does_not_reembed_question(tmp_path):
    embedder = SemanticEmbeddings()
    cache = AnswerCache(tmp_path / "cache.db", embedder)
    evidence = [Evidence(2, "Python", 1.0)]
    assert cache.put(context(), "Tiene Python?", "Sí, página 2", evidence)
    calls_after_put = embedder.query_calls

    result = cache.get(context(), "Tiene Python?")

    assert result and result.match_type == "exact"
    assert result.answer == "Sí, página 2"
    assert embedder.query_calls == calls_after_put


def test_semantic_hit_is_scoped_to_same_documents_and_route(tmp_path):
    cache = AnswerCache(tmp_path / "cache.db", SemanticEmbeddings())
    cache.put(context(), "Tiene Python?", "Respuesta A", [Evidence(1, "Python")])

    semantic = cache.get(context(), "Cuenta con experiencia en programacion?")
    other_cv = cache.get(context(cv_hash="cv-b"), "Cuenta con experiencia en programacion?")
    other_route = cache.get(context(route="ollama:model-b"), "Cuenta con experiencia en programacion?")

    assert semantic and semantic.match_type == "semantic"
    assert semantic.similarity >= 0.97
    assert other_cv is None
    assert other_route is None


def test_different_intent_below_threshold_is_a_miss(tmp_path):
    cache = AnswerCache(tmp_path / "cache.db", SemanticEmbeddings())
    cache.put(context(), "Tiene Python?", "Respuesta", [Evidence(1, "Python")])

    assert cache.get(context(), "Tiene experiencia en SQL?") is None


def test_answer_expires_at_exactly_24_hours(tmp_path):
    clock = Clock()
    cache = AnswerCache(tmp_path / "cache.db", SemanticEmbeddings(), now=clock)
    cache.put(context(), "Tiene Python?", "Respuesta", [Evidence(1, "Python")])

    clock.value = CACHE_TTL_SECONDS - 1
    assert cache.get(context(), "Tiene Python?") is not None
    clock.value = CACHE_TTL_SECONDS
    assert cache.get(context(), "Tiene Python?") is None
    assert cache.count() == 0

def test_migrates_v1_schema_idempotently_and_preserves_answer(tmp_path):
    db_path = tmp_path / "cache.db"
    vector = np.array([1.0, 0.0], dtype=np.float32)
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE cache_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        db.execute("INSERT INTO cache_meta VALUES ('schema_version', '1')")
        db.execute(
            """
            CREATE TABLE answers (
                id INTEGER PRIMARY KEY, profile_hash TEXT NOT NULL, cv_hash TEXT NOT NULL,
                response_route TEXT NOT NULL, prompt_version TEXT NOT NULL,
                moderation_version TEXT NOT NULL, question_norm TEXT NOT NULL,
                question_vector BLOB NOT NULL, vector_dim INTEGER NOT NULL,
                answer TEXT NOT NULL, evidence_json TEXT NOT NULL,
                created_at REAL NOT NULL, expires_at REAL NOT NULL,
                UNIQUE(profile_hash, cv_hash, response_route, prompt_version,
                       moderation_version, question_norm)
            )
            """
        )
        db.execute(
            "INSERT INTO answers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                1, "profile", "cv-a", "gemini:model-a", "hr-documental-v1",
                "local-rules-v1", "tiene python", vector.tobytes(), 2,
                "Respuesta anterior", json.dumps([{"page": 1, "text": "Python"}]),
                0.0, float(CACHE_TTL_SECONDS),
            ),
        )

    clock = Clock()
    cache = AnswerCache(db_path, SemanticEmbeddings(), now=clock)
    AnswerCache(db_path, SemanticEmbeddings(), now=clock)

    result = cache.get(context(), "Tiene Python")
    summaries = cache.list_active("profile", "cv-a")
    with sqlite3.connect(db_path) as db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(answers)")}
        version = db.execute(
            "SELECT value FROM cache_meta WHERE key='answer_schema_version'"
        ).fetchone()[0]

    assert result and result.answer == "Respuesta anterior"
    assert result.entry_id == 1
    assert summaries[0].reuse_count == 0
    assert {"exact_hit_count", "semantic_hit_count", "last_hit_at", "last_match_type"} <= columns
    assert version == "2"


def test_list_active_is_scoped_and_truncates_question(tmp_path):
    cache = AnswerCache(tmp_path / "cache.db", SemanticEmbeddings())
    long_question = "Python " + "experiencia " * 20
    cache.put(context(), long_question, "Respuesta A", [Evidence(1, "Python")])
    cache.put(context(cv_hash="cv-b"), "Python?", "Respuesta B", [Evidence(1, "Python")])

    summaries = cache.list_active("profile", "cv-a")

    assert len(summaries) == 1
    assert len(summaries[0].question_preview) <= 96
    assert summaries[0].question_preview.endswith("…")
    assert not hasattr(summaries[0], "answer")


def test_metrics_count_exact_semantic_and_single_explicit_miss(tmp_path):
    cache = AnswerCache(tmp_path / "cache.db", SemanticEmbeddings())
    cache.put(context(), "Tiene Python?", "Respuesta", [Evidence(1, "Python")])
    exact = cache.get(context(), "Tiene Python?")
    semantic = cache.get(context(), "Experiencia en programacion?")

    assert exact and exact.entry_id is not None
    assert semantic and semantic.entry_id is not None
    assert cache.record_hit(exact.entry_id, context(), exact.match_type)
    assert cache.record_hit(semantic.entry_id, context(), semantic.match_type)
    cache.record_miss()

    metrics = cache.metrics()
    summary = cache.list_active("profile", "cv-a")[0]
    assert metrics.exact_hits == 1
    assert metrics.semantic_hits == 1
    assert metrics.misses == 1
    assert metrics.calls_avoided == 2
    assert metrics.hit_rate == 2 / 3
    assert summary.reuse_count == 2


def test_delete_entry_requires_matching_document_scope(tmp_path):
    cache = AnswerCache(tmp_path / "cache.db", SemanticEmbeddings())
    cache.put(context(), "Tiene Python?", "Respuesta A", [Evidence(1, "Python")])
    cache.put(context(), "Usa programacion?", "Respuesta B", [Evidence(1, "Python")])
    summaries = cache.list_active("profile", "cv-a")
    target = summaries[0]

    assert not cache.delete_entry(target.entry_id, "profile", "cv-b")
    assert cache.delete_entry(target.entry_id, "profile", "cv-a")
    assert len(cache.list_active("profile", "cv-a")) == 1
