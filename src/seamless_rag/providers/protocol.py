"""Embedding provider protocol — the interface all providers must satisfy."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for embedding providers. Implement this to add custom providers.

    Example:
        class MyProvider:
            @property
            def dimensions(self) -> int:
                return 384

            def embed(self, text: str) -> list[float]:
                return my_model.encode(text).tolist()

            def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
                return [self.embed(t) for t in texts]
    """

    @property
    def dimensions(self) -> int:
        """Number of dimensions in the embedding vector."""
        ...

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        ...

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        ...
