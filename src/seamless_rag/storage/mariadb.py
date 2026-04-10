"""MariaDB VectorStore implementation — real database operations."""


class MariaDBVectorStore:
    """VectorStore backed by MariaDB with VECTOR columns and HNSW index."""

    def __init__(self, host: str, port: int, user: str, password: str, database: str) -> None:
        raise NotImplementedError("MariaDB VectorStore not yet implemented")

    def insert_embedding(self, table: str, row_id: int, embedding: list[float]) -> None:
        raise NotImplementedError

    def insert_embeddings_batch(
        self, table: str, row_ids: list[int], embeddings: list[list[float]]
    ) -> None:
        raise NotImplementedError

    def search(
        self, table: str, query_vec: list[float], top_k: int = 5, context_window: int = 0
    ) -> list[dict]:
        raise NotImplementedError

    def get_new_rows(self, table: str, text_column: str, last_id: int) -> list[dict]:
        raise NotImplementedError

    def get_max_id(self, table: str) -> int:
        raise NotImplementedError

    def ensure_vector_column(self, table: str, dimensions: int) -> None:
        raise NotImplementedError
