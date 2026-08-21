from __future__ import annotations

from typing import Protocol, Sequence

import numpy as np

from .cache_models import EMBEDDING_MODEL_ID


class EmbeddingProvider(Protocol):
    model_id: str

    def embed_passages(self, texts: Sequence[str]) -> np.ndarray: ...

    def embed_query(self, text: str) -> np.ndarray: ...


def normalize_rows(values: np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=np.float32)
    if matrix.ndim == 1:
        matrix = matrix.reshape(1, -1)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return np.ascontiguousarray(matrix / norms, dtype=np.float32)


class FastEmbedProvider:
    """Lazy local embedding adapter; model weights are downloaded on first real use."""

    def __init__(self, model_id: str = EMBEDDING_MODEL_ID):
        self.model_id = model_id
        self._model = None

    def _get_model(self):
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=self.model_id)
        return self._model

    def embed_passages(self, texts: Sequence[str]) -> np.ndarray:
        items = list(texts)
        if not items:
            return np.empty((0, 0), dtype=np.float32)
        model = self._get_model()
        runner = getattr(model, "passage_embed", model.embed)
        return normalize_rows(np.asarray(list(runner(items)), dtype=np.float32))

    def embed_query(self, text: str) -> np.ndarray:
        model = self._get_model()
        runner = getattr(model, "query_embed", model.embed)
        return normalize_rows(np.asarray(list(runner([text])), dtype=np.float32))[0]
