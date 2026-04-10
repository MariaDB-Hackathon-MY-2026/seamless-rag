"""SentenceTransformers embedding provider — local, free, no API key needed."""
from __future__ import annotations

from sentence_transformers import SentenceTransformer


class SentenceTransformersProvider:
    """Embedding provider using sentence-transformers models.

    Default model: all-MiniLM-L6-v2 (384 dimensions).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model = SentenceTransformer(model_name)
        self._dimensions = self._model.get_embedding_dimension()

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, text: str) -> list[float]:
        vec = self._model.encode(text)
        return vec.tolist()

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        if not texts:
            return []
        vecs = self._model.encode(texts, batch_size=batch_size)
        return [v.tolist() for v in vecs]
