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


class TestMultiColumnEmbed:
    """Test multi-column embedding — concatenating multiple columns."""

    def test_multi_column_batch_embed(self, embedder, mock_provider, mock_storage):
        """batch_embed with multiple columns concatenates values."""
        mock_storage.get_new_rows.side_effect = [
            [
                {"id": 1, "name": "Widget", "category": "Tools", "price": "29.99"},
                {"id": 2, "name": "Gadget", "category": "Tools", "price": "19.99"},
            ],
            [],
        ]
        mock_provider.embed_batch.return_value = [[0.1] * 384, [0.2] * 384]

        result = embedder.batch_embed("products", ["name", "category", "price"])

        assert result["embedded"] == 2
        assert result["failed"] == 0
        # Verify the texts passed to embed_batch are concatenated
        call_args = mock_provider.embed_batch.call_args[0][0]
        assert call_args[0] == "Widget — Tools — 29.99"
        assert call_args[1] == "Gadget — Tools — 19.99"

    def test_multi_column_skips_empty_values(self, embedder, mock_provider, mock_storage):
        """Multi-column embed skips None and empty values."""
        mock_storage.get_new_rows.side_effect = [
            [{"id": 1, "name": "Widget", "desc": None, "price": "29.99"}],
            [],
        ]
        mock_provider.embed_batch.return_value = [[0.1] * 384]

        embedder.batch_embed("products", ["name", "desc", "price"])

        call_args = mock_provider.embed_batch.call_args[0][0]
        assert call_args[0] == "Widget — 29.99"  # desc=None skipped

    def test_single_column_backward_compat(self, embedder, mock_provider, mock_storage):
        """Single column string still works (backward compatibility)."""
        mock_storage.get_new_rows.side_effect = [
            [{"id": 1, "content": "hello world"}],
            [],
        ]
        mock_provider.embed_batch.return_value = [[0.1] * 384]

        result = embedder.batch_embed("chunks", "content")

        assert result["embedded"] == 1
        call_args = mock_provider.embed_batch.call_args[0][0]
        assert call_args[0] == "hello world"

    def test_single_column_in_list_form(self, embedder, mock_provider, mock_storage):
        """Single column passed as list should work identically to string."""
        mock_storage.get_new_rows.side_effect = [
            [{"id": 1, "content": "hello world"}],
            [],
        ]
        mock_provider.embed_batch.return_value = [[0.1] * 384]

        result = embedder.batch_embed("chunks", ["content"])

        assert result["embedded"] == 1
        call_args = mock_provider.embed_batch.call_args[0][0]
        assert call_args[0] == "hello world"

    def test_multi_column_row_by_row_fallback(
        self, embedder, mock_provider, mock_storage,
    ):
        """Multi-column fallback also concatenates correctly."""
        mock_storage.get_new_rows.side_effect = [
            [{"id": 1, "name": "Widget", "category": "Tools"}],
            [],
        ]
        mock_provider.embed_batch.side_effect = RuntimeError("batch failed")
        mock_provider.embed.return_value = [0.1] * 384

        result = embedder.batch_embed("products", ["name", "category"])

        assert result["embedded"] == 1
        # Verify the text passed to single embed is concatenated
        mock_provider.embed.assert_called_once_with("Widget — Tools")

    def test_row_text_static_method(self):
        """_row_text helper correctly concatenates columns."""
        row = {"name": "Widget", "category": "Tools", "price": "29.99"}
        result = AutoEmbedder._row_text(row, ["name", "category", "price"])
        assert result == "Widget — Tools — 29.99"

    def test_row_text_single_column(self):
        """_row_text with single column returns value as-is."""
        row = {"content": "hello world"}
        result = AutoEmbedder._row_text(row, ["content"])
        assert result == "hello world"

    def test_row_text_skips_none_and_empty(self):
        """_row_text skips None and whitespace-only values."""
        row = {"a": "hello", "b": None, "c": "  ", "d": "world"}
        result = AutoEmbedder._row_text(row, ["a", "b", "c", "d"])
        assert result == "hello — world"
