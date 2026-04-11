"""MariaDB VectorStore implementation — real database operations."""
from __future__ import annotations

import array
import contextlib

import mariadb

_SCHEMA_SQL = [
    """CREATE TABLE IF NOT EXISTS documents (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(512) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS chunks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        document_id INT NOT NULL,
        chunk_order INT NOT NULL,
        content LONGTEXT NOT NULL,
        embedding VECTOR({dimensions}) NOT NULL,
        VECTOR INDEX (embedding) DISTANCE=cosine,
        FOREIGN KEY (document_id) REFERENCES documents(id),
        INDEX idx_doc_order (document_id, chunk_order)
    )""",
]


def _vec_bytes(vec: list[float] | array.array) -> bytes:
    """Convert vector to bytes for VEC_DISTANCE_COSINE parameter binding."""
    if isinstance(vec, array.array):
        return vec.tobytes()
    return array.array("f", vec).tobytes()


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

    # ── Schema ────────────────────────────────────────────────

    def init_schema(self, dimensions: int = 384) -> None:
        """Create documents + chunks tables if they don't exist."""
        cursor = self._cursor()
        for sql in _SCHEMA_SQL:
            cursor.execute(sql.format(dimensions=dimensions))
        cursor.close()

    def ensure_vector_column(self, table: str, dimensions: int) -> None:
        cursor = self._cursor()
        with contextlib.suppress(mariadb.Error):
            cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN embedding"  # noqa: S608
                f" VECTOR({dimensions}) NOT NULL"
            )
        with contextlib.suppress(mariadb.Error):
            cursor.execute(
                f"ALTER TABLE {table} ADD VECTOR INDEX (embedding)"  # noqa: S608
                " DISTANCE=cosine"
            )
        cursor.close()

    # ── Write ─────────────────────────────────────────────────

    def insert_document(self, title: str) -> int:
        cursor = self._cursor()
        cursor.execute("INSERT INTO documents (title) VALUES (?)", (title,))
        doc_id = cursor.lastrowid
        cursor.close()
        return doc_id

    def insert_chunk(
        self, document_id: int, chunk_order: int, content: str, embedding: list[float],
    ) -> int:
        vec = array.array("f", embedding)
        cursor = self._cursor()
        cursor.execute(
            "INSERT INTO chunks (document_id, chunk_order, content, embedding)"
            " VALUES (?, ?, ?, ?)",
            (document_id, chunk_order, content, vec),
        )
        chunk_id = cursor.lastrowid
        cursor.close()
        return chunk_id

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

    # ── Read / Search ─────────────────────────────────────────

    def search(
        self, table: str, query_vec: list[float], top_k: int = 5, context_window: int = 0,
    ) -> list[dict]:
        qb = _vec_bytes(query_vec)
        cursor = self._dict_cursor()
        cursor.execute("SET mhnsw_ef_search = 100")

        if context_window > 0:
            cursor.execute(
                f"""
                WITH closest AS (
                    SELECT id, document_id, chunk_order,
                           VEC_DISTANCE_COSINE(embedding, ?) AS distance
                    FROM {table}
                    ORDER BY distance LIMIT ?
                )
                SELECT c.id, c.content, c.chunk_order, c.document_id,
                       closest.distance
                FROM closest
                JOIN {table} c ON c.document_id = closest.document_id
                WHERE c.chunk_order BETWEEN
                    (closest.chunk_order - ?) AND (closest.chunk_order + ?)
                ORDER BY closest.distance, c.chunk_order
                """,  # noqa: S608
                (qb, top_k, context_window, context_window),
            )
        else:
            cursor.execute(
                f"""
                SELECT id, content,
                       VEC_DISTANCE_COSINE(embedding, ?) AS distance
                FROM {table} ORDER BY distance LIMIT ?
                """,  # noqa: S608
                (qb, top_k),
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

    def execute_query(self, sql: str) -> list[dict]:
        """Execute arbitrary SELECT and return dict rows."""
        cursor = self._dict_cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def close(self) -> None:
        self._conn.close()
