"""
Integration test fixtures — real MariaDB via Docker.

Prerequisites: run 'make docker-up' first, or use 'make test-integration'
which auto-starts Docker before running tests.
"""
import array

import pytest

try:
    import mariadb
except ImportError:
    pytest.skip("mariadb connector not installed", allow_module_level=True)


def _get_db_config():
    """Get database config from environment or defaults."""
    import os
    return {
        "host": os.environ.get("DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", "seamless"),
        "database": os.environ.get("DB_NAME", "test_seamless_rag"),
    }


@pytest.fixture(scope="session")
def db_connection():
    """Create a MariaDB connection for the test session."""
    config = _get_db_config()
    try:
        conn = mariadb.connect(**config)
    except mariadb.Error as e:
        pytest.skip(f"MariaDB not available: {e}")
        return

    conn.autocommit = True
    cursor = conn.cursor()

    # Create test schema
    cursor.execute("DROP TABLE IF EXISTS test_chunks")
    cursor.execute("DROP TABLE IF EXISTS test_documents")

    cursor.execute("""
        CREATE TABLE test_documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(512) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE test_chunks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            document_id INT NOT NULL,
            chunk_order INT NOT NULL,
            content LONGTEXT NOT NULL,
            embedding VECTOR(384) NOT NULL,
            VECTOR INDEX (embedding) DISTANCE=cosine,
            FOREIGN KEY (document_id) REFERENCES test_documents(id),
            INDEX idx_doc_order (document_id, chunk_order)
        )
    """)

    cursor.close()
    yield conn

    # Cleanup
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS test_chunks")
    cursor.execute("DROP TABLE IF EXISTS test_documents")
    cursor.close()
    conn.close()


@pytest.fixture
def db_cursor(db_connection):
    """Fresh cursor, cleans up test data after each test."""
    cursor = db_connection.cursor()
    yield cursor
    # Clean test data
    cursor.execute("DELETE FROM test_chunks")
    cursor.execute("DELETE FROM test_documents")
    cursor.close()


@pytest.fixture
def dict_cursor(db_connection):
    """Dictionary cursor for TOON-ready output."""
    cursor = db_connection.cursor(dictionary=True)
    yield cursor
    cursor.execute("DELETE FROM test_chunks")
    cursor.execute("DELETE FROM test_documents")
    cursor.close()


@pytest.fixture
def sample_doc_with_chunks(db_cursor):
    """Insert a sample document with chunks and embeddings."""
    db_cursor.execute(
        "INSERT INTO test_documents (title) VALUES (?)",
        ("Test Document",),
    )
    doc_id = db_cursor.lastrowid

    texts = [
        "Climate change affects biodiversity through multiple mechanisms.",
        "Rising temperatures force species to migrate to new habitats.",
        "Ocean acidification reduces availability of carbonate ions.",
    ]

    for i, text in enumerate(texts):
        vec = array.array("f", [0.1 + i * 0.05] * 384)
        db_cursor.execute(
            "INSERT INTO test_chunks (document_id, chunk_order, content, embedding) VALUES (?, ?, ?, ?)",
            (doc_id, i, text, vec),
        )

    return doc_id, texts
