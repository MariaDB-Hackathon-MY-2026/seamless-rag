"""MariaDB VectorStore implementation — real database operations."""
from __future__ import annotations

import array

import mariadb


class MariaDBVectorStore:
    """VectorStore backed by MariaDB with VECTOR columns and HNSW index."""

    def __init__(self, host: str, port: int, user: str, password: str, database: str) -> None:
        self._conn = mariadb.connect(
            host=host, port=port, user=user, password=password, database=database,
        )
        self._conn.autocommit = True

    def _cursor(self) -> mariadb.Cursor:
        return self._conn.cursor()

    def _dict_cursor(self) -> mariadb.Cursor:
        return self._conn.cursor(dictionary=True)

    def insert_embedding(self, table: str, row_id: int, embedding: list[float]) -> None:
        vec = array.array("f", embedding)
        cursor = self._cursor()
        cursor.execute(
            f"UPDATE {table} SET embedding = ? WHERE id = ?",  # noqa: S608
            (vec, row_id),
        )
        cursor.close()

    def insert_embeddings_batch(
        self, table: str, row_ids: list[int], embeddings: list[list[float]],
    ) -> None:
        cursor = self._cursor()
        for row_id, emb in zip(row_ids, embeddings, strict=True):
            vec = array.array("f", emb)
            cursor.execute(
                f"UPDATE {table} SET embedding = ? WHERE id = ?",  # noqa: S608
                (vec, row_id),
            )
        cursor.close()

    def search(
        self, table: str, query_vec: list[float], top_k: int = 5, context_window: int = 0,
    ) -> list[dict]:
        vec = array.array("f", query_vec)
        cursor = self._dict_cursor()

        # Tune HNSW search quality
        cursor.execute("SET mhnsw_ef_search = 100")

        if context_window > 0:
            cursor.execute(
                f"""
                WITH closest AS (
                    SELECT id, document_id, chunk_order,
                           VEC_DISTANCE_COSINE(embedding, ?) AS distance
                    FROM {table}
                    ORDER BY distance
                    LIMIT ?
                )
                SELECT c.id, c.content, c.chunk_order, c.document_id,
                       closest.distance
                FROM closest
                JOIN {table} c ON c.document_id = closest.document_id
                WHERE c.chunk_order BETWEEN
                    (closest.chunk_order - ?) AND (closest.chunk_order + ?)
                ORDER BY closest.distance, c.chunk_order
                """,  # noqa: S608
                (vec, top_k, context_window, context_window),
            )
        else:
            cursor.execute(
                f"""
                SELECT id, content,
                       VEC_DISTANCE_COSINE(embedding, ?) AS distance
                FROM {table}
                ORDER BY distance
                LIMIT ?
                """,  # noqa: S608
                (vec, top_k),
            )

        results = cursor.fetchall()
        cursor.close()
        return results

    def get_new_rows(self, table: str, text_column: str, last_id: int) -> list[dict]:
        cursor = self._dict_cursor()
        cursor.execute(
            f"SELECT id, {text_column} FROM {table} WHERE id > ? ORDER BY id",  # noqa: S608
            (last_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def get_max_id(self, table: str) -> int:
        cursor = self._cursor()
        cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table}")  # noqa: S608
        result = cursor.fetchone()[0]
        cursor.close()
        return result

    def ensure_vector_column(self, table: str, dimensions: int) -> None:
        cursor = self._cursor()
        try:
            cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN embedding VECTOR({dimensions}) NOT NULL"  # noqa: S608
            )
            cursor.execute(
                f"ALTER TABLE {table} ADD VECTOR INDEX (embedding) DISTANCE=cosine"  # noqa: S608
            )
        except mariadb.Error:
            pass  # Column/index already exists
        cursor.close()

    def close(self) -> None:
        self._conn.close()
