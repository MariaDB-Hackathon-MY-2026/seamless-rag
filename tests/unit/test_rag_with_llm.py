"""
Tests for RAG engine with LLM integration.

Verifies that the RAG engine correctly calls the LLM provider when one is supplied,
and still works when no LLM is provided (backward compatibility).
"""
from unittest.mock import Mock

import pytest

from seamless_rag.pipeline.rag import RAGEngine


@pytest.fixture
def mock_llm():
    """Mock LLM provider."""
    llm = Mock()
    llm.generate.return_value = "Based on the context, the answer is: test answer."
    return llm


@pytest.fixture
def rag_with_llm(mock_provider, mock_storage, mock_llm):
    """RAG engine with mocked LLM."""
    return RAGEngine(
        provider=mock_provider, storage=mock_storage, llm=mock_llm,
    )


@pytest.fixture
def rag_without_llm(mock_provider, mock_storage):
    """RAG engine without LLM (backward compatible)."""
    return RAGEngine(provider=mock_provider, storage=mock_storage)


class TestRAGWithLLM:
    """Test RAG engine with LLM provider attached."""

    def test_ask_returns_answer(self, rag_with_llm):
        result = rag_with_llm.ask("What is the answer?")
        assert result.answer != ""
        assert "test answer" in result.answer

    def test_ask_calls_llm_generate(self, rag_with_llm, mock_llm):
        rag_with_llm.ask("test question")
        mock_llm.generate.assert_called_once()
        args = mock_llm.generate.call_args[0]
        assert args[0] == "test question"
        assert isinstance(args[1], str)
        assert len(args[1]) > 0

    def test_llm_receives_toon_context(self, rag_with_llm, mock_llm):
        rag_with_llm.ask("test")
        context = mock_llm.generate.call_args[0][1]
        assert "," in context or ":" in context

    def test_result_still_has_metrics(self, rag_with_llm):
        result = rag_with_llm.ask("test")
        assert result.json_tokens > 0
        assert result.toon_tokens > 0
        assert result.savings_pct > 0


class TestRAGWithoutLLM:
    """Test backward compatibility when no LLM is provided."""

    def test_ask_returns_empty_answer(self, rag_without_llm):
        result = rag_without_llm.ask("test")
        assert result.answer == ""

    def test_result_still_has_context(self, rag_without_llm):
        result = rag_without_llm.ask("test")
        assert result.context_toon != ""
        assert result.context_json != ""

    def test_result_still_has_metrics(self, rag_without_llm):
        result = rag_without_llm.ask("test")
        assert result.json_tokens > 0
        assert result.toon_tokens > 0
