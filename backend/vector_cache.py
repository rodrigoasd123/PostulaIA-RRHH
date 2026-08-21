from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
import shutil
import sqlite3
import time
from typing import Callable, Iterator, Sequence

import faiss
import numpy as np

from .cache_models import (
    CACHE_SCHEMA_VERSION,
    CACHE_TTL_SECONDS,
    CHUNKER_VERSION,
    DocumentIdentity,
    sha256_bytes,
)
from .local_embeddings import EmbeddingProvider
from .models import Evidence, PageText
from .retrieval import chunks_from_pages


class CacheSchemaError(RuntimeError):
    pass


class VectorCache:
    def __init__(
        self,
        root: str | Path,
        embedder: EmbeddingProvider,
        now: Callable[[], float] = time.time,
        ttl_seconds: int = CACHE_TTL_SECONDS,
    ):
        self.root = Path(root).resolve()
        self.vectors_root = self.root / "vectors"
        self.db_path = self.root / "cache.db"
        self.embedder = embedder
        self.now = now
        self.ttl_seconds = ttl_seconds
        self.vectors_root.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.db_path)
        db.execute("PRAGMA foreign_keys = ON")
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
            db.execute("CREATE TABLE IF NOT EXISTS cache_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            row = db.execute("SELECT value FROM cache_meta WHERE key='schema_version'").fetchone()
            if row and int(row[0]) != CACHE_SCHEMA_VERSION:
                raise CacheSchemaError("Version de cache incompatible")
            db.execute(
                "INSERT OR IGNORE INTO cache_meta(key, value) VALUES ('schema_version', ?)",
                (str(CACHE_SCHEMA_VERSION),),
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    cache_key TEXT PRIMARY KEY,
                    document_hash TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    embedding_model TEXT NOT NULL,
                    chunker_version TEXT NOT NULL,
                    index_path TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    document_cache_key TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    page INTEGER NOT NULL,
                    source_type TEXT NOT NULL,
                    text TEXT NOT NULL,
                    PRIMARY KEY(document_cache_key, position),
                    FOREIGN KEY(document_cache_key) REFERENCES documents(cache_key) ON DELETE CASCADE
                )
                """
            )

    def _safe_index_path(self, cache_key: str) -> Path:
        if len(cache_key) != 64 or any(ch not in "0123456789abcdef" for ch in cache_key):
            raise ValueError("Clave documental invalida")
        path = (self.vectors_root / cache_key / "index.faiss").resolve()
        if self.vectors_root not in path.parents:
            raise ValueError("Ruta vectorial fuera del directorio permitido")
        return path

    def cleanup_expired(self) -> int:
        cutoff = self.now()
        with self._connect() as db:
            rows = db.execute(
                "SELECT cache_key FROM documents WHERE expires_at <= ?",
                (cutoff,),
            ).fetchall()
            db.execute("DELETE FROM documents WHERE expires_at <= ?", (cutoff,))
        for (cache_key,) in rows:
            try:
                index_dir = self._safe_index_path(cache_key).parent
                if index_dir.exists():
                    shutil.rmtree(index_dir)
            except (OSError, ValueError):
                continue
        return len(rows)

    def _is_valid(self, identity: DocumentIdentity) -> bool:
        with self._connect() as db:
            row = db.execute(
                "SELECT index_path FROM documents WHERE cache_key=? AND expires_at>?",
                (identity.cache_key, self.now()),
            ).fetchone()
            count = db.execute(
                "SELECT COUNT(*) FROM chunks WHERE document_cache_key=?",
                (identity.cache_key,),
            ).fetchone()[0]
        if not row or count <= 0:
            return False
        try:
            path = self._safe_index_path(identity.cache_key)
            index = faiss.read_index(str(path))
            return index.ntotal == count
        except (OSError, RuntimeError, ValueError):
            return False

    def ensure_document(
        self,
        document_bytes: bytes,
        pages: list[PageText],
        source_type: str,
    ) -> DocumentIdentity | None:
        self.cleanup_expired()
        identity = DocumentIdentity(
            document_hash=sha256_bytes(document_bytes),
            source_type=source_type,
            embedding_model=self.embedder.model_id,
            chunker_version=CHUNKER_VERSION,
        )
        if self._is_valid(identity):
            return identity

        chunks = chunks_from_pages(pages)
        if not chunks:
            return None
        try:
            vectors = self.embedder.embed_passages([item.text for item in chunks])
            if vectors.ndim != 2 or vectors.shape[0] != len(chunks) or vectors.shape[1] <= 0:
                return None
            index = faiss.IndexFlatIP(vectors.shape[1])
            index.add(np.ascontiguousarray(vectors, dtype=np.float32))
            index_path = self._safe_index_path(identity.cache_key)
            index_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = index_path.with_suffix(".tmp")
            faiss.write_index(index, str(temp_path))
            os.replace(temp_path, index_path)
            created_at = self.now()
            with self._connect() as db:
                db.execute("DELETE FROM documents WHERE cache_key=?", (identity.cache_key,))
                db.execute(
                    """
                    INSERT INTO documents(
                        cache_key, document_hash, source_type, embedding_model,
                        chunker_version, index_path, created_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        identity.cache_key,
                        identity.document_hash,
                        source_type,
                        identity.embedding_model,
                        identity.chunker_version,
                        str(index_path.relative_to(self.root)),
                        created_at,
                        created_at + self.ttl_seconds,
                    ),
                )
                db.executemany(
                    "INSERT INTO chunks(document_cache_key, position, page, source_type, text) VALUES (?, ?, ?, ?, ?)",
                    [
                        (identity.cache_key, position, item.page, source_type, item.text)
                        for position, item in enumerate(chunks)
                    ],
                )
            return identity
        except (OSError, RuntimeError, sqlite3.Error, ValueError):
            return None

    def search(
        self,
        identities: Sequence[DocumentIdentity],
        question: str,
        limit: int = 4,
    ) -> list[Evidence]:
        self.cleanup_expired()
        try:
            query = np.asarray(self.embedder.embed_query(question), dtype=np.float32).reshape(1, -1)
        except (OSError, RuntimeError, ValueError):
            return []
        ranked: list[Evidence] = []
        per_document = max(1, limit)
        for identity in identities:
            if not self._is_valid(identity):
                continue
            try:
                path = self._safe_index_path(identity.cache_key)
                index = faiss.read_index(str(path))
                with self._connect() as db:
                    rows = db.execute(
                        "SELECT position, page, source_type, text FROM chunks WHERE document_cache_key=? ORDER BY position",
                        (identity.cache_key,),
                    ).fetchall()
                scores, positions = index.search(query, min(per_document, len(rows)))
                for score, position in zip(scores[0], positions[0]):
                    if position < 0 or position >= len(rows):
                        continue
                    _, page, source_type, text = rows[position]
                    label = "PERFIL DEL PUESTO" if source_type == "profile" else "CV SELECCIONADO"
                    ranked.append(
                        Evidence(
                            page=int(page),
                            text=f"[FUENTE: {label}, PÁGINA {page}] {text}",
                            score=float(score),
                        )
                    )
            except (OSError, RuntimeError, sqlite3.Error, ValueError):
                continue
        ranked.sort(key=lambda item: (-item.score, item.page, item.text))
        return ranked[:limit]

    def clear_documents(self) -> tuple[int, int]:
        with self._connect() as db:
            count = int(db.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
            db.execute("DELETE FROM documents")
        removed_files = 0
        if self.vectors_root.exists():
            for child in self.vectors_root.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                    removed_files += 1
        return count, removed_files

    def document_count(self) -> int:
        with self._connect() as db:
            return int(db.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
