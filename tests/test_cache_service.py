from __future__ import annotations

import hashlib
import numpy as np
import pytest

from backend.cache_models import CacheContext
from backend.cache_service import CacheService
from backend.local_embeddings import normalize_rows
from backend.models import Evidence, PageText


class FakeEmbeddings:
    model_id = "fake-v1"

    def _vector(self, text: str):
        digest = hashlib.sha256(text.encode()).digest()
        return normalize_rows(np.array([digest[0] + 1, digest[1] + 1], dtype=np.float32))[0]

    def embed_passages(self, texts):
        return np.vstack([self._vector(text) for text in texts])

    def embed_query(self, text):
        return self._vector(text)


def test_clear_all_removes_candidate_artifacts_and_recreates_empty_store(tmp_path):
    service = CacheService(tmp_path / "cache", embedder=FakeEmbeddings())
    service.prepare_document(b"cv", [PageText(1, "Python")], "cv")
    service.store_response(
        CacheContext("profile", "cv", "local:v1"),
        "Python?",
        "Respuesta",
        [Evidence(1, "Python")],
    )

    result = service.clear_all()
    stats = service.stats()

    assert result.removed_documents == 1
    assert result.removed_answers == 1
    assert result.removed_files >= 2
    assert stats.documents == 0
    assert stats.answers == 0


def test_clear_rejects_non_cache_directory(tmp_path):
    service = CacheService(tmp_path / "candidate-data", embedder=FakeEmbeddings())

    with pytest.raises(ValueError):
        service.clear_all()

def test_delete_one_response_preserves_document_and_other_answer(tmp_path):
    service = CacheService(tmp_path / "cache", embedder=FakeEmbeddings())
    identity = service.prepare_document(b"cv", [PageText(1, "Python")], "cv")
    ctx = CacheContext("profile", "cv", "local:v1")
    service.store_response(ctx, "Python?", "Respuesta A", [Evidence(1, "Python")])
    service.store_response(ctx, "SQL?", "Respuesta B", [Evidence(1, "SQL")])
    target = service.list_responses("profile", "cv")[0]

    assert not service.delete_response(target.entry_id, "profile", "otro-cv")
    assert service.delete_response(target.entry_id, "profile", "cv")
    assert len(service.list_responses("profile", "cv")) == 1
    assert service.stats().documents == 1
    assert identity is not None
    assert service.vector_cache._safe_index_path(identity.cache_key).exists()


def test_service_metrics_and_clear_all_reset_aggregates(tmp_path):
    service = CacheService(tmp_path / "cache", embedder=FakeEmbeddings())
    ctx = CacheContext("profile", "cv", "local:v1")
    service.store_response(ctx, "Python?", "Respuesta", [Evidence(1, "Python")])
    response = service.get_response(ctx, "Python?")

    assert response is not None
    assert service.record_response_hit(ctx, response)
    service.record_response_miss()
    assert service.response_metrics().hits == 1
    assert service.response_metrics().misses == 1

    service.clear_all()

    assert service.response_metrics().total_lookups == 0
