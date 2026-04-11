"""MariaDB VectorStore implementation — real database operations."""
from __future__ import annotations

import array
import contextlib
import re
import threading

import mariadb

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Strict SQL validation: only allow simple SELECT (no subquery writes)
_FORBIDDEN_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE"
    r"|EXECUTE|CALL|LOAD|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b",
    re.IGNORECASE,
)

_MIN_MARIADB_VERSION = (11, 7, 2)

_SCHEMA_SQL = [
    """CREATE TABLE IF NOT EXISTS documents (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(512) NOT NULL,
        source VARCHAR(256) DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS chunks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        document_id INT NOT NULL,
        chunk_order INT NOT NULL,
        content LONGTEXT NOT NULL,
        embedding VECTOR({dimensions}) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        VECTOR INDEX (embedding) DISTANCE=cosine,
        FOREIGN KEY (document_id) REFERENCES documents(id),
        INDEX idx_doc_order (document_id, chunk_order)
    )""",
]


def _validate_ident(name: str) -> str:
    """Validate SQL identifier to prevent injection."""
    if not _IDENT_RE.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


def _vec_bytes(vec: list[float] | array.array) -> bytes:
    """Convert vector to bytes for VEC_DISTANCE_COSINE parameter binding."""
    if isinstance(vec, (bytes, bytearray)):
        return bytes(vec)
    if isinstance(vec, array.array):
        return vec.tobytes()
    return array.array("f", vec).tobytes()


