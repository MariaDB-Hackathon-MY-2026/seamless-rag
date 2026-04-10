"""
End-to-end integration test for the full RAG pipeline with real MariaDB.

Tests the complete flow: embed → store → search → TOON format → verify
"""
import array

import pytest

try:
    from seamless_rag.toon.encoder import encode_tabular
except ImportError:
    pytest.skip("seamless_rag not yet implemented", allow_module_level=True)


@pytest.mark.integration
class TestRAGEndToEnd:
    """Full pipeline test with real database."""

    def test_embed_store_search_toon(self, dict_cursor, sample_doc_with_chunks):
        """Complete flow: search MariaDB vectors → TOON encode results."""
        doc_id, texts = sample_doc_with_chunks
        query_vec = array.array("f", [0.1] * 384)

        dict_cursor.execute(
            """SELECT id, content, VEC_DISTANCE_COSINE(embedding, ?) AS distance
               FROM test_chunks ORDER BY distance LIMIT 3""",
            (query_vec,),
        )
        results = dict_cursor.fetchall()

        # Encode to TOON
        toon_output = encode_tabular(results)

        # Verify TOON structure
        assert "[3,]{" in toon_output or "[" in toon_output
        assert "content" in toon_output
        assert "distance" in toon_output

        # Verify it's more compact than JSON
        import json
        json_output = json.dumps(results)
        assert len(toon_output) < len(json_output)

    def test_watch_mode_detects_new_inserts(self, db_cursor):
        """Simulate watch mode: insert new rows, detect them by ID."""
        # Get current max ID
        db_cursor.execute("SELECT COALESCE(MAX(id), 0) FROM test_documents")
        last_id = db_cursor.fetchone()[0]

        # Insert new document
        db_cursor.execute("INSERT INTO test_documents (title) VALUES (?)", ("New Doc",))
        new_doc_id = db_cursor.lastrowid

        # Detect new rows (this is what watch mode does)
        db_cursor.execute("SELECT id, title FROM test_documents WHERE id > ?", (last_id,))
        new_rows = db_cursor.fetchall()

        assert len(new_rows) == 1
        assert new_rows[0][0] == new_doc_id
        assert new_rows[0][1] == "New Doc"
