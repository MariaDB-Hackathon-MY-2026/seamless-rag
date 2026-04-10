"""SentenceTransformers embedding provider — local, free, no API key needed."""


class SentenceTransformersProvider:
    """Embedding provider using sentence-transformers models.

    Default model: all-MiniLM-L6-v2 (384 dimensions).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        raise NotImplementedError("SentenceTransformers provider not yet implemented")

    @property
    def dimensions(self) -> int:
        raise NotImplementedError

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        raise NotImplementedError
