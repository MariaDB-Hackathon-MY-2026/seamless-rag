"""
Tests for the RAG query pipeline.

Verifies the full flow: question → embed → search → TOON format → answer
All using Protocol-based mocks (no DB, no LLM API needed).
"""
import pytest

from seamless_rag.pipeline.rag import RAGEngine, RAGResult


@pytest.fixture
def rag_engine(mock_provider, mock_storage):
    """Shared RAG engine fixture with mocked dependencies."""
    return RAGEngine(provider=mock_provider, storage=mock_storage)


class TestRAGPipeline:
    """Test the RAG query engine with mocked dependencies."""

    def test_ask_returns_rag_result(self, rag_engine):
        result = rag_engine.ask("What is climate change?")
        assert isinstance(result, RAGResult)

    def test_ask_calls_embed(self, rag_engine, mock_provider):
        rag_engine.ask("test question")
        mock_provider.embed.assert_called_once_with("test question")

    def test_ask_calls_search(self, rag_engine, mock_storage):
        rag_engine.ask("test question", top_k=5)
        mock_storage.search.assert_called_once()

    def test_result_has_toon_context(self, rag_engine):
        result = rag_engine.ask("test")
        assert result.context_toon is not None
        assert isinstance(result.context_toon, str)
        assert len(result.context_toon) > 0

    def test_result_has_token_counts(self, rag_engine):
        result = rag_engine.ask("test")
        assert result.json_tokens > 0
        assert result.toon_tokens > 0
        assert result.toon_tokens < result.json_tokens

    def test_result_has_savings_percentage(self, rag_engine):
        result = rag_engine.ask("test")
        assert 0 < result.savings_pct < 100

    def test_result_has_sources(self, rag_engine):
        result = rag_engine.ask("test")
        assert isinstance(result.sources, list)
        assert len(result.sources) > 0


class TestTokenBenchmarkInRAG:
    """Test token comparison via RAG results."""

    def test_json_tokens_counted(self, rag_engine):
        result = rag_engine.ask("test")
        assert isinstance(result.json_tokens, int)
        assert result.json_tokens > 0

    def test_toon_tokens_counted(self, rag_engine):
        result = rag_engine.ask("test")
        assert isinstance(result.toon_tokens, int)
        assert result.toon_tokens > 0

    def test_savings_calculation_correct(self, rag_engine):
        result = rag_engine.ask("test")
        expected = (result.json_tokens - result.toon_tokens) / result.json_tokens * 100
        assert abs(result.savings_pct - expected) < 0.1
