"""
Tests for AutoEmbedder batch and watch pipeline.

Verifies batch_embed counts, empty-table handling, and error isolation
using Protocol-based mocks (no DB or API keys required).
"""
from unittest.mock import Mock

import pytest

from seamless_rag.pipeline.embedder import AutoEmbedder


@pytest.fixture
def embedder(mock_provider, mock_storage):
    """AutoEmbedder with mocked provider and storage."""
    # Add methods not in conftest's StorageProtocol but used by AutoEmbedder
    mock_storage.insert_embeddings_batch = Mock()
    return AutoEmbedder(provider=mock_provider, store=mock_storage)


class TestBatchEmbed:
    """Test AutoEmbedder.batch_embed with various scenarios."""

    def test_returns_correct_counts(self, embedder, mock_provider, mock_storage):
        """batch_embed returns dict with embedded/failed/total keys."""
        mock_storage.get_new_rows.side_effect = [
            [
                {"id": 1, "content": "row one"},
                {"id": 2, "content": "row two"},
            ],
            [],  # second call returns empty to stop loop
        ]
        mock_provider.embed_batch.return_value = [[0.1] * 384, [0.2] * 384]

        result = embedder.batch_embed("chunks", "content")

        assert result["embedded"] == 2
        assert result["failed"] == 0
        assert result["total"] == 2

    def test_empty_table_returns_zero_counts(self, embedder, mock_storage):
        """batch_embed on a table with no unembedded rows returns all zeros."""
        mock_storage.get_new_rows.return_value = []

        result = embedder.batch_embed("chunks", "content")

        assert result == {"embedded": 0, "failed": 0, "total": 0}

    def test_error_isolation_row_by_row_fallback(self, embedder, mock_provider, mock_storage):
        """When batch embed fails, falls back to row-by-row; failed rows are counted."""
        mock_storage.get_new_rows.side_effect = [
            [
                {"id": 1, "content": "good row"},
                {"id": 2, "content": "bad row"},
            ],
            [],
        ]
        # Batch call fails, triggering row-by-row fallback
        mock_provider.embed_batch.side_effect = RuntimeError("batch failed")
        # Row-by-row: first succeeds, second fails
        mock_provider.embed.side_effect = [
            [0.1] * 384,
            RuntimeError("row failed"),
        ]

        result = embedder.batch_embed("chunks", "content")

        assert result["embedded"] == 1
        assert result["failed"] == 1
        assert result["total"] == 2

    def test_all_rows_fail_in_fallback(self, embedder, mock_provider, mock_storage):
        """When every row fails in fallback, all are counted as failed."""
        mock_storage.get_new_rows.side_effect = [
            [
                {"id": 1, "content": "bad one"},
                {"id": 2, "content": "bad two"},
            ],
            [],
        ]
        mock_provider.embed_batch.side_effect = RuntimeError("batch failed")
        mock_provider.embed.side_effect = RuntimeError("always fails")

        result = embedder.batch_embed("chunks", "content")

        assert result["embedded"] == 0
        assert result["failed"] == 2
        assert result["total"] == 2

    def test_calls_store_insert_embeddings_batch(self, embedder, mock_provider, mock_storage):
        """Successful batch calls insert_embeddings_batch on the store."""
        mock_storage.get_new_rows.side_effect = [
            [{"id": 1, "content": "text"}],
            [],
        ]
        mock_provider.embed_batch.return_value = [[0.1] * 384]

        embedder.batch_embed("chunks", "content")

        mock_storage.insert_embeddings_batch.assert_called_once_with(
            "chunks", [1], [[0.1] * 384],
        )

    def test_multiple_batches(self, embedder, mock_provider, mock_storage):
        """batch_embed processes rows in batches of batch_size."""
        rows = [{"id": i, "content": f"row {i}"} for i in range(1, 4)]
        mock_storage.get_new_rows.side_effect = [rows, []]
        mock_provider.embed_batch.return_value = [[0.1] * 384]

        result = embedder.batch_embed("chunks", "content", batch_size=2)

        assert result["embedded"] == 3
        assert result["total"] == 3
        # Two batch calls: first with 2 rows, second with 1 row
        assert mock_provider.embed_batch.call_count == 2

    def test_fallback_calls_insert_embedding_per_row(
        self, embedder, mock_provider, mock_storage,
    ):
        """Row-by-row fallback calls insert_embedding for each successful row."""
        mock_storage.get_new_rows.side_effect = [
            [{"id": 5, "content": "text"}],
            [],
        ]
        mock_provider.embed_batch.side_effect = RuntimeError("batch failed")
        mock_provider.embed.return_value = [0.1] * 384

        embedder.batch_embed("chunks", "content")

        mock_storage.insert_embedding.assert_called_once_with(
            "chunks", 5, [0.1] * 384,
        )
