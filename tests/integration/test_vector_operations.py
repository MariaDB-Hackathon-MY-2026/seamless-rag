"""
Integration tests for MariaDB VECTOR operations.

Requires: running MariaDB 11.7.2+ with VECTOR support.
Run with: make test-integration
"""
import array

import pytest


@pytest.mark.integration
class TestVectorInsert:
    """Test vector insertion via native binary protocol."""

    def test_insert_array_float32(self, db_cursor):
        """array.array('f') should be accepted as VECTOR parameter."""
        db_cursor.execute(
            "INSERT INTO test_documents (title) VALUES (?)", ("doc1",)
        )
        doc_id = db_cursor.lastrowid

        vec = array.array("f", [0.1] * 384)
        db_cursor.execute(
            "INSERT INTO test_chunks (document_id, chunk_order, content, embedding) VALUES (?, ?, ?, ?)",
            (doc_id, 0, "test content", vec),
        )
        assert db_cursor.lastrowid is not None

    def test_read_vector_as_bytes(self, db_cursor, sample_doc_with_chunks):
        """VECTOR column should return raw bytes on SELECT."""
        doc_id, _ = sample_doc_with_chunks
        db_cursor.execute("SELECT embedding FROM test_chunks WHERE document_id = ? LIMIT 1", (doc_id,))
        row = db_cursor.fetchone()
        assert isinstance(row[0], (bytes, bytearray))
        # 384 floats * 4 bytes each = 1536 bytes
        assert len(row[0]) == 384 * 4

    def test_deserialize_vector(self, db_cursor, sample_doc_with_chunks):
        """Raw bytes should deserialize back to float32 array."""
        doc_id, _ = sample_doc_with_chunks
        db_cursor.execute("SELECT embedding FROM test_chunks WHERE document_id = ? LIMIT 1", (doc_id,))
        raw = db_cursor.fetchone()[0]
        vec = array.array("f")
        vec.frombytes(raw)
        assert len(vec) == 384


@pytest.mark.integration
class TestVectorSearch:
    """Test VEC_DISTANCE_COSINE search with HNSW index."""

    def test_cosine_search_returns_results(self, db_cursor, sample_doc_with_chunks):
        doc_id, texts = sample_doc_with_chunks
        query_vec = array.array("f", [0.1] * 384)
        db_cursor.execute(
            """SELECT content, VEC_DISTANCE_COSINE(embedding, ?) AS distance
               FROM test_chunks
               ORDER BY distance ASC
               LIMIT 3""",
            (query_vec,),
        )
        results = db_cursor.fetchall()
        assert len(results) == 3
        # First result should be most similar (smallest distance)
        assert results[0][1] <= results[1][1]

    def test_cosine_distance_ordering(self, db_cursor, sample_doc_with_chunks):
        """Results must be ordered by ascending distance."""
        query_vec = array.array("f", [0.1] * 384)
        db_cursor.execute(
            """SELECT VEC_DISTANCE_COSINE(embedding, ?) AS distance
               FROM test_chunks ORDER BY distance LIMIT 10""",
            (query_vec,),
        )
        distances = [row[0] for row in db_cursor.fetchall()]
        assert distances == sorted(distances), "Results not sorted by distance"

    def test_dictionary_cursor_for_toon(self, dict_cursor, sample_doc_with_chunks):
        """Dictionary cursor returns list[dict] — ready for TOON encoding."""
        query_vec = array.array("f", [0.1] * 384)
        dict_cursor.execute(
            """SELECT id, content, VEC_DISTANCE_COSINE(embedding, ?) AS distance
               FROM test_chunks ORDER BY distance LIMIT 3""",
            (query_vec,),
        )
        results = dict_cursor.fetchall()
        assert isinstance(results[0], dict)
        assert "content" in results[0]
        assert "distance" in results[0]

    def test_hnsw_ef_search_tuning(self, db_cursor, sample_doc_with_chunks):
        """Verify mhnsw_ef_search session variable is settable."""
        db_cursor.execute("SET mhnsw_ef_search = 100")
        query_vec = array.array("f", [0.1] * 384)
        db_cursor.execute(
            """SELECT content FROM test_chunks
               ORDER BY VEC_DISTANCE_COSINE(embedding, ?) LIMIT 3""",
            (query_vec,),
        )
        results = db_cursor.fetchall()
        assert len(results) > 0


@pytest.mark.integration
class TestCTEContextWindow:
    """Test CTE-based context windowing for RAG."""

    def test_cte_with_neighbors(self, db_cursor, sample_doc_with_chunks):
        """CTE should retrieve matching chunks plus neighboring chunks."""
        doc_id, texts = sample_doc_with_chunks
        query_vec = array.array("f", [0.1] * 384)

        db_cursor.execute("""
            WITH closest AS (
                SELECT id, document_id, chunk_order,
                       VEC_DISTANCE_COSINE(embedding, ?) AS distance
                FROM test_chunks
                ORDER BY distance
                LIMIT 1
            )
            SELECT c.content, c.chunk_order,
                   closest.distance
            FROM closest
            JOIN test_chunks c ON c.document_id = closest.document_id
            WHERE c.chunk_order BETWEEN (closest.chunk_order - 1) AND (closest.chunk_order + 1)
            ORDER BY c.chunk_order
        """, (query_vec,))

        results = db_cursor.fetchall()
        # Should get the matching chunk plus up to 2 neighbors
        assert len(results) >= 1
        assert len(results) <= 3
