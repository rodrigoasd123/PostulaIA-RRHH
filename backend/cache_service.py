from __future__ import annotations

from pathlib import Path
import shutil
import time
from typing import Callable

from .answer_cache import AnswerCache
from .cache_models import (
    AnswerCacheMetrics,
    CacheContext,
    CachedAnswerSummary,
    CachedResponse,
    CacheStats,
    ClearResult,
    DocumentIdentity,
)
from .local_embeddings import EmbeddingProvider, FastEmbedProvider
from .models import Evidence, PageText
from .vector_cache import VectorCache


class CacheService:
    def __init__(
        self,
        root: str | Path = "data/cache",
        embedder: EmbeddingProvider | None = None,
        now: Callable[[], float] = time.time,
        semantic_threshold: float = 0.97,
    ):
        self.root = Path(root).resolve()
        self.embedder = embedder or FastEmbedProvider()
        self.now = now
        self.semantic_threshold = semantic_threshold
        self._build_components()

    def _build_components(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.vector_cache = VectorCache(self.root, self.embedder, now=self.now)
        self.answer_cache = AnswerCache(
            self.root / "cache.db",
            self.embedder,
            now=self.now,
            semantic_threshold=self.semantic_threshold,
        )

    def cleanup_expired(self) -> tuple[int, int]:
        return self.vector_cache.cleanup_expired(), self.answer_cache.cleanup_expired()

    def prepare_document(
        self,
        document_bytes: bytes,
        pages: list[PageText],
        source_type: str,
    ) -> DocumentIdentity | None:
        return self.vector_cache.ensure_document(document_bytes, pages, source_type)

    def search(
        self,
        profile_identity: DocumentIdentity | None,
        cv_identity: DocumentIdentity | None,
        question: str,
        limit: int = 4,
    ) -> list[Evidence]:
        identities = [item for item in (profile_identity, cv_identity) if item is not None]
        if not identities:
            return []
        return self.vector_cache.search(identities, question, limit=limit)

    def get_response(self, context: CacheContext, question: str) -> CachedResponse | None:
        return self.answer_cache.get(context, question)

    def store_response(
        self,
        context: CacheContext,
        question: str,
        answer: str,
        evidence: list[Evidence],
    ) -> bool:
        return self.answer_cache.put(context, question, answer, evidence)

    def list_responses(self, profile_hash: str, cv_hash: str) -> list[CachedAnswerSummary]:
        return self.answer_cache.list_active(profile_hash, cv_hash)

    def response_metrics(self) -> AnswerCacheMetrics:
        return self.answer_cache.metrics()

    def record_response_hit(self, context: CacheContext, response: CachedResponse) -> bool:
        if response.entry_id is None:
            return False
        return self.answer_cache.record_hit(response.entry_id, context, response.match_type)

    def record_response_miss(self) -> None:
        self.answer_cache.record_miss()

    def delete_response(self, entry_id: int, profile_hash: str, cv_hash: str) -> bool:
        return self.answer_cache.delete_entry(entry_id, profile_hash, cv_hash)

    def stats(self) -> CacheStats:
        self.cleanup_expired()
        size = 0
        if self.root.exists():
            for item in self.root.rglob("*"):
                if item.is_file():
                    try:
                        size += item.stat().st_size
                    except OSError:
                        continue
        return CacheStats(
            documents=self.vector_cache.document_count(),
            answers=self.answer_cache.count(),
            bytes_on_disk=size,
        )

    def clear_all(self) -> ClearResult:
        resolved = self.root.resolve()
        if resolved.name != "cache" or resolved == Path(resolved.anchor):
            raise ValueError("Ruta de cache no autorizada para borrado")
        stats = self.stats()
        removed_files = 0
        if resolved.exists():
            removed_files = sum(1 for item in resolved.rglob("*") if item.is_file())
            shutil.rmtree(resolved)
        self._build_components()
        return ClearResult(
            removed_documents=stats.documents,
            removed_answers=stats.answers,
            removed_files=removed_files,
        )
