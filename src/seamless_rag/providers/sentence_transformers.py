"""SentenceTransformers embedding provider — local, free, no API key needed."""
from __future__ import annotations

try:
    from sentence_transformers import SentenceTransformer
except ImportError as _e:
    raise ImportError(
        "The `sentence-transformers` package is required for the "
        "sentence-transformers embedding provider but is not installed.\n"
        "\n"
        "Install with:\n"
        '    pip install "seamless-rag[embeddings]"\n'
        "\n"
        "This pulls in PyTorch (~500 MB). If you don't need local embeddings, "
        "switch provider:\n"
        "    EMBEDDING_PROVIDER=gemini   (then: pip install \"seamless-rag[gemini]\")\n"
        "    EMBEDDING_PROVIDER=openai   (then: pip install \"seamless-rag[openai]\")\n"
        "    EMBEDDING_PROVIDER=ollama   (no extra dep, needs local Ollama)"
    ) from _e


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
