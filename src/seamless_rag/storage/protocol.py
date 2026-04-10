"""VectorStore protocol — unified interface for vector operations.

Both RAG engine and Watch mode use this protocol, eliminating duplicate SQL.
Can be mocked with an in-memory implementation for CI testing.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for vector storage operations."""

    def insert_embedding(self, table: str, row_id: int, embedding: list[float]) -> None:
        """Store a vector embedding for a row."""
        ...

    def insert_embeddings_batch(
        self, table: str, row_ids: list[int], embeddings: list[list[float]]
    ) -> None:
        """Store multiple vector embeddings in a batch."""
        ...

    def search(
        self, table: str, query_vec: list[float], top_k: int = 5, context_window: int = 0
    ) -> list[dict]:
        """Search for similar vectors, returning results as list[dict]."""
        ...

    def get_new_rows(self, table: str, text_column: str, last_id: int) -> list[dict]:
        """Get rows inserted after last_id that need embedding."""
        ...

    def get_max_id(self, table: str) -> int:
        """Get the current maximum ID in a table."""
        ...

    def ensure_vector_column(self, table: str, dimensions: int) -> None:
        """Create VECTOR column and HNSW index if they don't exist."""
        ...
