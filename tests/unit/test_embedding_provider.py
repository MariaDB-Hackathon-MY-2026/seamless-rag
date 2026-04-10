"""
Tests for the embedding provider protocol and implementations.

Verifies:
- Protocol compliance
- Vector dimensions
- Batch processing
- Error handling
"""
import pytest

from seamless_rag.providers.protocol import EmbeddingProvider
from seamless_rag.providers.sentence_transformers import SentenceTransformersProvider


class TestEmbeddingProviderProtocol:
    """Verify provider implementations satisfy the protocol."""

    def test_mock_satisfies_protocol(self, mock_provider):
        """Mock provider is a valid EmbeddingProvider."""
        assert hasattr(mock_provider, "dimensions")
        assert hasattr(mock_provider, "embed")
        assert hasattr(mock_provider, "embed_batch")

    def test_mock_returns_correct_dimensions(self, mock_provider):
        result = mock_provider.embed("test")
        assert len(result) == mock_provider.dimensions

    def test_mock_batch_returns_list_of_lists(self, mock_provider):
        result = mock_provider.embed_batch(["a", "b"])
        assert isinstance(result, list)
        assert all(isinstance(v, list) for v in result)


class TestSentenceTransformersProvider:
    """Tests for the default local embedding provider."""

    @pytest.fixture
    def provider(self):
        """Create a real SentenceTransformers provider (downloads model on first use)."""
        return SentenceTransformersProvider(model_name="all-MiniLM-L6-v2")

    @pytest.mark.slow
    def test_dimensions_384(self, provider):
        assert provider.dimensions == 384

    @pytest.mark.slow
    def test_embed_returns_list_of_floats(self, provider):
        result = provider.embed("Hello world")
        assert isinstance(result, list)
        assert len(result) == 384
        assert all(isinstance(v, float) for v in result)

    @pytest.mark.slow
    def test_embed_batch(self, provider):
        texts = ["Hello", "World", "Test"]
        result = provider.embed_batch(texts)
        assert len(result) == 3
        assert all(len(v) == 384 for v in result)

    @pytest.mark.slow
    def test_different_texts_different_embeddings(self, provider):
        v1 = provider.embed("The cat sat on the mat")
        v2 = provider.embed("Quantum physics explains the universe")
        # Cosine similarity should be low for unrelated texts
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a**2 for a in v1) ** 0.5
        norm2 = sum(b**2 for b in v2) ** 0.5
        similarity = dot / (norm1 * norm2)
        assert similarity < 0.8, f"Unrelated texts too similar: {similarity:.3f}"

    @pytest.mark.slow
    def test_similar_texts_similar_embeddings(self, provider):
        v1 = provider.embed("Climate change affects the environment")
        v2 = provider.embed("Global warming impacts the ecosystem")
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a**2 for a in v1) ** 0.5
        norm2 = sum(b**2 for b in v2) ** 0.5
        similarity = dot / (norm1 * norm2)
        assert similarity > 0.5, f"Related texts not similar enough: {similarity:.3f}"


class TestProviderEdgeCases:
    """Test edge cases for embedding providers using mocks."""

    def test_empty_string(self, mock_provider):
        """Provider must handle empty string input."""
        mock_provider.embed("")
        mock_provider.embed.assert_called_once_with("")

    def test_very_long_text(self, mock_provider):
        """Provider must handle long text (model truncates internally)."""
        long_text = "word " * 10000
        mock_provider.embed(long_text)
        mock_provider.embed.assert_called_once()

    def test_batch_single_item(self, mock_provider):
        """Batch with single item should work."""
        mock_provider.embed_batch(["single"])
        mock_provider.embed_batch.assert_called_once()

    def test_batch_empty_list(self, mock_provider):
        """Batch with empty list should return empty list."""
        mock_provider.embed_batch.return_value = []
        result = mock_provider.embed_batch([])
        assert result == []
