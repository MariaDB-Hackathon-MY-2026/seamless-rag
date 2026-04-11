"""
Tests for the Typer CLI commands.

Verifies init, ask, and export commands using CliRunner and
unittest.mock.patch to avoid real DB and provider connections.
"""
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from seamless_rag.cli import app
from seamless_rag.pipeline.rag import RAGResult

runner = CliRunner()


@pytest.fixture
def mock_rag():
    """Mock SeamlessRAG instance for CLI tests."""
    rag = MagicMock()
    rag.__enter__ = MagicMock(return_value=rag)
    rag.__exit__ = MagicMock(return_value=False)
    rag.ask.return_value = RAGResult(
        answer="Test answer",
        context_toon="[1,]{id,content}:\n  1,test content",
        context_json='[{"id": 1, "content": "test content"}]',
        json_tokens=20,
        toon_tokens=12,
        savings_pct=40.0,
        json_cost_usd=0.0006,
        toon_cost_usd=0.00036,
        savings_cost_usd=0.00024,
        sources=[{"id": 1, "content": "test content", "distance": 0.1}],
    )
    rag.export.return_value = "[1,]{id,name}:\n  1,Ada"
    return rag


class TestInitCommand:
    """Test the 'init' CLI command."""

    def test_init_exits_zero(self, mock_rag):
        """init command completes without error."""
        with patch("seamless_rag.cli._get_rag", return_value=mock_rag):
            result = runner.invoke(app, ["init"])
        assert result.exit_code == 0

    def test_init_calls_rag_init(self, mock_rag):
        """init command calls rag.init()."""
        with patch("seamless_rag.cli._get_rag", return_value=mock_rag):
            runner.invoke(app, ["init"])
        mock_rag.init.assert_called_once()

    def test_init_calls_rag_close(self, mock_rag):
        """init command calls rag.close() for cleanup."""
        with patch("seamless_rag.cli._get_rag", return_value=mock_rag):
            runner.invoke(app, ["init"])
        mock_rag.__exit__.assert_called_once()


class TestAskCommand:
    """Test the 'ask' CLI command."""

    def test_ask_exits_zero(self, mock_rag):
        """ask command completes without error."""
        with patch("seamless_rag.cli._get_rag", return_value=mock_rag):
            result = runner.invoke(app, ["ask", "What is testing?"])
        assert result.exit_code == 0

    def test_ask_shows_answer(self, mock_rag):
        """ask command displays the LLM answer."""
        with patch("seamless_rag.cli._get_rag", return_value=mock_rag):
            result = runner.invoke(app, ["ask", "What is testing?"])
        assert "Test answer" in result.output

    def test_ask_shows_toon_context(self, mock_rag):
        """ask command displays TOON-formatted context."""
        with patch("seamless_rag.cli._get_rag", return_value=mock_rag):
            result = runner.invoke(app, ["ask", "What is testing?"])
        assert "test content" in result.output

    def test_ask_shows_token_benchmark(self, mock_rag):
        """ask command displays token comparison table."""
        with patch("seamless_rag.cli._get_rag", return_value=mock_rag):
            result = runner.invoke(app, ["ask", "question"])
        assert "20" in result.output  # JSON tokens
        assert "12" in result.output  # TOON tokens

    def test_ask_no_results(self, mock_rag):
        """ask command shows guidance when no results found."""
        mock_rag.ask.return_value = RAGResult(
            answer="",
            context_toon="[0,]:",
            context_json="[]",
            json_tokens=0,
            toon_tokens=0,
            savings_pct=0.0,
            json_cost_usd=0.0,
            toon_cost_usd=0.0,
            savings_cost_usd=0.0,
            sources=[],
        )
        with patch("seamless_rag.cli._get_rag", return_value=mock_rag):
            result = runner.invoke(app, ["ask", "anything"])
        assert result.exit_code == 0
        assert "No results found" in result.output

    def test_ask_with_top_k(self, mock_rag):
        """ask command passes --top-k to rag.ask()."""
        with patch("seamless_rag.cli._get_rag", return_value=mock_rag):
            runner.invoke(app, ["ask", "question", "--top-k", "3"])
        mock_rag.ask.assert_called_once()
        call_kwargs = mock_rag.ask.call_args
        assert call_kwargs[1]["top_k"] == 3 or call_kwargs[0][1] == 3

    def test_ask_calls_close(self, mock_rag):
        """ask command calls rag.close() for cleanup."""
        with patch("seamless_rag.cli._get_rag", return_value=mock_rag):
            runner.invoke(app, ["ask", "question"])
        mock_rag.__exit__.assert_called_once()


class TestExportCommand:
    """Test the 'export' CLI command."""

    def test_export_exits_zero(self, mock_rag):
        """export command completes without error."""
        with patch("seamless_rag.cli._get_rag", return_value=mock_rag):
            result = runner.invoke(app, ["export", "SELECT 1"])
        assert result.exit_code == 0

    def test_export_shows_toon_output(self, mock_rag):
        """export command prints TOON-formatted output."""
        with patch("seamless_rag.cli._get_rag", return_value=mock_rag):
            result = runner.invoke(app, ["export", "SELECT id, name FROM t"])
        assert "Ada" in result.output

    def test_export_calls_close(self, mock_rag):
        """export command calls rag.close() for cleanup."""
        with patch("seamless_rag.cli._get_rag", return_value=mock_rag):
            runner.invoke(app, ["export", "SELECT 1"])
        mock_rag.__exit__.assert_called_once()
