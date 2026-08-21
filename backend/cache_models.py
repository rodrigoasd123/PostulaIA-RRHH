from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .models import Evidence


CACHE_SCHEMA_VERSION = 1
ANSWER_CACHE_SCHEMA_VERSION = 2
CACHE_TTL_SECONDS = 24 * 60 * 60
EMBEDDING_MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CHUNKER_VERSION = "review-chunks-v1"
PROMPT_VERSION = "hr-documental-v1"
MODERATION_VERSION = "local-rules-v1"
DEFAULT_SEMANTIC_THRESHOLD = 0.97


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_document_cache_key(
    document_hash: str,
    embedding_model: str = EMBEDDING_MODEL_ID,
    chunker_version: str = CHUNKER_VERSION,
) -> str:
    raw = f"{document_hash}\0{embedding_model}\0{chunker_version}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class DocumentIdentity:
    document_hash: str
    source_type: str
    embedding_model: str = EMBEDDING_MODEL_ID
    chunker_version: str = CHUNKER_VERSION

    @property
    def cache_key(self) -> str:
        return make_document_cache_key(
            self.document_hash,
            self.embedding_model,
            self.chunker_version,
        )


@dataclass(frozen=True)
class CacheContext:
    profile_hash: str
    cv_hash: str
    response_route: str
    prompt_version: str = PROMPT_VERSION
    moderation_version: str = MODERATION_VERSION


@dataclass(frozen=True)
class CachedResponse:
    answer: str
    evidence: tuple[Evidence, ...]
    match_type: str
    similarity: float
    entry_id: int | None = None


@dataclass(frozen=True)
class CachedAnswerSummary:
    entry_id: int
    question_preview: str
    response_route: str
    created_at: float
    expires_at: float
    exact_hit_count: int
    semantic_hit_count: int

    @property
    def reuse_count(self) -> int:
        return self.exact_hit_count + self.semantic_hit_count


@dataclass(frozen=True)
class AnswerCacheMetrics:
    exact_hits: int
    semantic_hits: int
    misses: int

    @property
    def hits(self) -> int:
        return self.exact_hits + self.semantic_hits

    @property
    def total_lookups(self) -> int:
        return self.hits + self.misses

    @property
    def calls_avoided(self) -> int:
        return self.hits

    @property
    def hit_rate(self) -> float:
        return self.hits / self.total_lookups if self.total_lookups else 0.0


@dataclass(frozen=True)
class CacheStats:
    documents: int
    answers: int
    bytes_on_disk: int


@dataclass(frozen=True)
class ClearResult:
    removed_documents: int
    removed_answers: int
    removed_files: int