class MariaDBVectorStore:
    """VectorStore backed by MariaDB with connection pool and HNSW index.

    Uses a thread-safe connection pool (default size 5) for concurrent access.
    Supports context manager for automatic cleanup.

    Example::

        with MariaDBVectorStore(host="localhost", ...) as store:
            store.init_schema()
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        pool_size: int = 5,
    ) -> None:
        self._pool = mariadb.ConnectionPool(
            pool_name="seamless_rag",
            pool_size=pool_size,
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )
        self._lock = threading.Lock()

    def __enter__(self) -> MariaDBVectorStore:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    @contextlib.contextmanager
    def _get_conn(self):
        """Get a connection from the pool, auto-return on exit."""
        conn = self._pool.get_connection()
        conn.autocommit = True
        try:
            yield conn
        finally:
            conn.close()  # returns to pool

    # ── Schema ─────────────────────────────────────────────────

    def _check_version(self) -> None:
        """Verify MariaDB version >= 11.7.2 (VECTOR support)."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT VERSION()")
                ver_str = cursor.fetchone()[0]
            finally:
                cursor.close()
        # Parse "11.8.1-MariaDB" or "11.7.2"
        parts = ver_str.split("-")[0].split(".")
        version = tuple(int(p) for p in parts[:3])
        if version < _MIN_MARIADB_VERSION:
            raise RuntimeError(
                f"MariaDB {ver_str} is too old. "
                f"VECTOR support requires >= {'.'.join(map(str, _MIN_MARIADB_VERSION))}"
            )

    def init_schema(self, dimensions: int = 384) -> None:
        """Create documents + chunks tables if they don't exist.

        Also validates MariaDB version >= 11.7.2 for VECTOR support.
        """
        self._check_version()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                for sql in _SCHEMA_SQL:
                    cursor.execute(sql.format(dimensions=dimensions))
            finally:
                cursor.close()

    def ensure_vector_column(self, table: str, dimensions: int) -> None:
        t = _validate_ident(table)
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                with contextlib.suppress(mariadb.Error):
                    cursor.execute(
                        f"ALTER TABLE {t} ADD COLUMN embedding"
                        f" VECTOR({int(dimensions)}) NOT NULL"
                    )
                with contextlib.suppress(mariadb.Error):
                    cursor.execute(
                        f"ALTER TABLE {t} ADD VECTOR INDEX (embedding)"
                        " DISTANCE=cosine"
                    )
            finally:
                cursor.close()

    # ── Write ─────────────────────────────────────────────────

    def insert_document(self, title: str) -> int:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO documents (title) VALUES (?)", (title,),
                )
                return cursor.lastrowid
            finally:
                cursor.close()

    def insert_chunk(
        self, document_id: int, chunk_order: int,
        content: str, embedding: list[float],
    ) -> int:
        vec = array.array("f", embedding)
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO chunks (document_id, chunk_order,"
                    " content, embedding) VALUES (?, ?, ?, ?)",
                    (document_id, chunk_order, content, vec),
                )
                return cursor.lastrowid
            finally:
                cursor.close()

    def insert_embedding(
        self, table: str, row_id: int, embedding: list[float],
    ) -> None:
        t = _validate_ident(table)
        vec = array.array("f", embedding)
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    f"UPDATE {t} SET embedding = ? WHERE id = ?",
                    (vec, row_id),
                )
            finally:
                cursor.close()

    def insert_embeddings_batch(
        self, table: str, row_ids: list[int],
        embeddings: list[list[float]],
    ) -> None:
        t = _validate_ident(table)
        pairs = zip(row_ids, embeddings, strict=True)
        params = [(array.array("f", emb), rid) for rid, emb in pairs]
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(
                    f"UPDATE {t} SET embedding = ? WHERE id = ?", params,
                )
            finally:
                cursor.close()

    # ── Read / Search ─────────────────────────────────────────

    def search(
        self, table: str, query_vec: list[float],
        top_k: int = 5, context_window: int = 0,
    ) -> list[dict]:
        t = _validate_ident(table)
        qb = _vec_bytes(query_vec)
        with self._get_conn() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SET mhnsw_ef_search = 100")
                if context_window > 0:
                    cursor.execute(
                        f"""
                        WITH closest AS (
                            SELECT id, document_id, chunk_order,
                                VEC_DISTANCE_COSINE(embedding, ?) AS distance
                            FROM {t} ORDER BY distance LIMIT ?
                        )
                        SELECT DISTINCT c.id, c.content, c.chunk_order,
                            c.document_id, closest.distance
                        FROM closest
                        JOIN {t} c ON c.document_id = closest.document_id
                        WHERE c.chunk_order BETWEEN
                            (closest.chunk_order - ?)
                            AND (closest.chunk_order + ?)
                        ORDER BY closest.distance, c.chunk_order
                        """,
                        (qb, top_k, context_window, context_window),
                    )
                else:
                    cursor.execute(
                        f"""
                        SELECT id, content,
                            VEC_DISTANCE_COSINE(embedding, ?) AS distance
                        FROM {t} ORDER BY distance, id LIMIT ?
                        """,
                        (qb, top_k),
                    )
                return cursor.fetchall()
            finally:
                cursor.close()

    def get_new_rows(
        self, table: str, text_column: str, last_id: int,
    ) -> list[dict]:
        t = _validate_ident(table)
        col = _validate_ident(text_column)
        with self._get_conn() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(
                    f"SELECT id, {col} FROM {t} WHERE id > ?"
                    " ORDER BY id",
                    (last_id,),
                )
                return cursor.fetchall()
            finally:
                cursor.close()

    def get_max_id(self, table: str) -> int:
        t = _validate_ident(table)
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    f"SELECT COALESCE(MAX(id), 0) FROM {t}",
                )
                return cursor.fetchone()[0]
            finally:
                cursor.close()

    def execute_query(self, sql: str) -> list[dict]:
        """Execute a read-only SELECT query and return dict rows.

        Uses regex-based validation that catches write operations even
        inside subqueries, CTEs, and string-like patterns. Blocks:
        INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE,
        GRANT, REVOKE, EXECUTE, CALL, LOAD, INTO OUTFILE/DUMPFILE.
        """
        stripped = sql.strip()
        if not stripped.upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")
        if _FORBIDDEN_RE.search(stripped):
            match = _FORBIDDEN_RE.search(stripped)
            raise ValueError(
                f"Query contains disallowed operation: {match.group()}"
            )
        with self._get_conn() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(stripped)
                return cursor.fetchall()
            finally:
                cursor.close()

    def close(self) -> None:
        """Close the connection pool."""
        self._pool.close()
