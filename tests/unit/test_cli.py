"""
Tests for the Typer CLI commands.

Verifies init, ask, and export commands using CliRunner and
unittest.mock.patch to avoid real DB and provider connections.
"""
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from seamless_rag.cli import _chunk_text, app
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


class TestChunkText:
    """Regression tests for _chunk_text — must respect chunk_size on any input shape.

    The original sentence-only splitter (`re.split(r"(?<=[.!?])\\s+")`) returned
    one giant chunk for any text without sentence punctuation (TSV/CSV/log/code),
    silently breaking RAG over structured data. These tests lock in the
    fixed-window fallback so that regression can never re-ship.
    """

    def test_prose_splits_at_sentences(self):
        text = (
            "First sentence. Second sentence is here. Third one closes. "
            "Fourth one starts now. Fifth and final one."
        )
        chunks = _chunk_text(text, size=40, overlap=10)
        assert len(chunks) >= 2
        # Each chunk must respect the size budget.
        assert all(len(c) <= 40 + 20 for c in chunks)  # tiny grace for joiner

    def test_tsv_with_no_sentence_punctuation(self):
        # 200 short rows joined by \n — no '.', '!', '?' anywhere.
        rows = "\n".join(f"{i}\t1\t1\tname{i}\t0\t8\t2025/05/15" for i in range(200))
        chunks = _chunk_text(rows, size=200, overlap=20)
        # Original bug: returned one chunk of full length. Fix: many bounded chunks.
        assert len(chunks) > 5, f"expected many chunks, got {len(chunks)}"
        assert all(len(c) <= 240 for c in chunks), [len(c) for c in chunks[:3]]

    def test_single_long_line(self):
        # 5 KB blob, no whitespace at all (worst case)
        text = "x" * 5000
        chunks = _chunk_text(text, size=500, overlap=50)
        assert len(chunks) >= 9  # 5000 / 500 = 10 minus overlap savings
        assert all(len(c) <= 500 for c in chunks)
        # Overlap covers the boundary
        joined = "".join(c[: 500 - 50] for c in chunks[:-1]) + chunks[-1]
        assert joined.startswith("x" * 100)

    def test_csv_with_commas_no_periods(self):
        text = "\n".join("a,b,c,d,e,f" for _ in range(100))
        chunks = _chunk_text(text, size=100, overlap=10)
        assert len(chunks) > 3
        assert all(len(c) <= 120 for c in chunks)

    def test_short_input_returns_one_chunk(self):
        text = "Just a short note."
        chunks = _chunk_text(text, size=500, overlap=50)
        assert chunks == ["Just a short note."]

    def test_empty_input(self):
        assert _chunk_text("", size=500, overlap=50) == [""]
