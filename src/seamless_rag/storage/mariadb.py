"""MariaDB VectorStore implementation — real database operations."""
from __future__ import annotations

import array
import contextlib
import re
import threading
import uuid

import mariadb
import sqlglot
from sqlglot import exp as sqlglot_exp

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# ── SQL safety helpers ────────────────────────────────────────

# Node types that indicate write/DDL/dangerous operations
_DANGEROUS_NODES = (
    sqlglot_exp.Insert, sqlglot_exp.Update, sqlglot_exp.Delete,
    sqlglot_exp.Drop, sqlglot_exp.Create, sqlglot_exp.Alter,
    sqlglot_exp.Command,
)


def _validate_where_clause(where: str) -> str:
    """Validate a WHERE clause fragment using sqlglot AST parsing.

    Wraps the fragment in a synthetic SELECT, parses the AST, and
    rejects any dangerous nodes (writes, DDL, subqueries with writes).

    Returns:
        The validated WHERE clause string (from the original input).

    Raises:
        ValueError: If the clause is invalid or contains dangerous SQL.
    """
    if not where or not where.strip():
        return ""
    synthetic = f"SELECT * FROM _t WHERE {where}"
    try:
        parsed = sqlglot.parse_one(synthetic, dialect="mysql")
    except sqlglot.errors.ParseError as e:
        raise ValueError(f"Invalid WHERE clause: {e}") from e

    # Walk AST — reject dangerous nodes anywhere (including subqueries)
    where_node = parsed.find(sqlglot_exp.Where)
    if where_node is None:
        raise ValueError("Failed to parse WHERE clause")

    for node in where_node.walk():
        if isinstance(node, _DANGEROUS_NODES):
            raise ValueError(
                f"WHERE clause contains disallowed operation: {type(node).__name__}"
            )
        # Block subqueries to prevent data exfiltration via EXISTS/IN/etc.
        if isinstance(node, sqlglot_exp.Select):
            raise ValueError("Subqueries are not allowed in WHERE clauses")
        # Reject function calls that could have side effects
        if isinstance(node, sqlglot_exp.Anonymous):
            func_name = node.name.upper()
            if func_name in ("SLEEP", "BENCHMARK", "LOAD_FILE", "INTO_OUTFILE"):
                raise ValueError(f"WHERE clause contains disallowed function: {func_name}")

    return where.strip()


def _validate_select_query(sql: str) -> str:
    """Validate a full SELECT query using sqlglot AST parsing.

    Raises:
        ValueError: If the query is not a valid SELECT or contains dangerous operations.
    """
    stripped = sql.strip()
    try:
        parsed = sqlglot.parse_one(stripped, dialect="mysql")
    except sqlglot.errors.ParseError as e:
        raise ValueError(f"Invalid SQL query: {e}") from e

    # Top-level must be a SELECT
    if not isinstance(parsed, sqlglot_exp.Select):
        raise ValueError("Only SELECT queries are allowed")

    # Walk AST — reject dangerous nodes anywhere
    for node in parsed.walk():
        if isinstance(node, _DANGEROUS_NODES):
            raise ValueError(
                f"Query contains disallowed operation: {type(node).__name__}"
            )
        if isinstance(node, sqlglot_exp.Anonymous):
            func_name = node.name.upper()
            if func_name in ("SLEEP", "BENCHMARK", "LOAD_FILE", "INTO_OUTFILE"):
                raise ValueError(f"Query contains disallowed function: {func_name}")

    return stripped

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
            pool_name=f"seamless_rag_{uuid.uuid4().hex[:8]}",
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

    def _get_non_vector_columns(self, conn, table: str) -> list[str]:
        """Get all column names except the embedding vector column."""
        cursor = conn.cursor()
        try:
            cursor.execute(f"SHOW COLUMNS FROM {_validate_ident(table)}")
            return [
                row[0] for row in cursor.fetchall()
                if row[1] and "vector" not in row[1].lower()
            ]
        finally:
            cursor.close()

    def search(
        self, table: str, query_vec: list[float],
        top_k: int = 5, context_window: int = 0,
        where: str = "",
    ) -> list[dict]:
        """Vector similarity search with optional SQL filter.

        Args:
            table: Table name containing embedding column.
            query_vec: Query vector for cosine similarity.
            top_k: Number of results to return.
            context_window: Include neighboring chunks (0=disabled).
            where: Optional SQL WHERE clause (e.g. "price < 50 AND category = 'tools'").
                   Values should use the column names directly — this is appended
                   to the query as-is after a "WHERE" keyword.
        """
        t = _validate_ident(table)
        qb = _vec_bytes(query_vec)
        validated_where = _validate_where_clause(where) if where else ""
        where_clause = f"WHERE {validated_where}" if validated_where else ""
        with self._get_conn() as conn:
            cols = self._get_non_vector_columns(conn, t)
            col_list = ", ".join(cols)
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SET mhnsw_ef_search = 100")
                if context_window > 0 and "document_id" in cols and "chunk_order" in cols:
                    cursor.execute(
                        f"""
                        WITH closest AS (
                            SELECT id, document_id, chunk_order,
                                VEC_DISTANCE_COSINE(embedding, ?) AS distance
                            FROM {t} {where_clause}
                            ORDER BY distance LIMIT ?
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
                        SELECT {col_list},
                            VEC_DISTANCE_COSINE(embedding, ?) AS distance
                        FROM {t} {where_clause}
                        ORDER BY distance, id LIMIT ?
                        """,
                        (qb, top_k),
                    )
                return cursor.fetchall()
            finally:
                cursor.close()

    def get_new_rows(
        self, table: str, text_columns: str | list[str], last_id: int,
    ) -> list[dict]:
        t = _validate_ident(table)
        if isinstance(text_columns, str):
            text_columns = [text_columns]
        cols = ", ".join(_validate_ident(c) for c in text_columns)
        with self._get_conn() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(
                    f"SELECT id, {cols} FROM {t} WHERE id > ?"
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

        Uses sqlglot AST parsing to validate the query structurally.
        Rejects anything that is not a pure SELECT — writes, DDL,
        and dangerous functions are blocked even inside subqueries.
        """
        stripped = _validate_select_query(sql)
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
