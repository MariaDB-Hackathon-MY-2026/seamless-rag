"""
Tests for SeamlessRAG facade.

Verifies lazy loading, init/close delegation, and ask() pipeline
using unittest.mock.patch to avoid real DB and provider connections.
"""
from unittest.mock import MagicMock, patch

import pytest

from seamless_rag.pipeline.rag import RAGResult


@pytest.fixture
def mock_store():
    """Mock MariaDBVectorStore that avoids real DB connections."""
    store = MagicMock()
    store.search.return_value = [
        {"id": 1, "content": "test content", "distance": 0.1},
    ]
    return store


@pytest.fixture
def mock_emb_provider():
    """Mock embedding provider with deterministic vectors."""
    provider = MagicMock()
    provider.dimensions = 384
    provider.embed.return_value = [0.1] * 384
    provider.embed_batch.return_value = [[0.1] * 384]
    return provider


@pytest.fixture
def rag_facade(mock_store, mock_emb_provider):
    """SeamlessRAG instance with mocked store and provider."""
    with patch("seamless_rag.core.MariaDBVectorStore", return_value=mock_store):
        from seamless_rag.core import SeamlessRAG
        rag = SeamlessRAG()
    # Inject the mock provider so _ensure_provider returns it
    rag._provider = mock_emb_provider
    return rag


class TestSeamlessRAGInit:
    """Test SeamlessRAG initialization and schema setup."""

    def test_init_calls_store_init_schema(self, rag_facade, mock_store, mock_emb_provider):
        """init() delegates to store.init_schema with provider dimensions."""
        rag_facade.init()
        mock_store.init_schema.assert_called_once_with(dimensions=384)

    def test_init_with_explicit_dimensions(self, rag_facade, mock_store):
        """init(dimensions=768) passes explicit value, not provider default."""
        rag_facade.init(dimensions=768)
        mock_store.init_schema.assert_called_once_with(dimensions=768)


class TestLazyLoading:
    """Test lazy initialization of provider and dependent components."""

    def test_provider_is_none_before_first_use(self, mock_store):
        """Provider is not created at construction time."""
        with patch("seamless_rag.core.MariaDBVectorStore", return_value=mock_store):
            from seamless_rag.core import SeamlessRAG
            rag = SeamlessRAG()
        assert rag._provider is None

    def test_ensure_provider_creates_provider(self, mock_store):
        """_ensure_provider lazy-loads the embedding provider."""
        with patch("seamless_rag.core.MariaDBVectorStore", return_value=mock_store), \
             patch("seamless_rag.core._make_provider") as make_prov:
            from seamless_rag.core import SeamlessRAG
            mock_prov = MagicMock()
            mock_prov.dimensions = 384
            make_prov.return_value = mock_prov

            rag = SeamlessRAG()
            assert rag._provider is None
            rag._ensure_provider()
            assert rag._provider is mock_prov
            make_prov.assert_called_once()

    def test_ensure_provider_called_only_once(self, mock_store):
        """Repeated _ensure_provider calls don't re-create the provider."""
        with patch("seamless_rag.core.MariaDBVectorStore", return_value=mock_store), \
             patch("seamless_rag.core._make_provider") as make_prov:
            from seamless_rag.core import SeamlessRAG
            mock_prov = MagicMock()
            mock_prov.dimensions = 384
            make_prov.return_value = mock_prov

            rag = SeamlessRAG()
            rag._ensure_provider()
            rag._ensure_provider()
            make_prov.assert_called_once()


