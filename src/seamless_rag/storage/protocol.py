"""VectorStore protocol — the interface all storage backends must satisfy.

Both RAG engine and AutoEmbedder use this protocol so the storage layer
can be swapped (MariaDB, in-memory mock, etc.) without changing pipeline code.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for vector storage backends.

    Example:
        class MyVectorStore:
            def init_schema(self, dimensions: int = 384) -> None: ...
            def search(self, table, query_vec, top_k=5, context_window=0): ...
            def insert_embedding(self, table, row_id, embedding): ...
            def insert_embeddings_batch(self, table, row_ids, embeddings): ...
            def get_new_rows(self, table, text_column, last_id): ...
            def get_max_id(self, table): ...
    """

    def init_schema(self, dimensions: int = 384) -> None:
        """Create required tables and indexes if they don't exist."""
        ...

    def search(
        self,
        table: str,
        query_vec: list[float],
        top_k: int = 5,
        context_window: int = 0,
        where: str = "",
    ) -> list[dict]:
        """Search for nearest vectors with optional SQL filter.

        Args:
            where: SQL WHERE clause for hybrid filter+vector search.
        """
        ...

    def insert_embedding(self, table: str, row_id: int, embedding: list[float]) -> None:
        """Update a single row with its embedding vector."""
        ...

    def insert_embeddings_batch(
        self, table: str, row_ids: list[int], embeddings: list[list[float]],
    ) -> None:
        """Update multiple rows with their embedding vectors in a batch."""
        ...

    def get_new_rows(self, table: str, text_column: str, last_id: int) -> list[dict]:
        """Fetch rows with id > last_id that need embedding."""
        ...

    def get_max_id(self, table: str) -> int:
        """Return the maximum id in the given table, or 0 if empty."""
        ...
