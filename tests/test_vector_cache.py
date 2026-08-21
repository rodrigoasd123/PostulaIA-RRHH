from __future__ import annotations

import hashlib

import numpy as np

from backend.cache_models import CACHE_TTL_SECONDS
from backend.local_embeddings import normalize_rows
from backend.models import PageText
from backend.vector_cache import VectorCache


class Clock:
    def __init__(self, value: float = 0.0):
        self.value = value

    def __call__(self) -> float:
        return self.value


class FakeEmbeddings:
    model_id = "fake-multilingual-v1"

    def __init__(self):
        self.passage_calls = 0
        self.query_calls = 0

    @staticmethod
    def _vector(text: str) -> np.ndarray:
        digest = hashlib.sha256(text.casefold().encode("utf-8")).digest()
        raw = np.array([digest[0] + 1, digest[1] + 1, digest[2] + 1, digest[3] + 1], dtype=np.float32)
        return normalize_rows(raw)[0]

    def embed_passages(self, texts):
        self.passage_calls += 1
        return np.vstack([self._vector(text) for text in texts])

    def embed_query(self, text):
        self.query_calls += 1
        return self._vector(text)


def test_same_pdf_reuses_persisted_vectors(tmp_path):
    embedder = FakeEmbeddings()
    cache = VectorCache(tmp_path / "cache", embedder)
    pages = [PageText(1, "Experiencia profesional con Python")]

    first = cache.ensure_document(b"same-pdf", pages, "cv")
    second = cache.ensure_document(b"same-pdf", pages, "cv")

    assert first == second
    assert first is not None
    assert embedder.passage_calls == 1


def test_changed_pdf_or_model_creates_distinct_identity(tmp_path):
    pages = [PageText(1, "Experiencia con SQL")]
    first_embedder = FakeEmbeddings()
    cache = VectorCache(tmp_path / "cache", first_embedder)

    first = cache.ensure_document(b"version-one", pages, "cv")
    second = cache.ensure_document(b"version-two", pages, "cv")

    other_embedder = FakeEmbeddings()
    other_embedder.model_id = "fake-multilingual-v2"
    other_cache = VectorCache(tmp_path / "cache", other_embedder)
    third = other_cache.ensure_document(b"version-one", pages, "cv")

    assert first and second and third
    assert len({first.cache_key, second.cache_key, third.cache_key}) == 3


def test_search_only_uses_selected_document_identities(tmp_path):
    embedder = FakeEmbeddings()
    cache = VectorCache(tmp_path / "cache", embedder)
    profile = cache.ensure_document(b"profile", [PageText(1, "Perfil Python")], "profile")
    ana = cache.ensure_document(b"ana", [PageText(1, "SECRETO_ANA")], "cv")
    jorge = cache.ensure_document(b"jorge", [PageText(2, "EVIDENCIA_JORGE")], "cv")

    results = cache.search([profile, jorge], "EVIDENCIA_JORGE", limit=4)

    assert results
    assert any("EVIDENCIA_JORGE" in item.text for item in results)
    assert all("SECRETO_ANA" not in item.text for item in results)
    assert ana is not None


def test_ttl_is_fixed_and_expires_at_exactly_24_hours(tmp_path):
    clock = Clock()
    embedder = FakeEmbeddings()
    cache = VectorCache(tmp_path / "cache", embedder, now=clock)
    pages = [PageText(1, "Python")]

    cache.ensure_document(b"cv", pages, "cv")
    clock.value = CACHE_TTL_SECONDS - 1
    cache.ensure_document(b"cv", pages, "cv")
    assert embedder.passage_calls == 1

    clock.value = CACHE_TTL_SECONDS
    cache.ensure_document(b"cv", pages, "cv")
    assert embedder.passage_calls == 2


def test_corrupt_index_returns_empty_instead_of_crashing(tmp_path):
    embedder = FakeEmbeddings()
    cache = VectorCache(tmp_path / "cache", embedder)
    identity = cache.ensure_document(b"cv", [PageText(1, "Python")], "cv")
    assert identity is not None
    cache._safe_index_path(identity.cache_key).write_bytes(b"not-faiss")

    assert cache.search([identity], "Python") == []