class TestAsk:
    """Test SeamlessRAG.ask() end-to-end with mocked deps."""

    @pytest.fixture(autouse=True)
    def _patch_rag_engine(self, rag_facade):
        """Inject a mock RAGEngine so ask() doesn't hit real pipeline."""
        mock_rag_engine = MagicMock()
        mock_rag_engine.ask.return_value = RAGResult(
            answer="mock answer",
            context_toon="[1,]{id,content}:\n  1,test",
            context_json='[{"id":1,"content":"test"}]',
            json_tokens=20,
            toon_tokens=12,
            savings_pct=40.0,
            json_cost_usd=0.0006,
            toon_cost_usd=0.00036,
            savings_cost_usd=0.00024,
            sources=[{"id": 1, "content": "test", "distance": 0.1}],
        )
        rag_facade._rag = mock_rag_engine

    def test_ask_returns_rag_result(self, rag_facade):
        """ask() returns a RAGResult instance."""
        result = rag_facade.ask("What is testing?")
        assert isinstance(result, RAGResult)

    def test_ask_result_has_sources(self, rag_facade):
        """ask() result includes the source documents from search."""
        result = rag_facade.ask("test question")
        assert isinstance(result.sources, list)
        assert len(result.sources) > 0

    def test_ask_result_has_token_counts(self, rag_facade):
        """ask() result includes JSON and TOON token counts."""
        result = rag_facade.ask("test")
        assert isinstance(result.json_tokens, int)
        assert isinstance(result.toon_tokens, int)
        assert result.json_tokens > 0


class TestClose:
    """Test SeamlessRAG.close() delegation."""

    def test_close_calls_store_close(self, rag_facade, mock_store):
        """close() delegates to the underlying store."""
        rag_facade.close()
        mock_store.close.assert_called_once()


class TestExport:
    """Test SeamlessRAG.export() SQL delegation."""

    def test_export_returns_toon_string(self, rag_facade, mock_store):
        """export() returns TOON-formatted string from query results."""
        mock_store.execute_query.return_value = [
            {"id": 1, "name": "Ada"},
        ]
        result = rag_facade.export("SELECT id, name FROM chunks")
        assert isinstance(result, str)
        assert "Ada" in result

    def test_export_empty_result(self, rag_facade, mock_store):
        """export() returns empty TOON for no results."""
        mock_store.execute_query.return_value = []
        result = rag_facade.export("SELECT id FROM chunks WHERE 1=0")
        assert result == "[0,]:"


class TestSchemaIntrospection:
    """Test SeamlessRAG.describe_schema() and compare_vec_distance() delegation."""

    def test_describe_schema_returns_store_payload(self, rag_facade, mock_store):
        """describe_schema() forwards to the store and returns its dict."""
        mock_store.describe_schema.return_value = {
            "table": "chunks",
            "ddl": "CREATE TABLE chunks (...)",
            "indexes": [{"Key_name": "embedding", "Index_type": "VECTOR"}],
            "row_count": 42,
        }
        info = rag_facade.describe_schema("chunks")
        mock_store.describe_schema.assert_called_once_with("chunks")
        assert info["row_count"] == 42
        assert info["indexes"][0]["Index_type"] == "VECTOR"

    def test_describe_schema_default_table(self, rag_facade, mock_store):
        """describe_schema() defaults to the facade's configured table."""
        mock_store.describe_schema.return_value = {
            "table": "chunks", "ddl": "", "indexes": [], "row_count": 0,
        }
        rag_facade.describe_schema()
        mock_store.describe_schema.assert_called_once_with("chunks")

    def test_compare_vec_distance_runs_both_queries(
        self, rag_facade, mock_store, mock_emb_provider,
    ):
        """compare_vec_distance() embeds the query and asks the store for both forms."""
        mock_store.compare_vec_distance.return_value = {
            "auto":     [{"id": 1, "distance": 0.12}, {"id": 2, "distance": 0.18}],
            "explicit": [{"id": 1, "distance": 0.12}, {"id": 2, "distance": 0.18}],
        }
        out = rag_facade.compare_vec_distance("chunks", query="climate", top_k=2)
        mock_emb_provider.embed.assert_called_once_with("climate")
        mock_store.compare_vec_distance.assert_called_once_with(
            "chunks", [0.1] * 384, top_k=2,
        )
        assert out["auto"] == out["explicit"], "expected identical rankings on cosine-indexed table"
