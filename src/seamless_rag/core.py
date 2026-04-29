"""
SeamlessRAG facade — the single entry point for the toolkit.

Usage:
    with SeamlessRAG(host="localhost", database="seamless_rag") as rag:
        rag.init()
        rag.ingest("doc1", ["chunk1", "chunk2"])
        result = rag.ask("What are the key findings?")
        print(result.context_toon)
        print(f"Tokens saved: {result.savings_pct:.1f}%")
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from seamless_rag.config import Settings
from seamless_rag.pipeline.embedder import AutoEmbedder
from seamless_rag.pipeline.rag import RAGEngine, RAGResult
from seamless_rag.storage.mariadb import MariaDBVectorStore
from seamless_rag.toon.encoder import encode_tabular

if TYPE_CHECKING:
    from seamless_rag.llm.protocol import LLMProvider
    from seamless_rag.providers.protocol import EmbeddingProvider

logger = logging.getLogger(__name__)


def _make_provider(settings: Settings) -> EmbeddingProvider:
    """Lazy-load embedding provider to avoid slow import at CLI --help time."""
    from seamless_rag.providers.factory import create_embedding_provider

    return create_embedding_provider(settings)


def _make_llm(settings: Settings) -> LLMProvider:
    """Lazy-load LLM provider."""
    from seamless_rag.llm.factory import create_llm_provider

    return create_llm_provider(settings)


class SeamlessRAG:
    """Top-level facade for Seamless-RAG toolkit.

    Supports context manager for automatic cleanup:

        with SeamlessRAG(host="localhost") as rag:
            result = rag.ask("question")
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 3306,
        user: str = "root",
        password: str = "seamless",
        database: str = "seamless_rag",
        model: str = "all-MiniLM-L6-v2",
        table: str = "chunks",
        settings: Settings | None = None,
    ) -> None:
        self._table = table
        self._settings = settings or Settings()
        # Thread model param through to settings if caller overrode it
        if model != "all-MiniLM-L6-v2":
            self._settings.embedding_model = model
        self._store = MariaDBVectorStore(
            host=host, port=port, user=user, password=password, database=database,
        )
        self._provider: EmbeddingProvider | None = None
        self._llm: LLMProvider | None = None
        self._llm_attempted = False
        self._embedder: AutoEmbedder | None = None
        self._rag: RAGEngine | None = None

    def __enter__(self) -> SeamlessRAG:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _ensure_provider(self) -> EmbeddingProvider:
        if self._provider is None:
            self._provider = _make_provider(self._settings)
        return self._provider

    def _ensure_embedder(self) -> AutoEmbedder:
        if self._embedder is None:
            self._embedder = AutoEmbedder(
                provider=self._ensure_provider(), store=self._store,
            )
        return self._embedder

    def _get_llm(self) -> LLMProvider | None:
        """Get LLM provider, creating it on first call. Returns None if unavailable."""
        if not self._llm_attempted:
            self._llm_attempted = True
            try:
                self._llm = _make_llm(self._settings)
            except (ValueError, ImportError) as e:
                logger.warning("LLM provider not available: %s", e)
        return self._llm

    def _ensure_rag(self) -> RAGEngine:
        if self._rag is None:
            self._rag = RAGEngine(
                provider=self._ensure_provider(), storage=self._store,
                table=self._table, llm=self._get_llm(),
            )
        return self._rag

    def init(self, dimensions: int | None = None) -> None:
        """Create schema (documents + chunks tables) if not exists.

        If dimensions is not specified, uses the embedding provider's dimensions.
        """
        if dimensions is None:
            dimensions = self._ensure_provider().dimensions
        self._store.init_schema(dimensions=dimensions)
        logger.info("Schema initialized (dimensions=%d)", dimensions)

    def ingest(self, title: str, texts: list[str]) -> int:
        """Ingest a document: create document row + embed and store all chunks."""
        provider = self._ensure_provider()
        doc_id = self._store.insert_document(title)
        embeddings = provider.embed_batch(texts)
        for i, (text, emb) in enumerate(zip(texts, embeddings, strict=True)):
            self._store.insert_chunk(doc_id, i, text, emb)
        logger.info("Ingested '%s' (%d chunks)", title, len(texts))
        return doc_id

    def embed_table(
        self,
        table: str | None = None,
        text_column: str | list[str] = "content",
        batch_size: int = 64,
    ) -> dict:
        """Bulk-embed all rows in a table that lack embeddings.

        Args:
            text_column: Single column name or list of columns to concatenate
                for richer semantic embeddings (e.g. ["name", "category", "price"]).
        """
        return self._ensure_embedder().batch_embed(
            table or self._table, text_column, batch_size=batch_size,
        )

    def watch(
        self,
        table: str | None = None,
        text_column: str | list[str] = "content",
        interval: float = 2.0,
    ) -> None:
        """Watch a table for new inserts and auto-embed them."""
        self._ensure_embedder().watch(table or self._table, text_column, interval=interval)

    def ask(
        self,
        question: str,
        top_k: int = 5,
        where: str = "",
        mmr: bool = False,
        mmr_lambda: float = 0.5,
        context_window: int = 0,
    ) -> RAGResult:
        """RAG query: embed → search → TOON → LLM → benchmark.

        Args:
            question: Natural language query.
            top_k: Number of results.
            where: SQL WHERE filter for hybrid search (e.g. "price < 50").
            mmr: Apply MMR diversity selection.
            mmr_lambda: Relevance/diversity trade-off (0=diverse, 1=relevant).
            context_window: Include neighboring chunks (0=disabled).
        """
        return self._ensure_rag().ask(
            question, top_k=top_k, where=where,
            mmr=mmr, mmr_lambda=mmr_lambda,
            context_window=context_window,
        )

    def export(self, query: str) -> str:
        """Export a SQL query's results as TOON format."""
        rows = self._store.execute_query(query)
        return encode_tabular(rows) if rows else "[0,]:"

    def describe_schema(self, table: str | None = None) -> dict:
        """Return DDL + indexes + row_count for a vector table."""
        return self._store.describe_schema(table or self._table)

    def compare_vec_distance(
        self, table: str | None = None, query: str = "", top_k: int = 3,
    ) -> dict:
        """Compare bare VEC_DISTANCE() (auto-pick) vs explicit VEC_DISTANCE_COSINE().

        Demonstrates a MariaDB-only feature: VEC_DISTANCE() reads the index's
        configured DISTANCE metric and applies it transparently. Returns
        {"auto": [...], "explicit": [...]} where each list contains
        dicts of {"id", "distance"} ordered by ascending distance.
        """
        embedding = self._ensure_provider().embed(query)
        return self._store.compare_vec_distance(
            table or self._table, embedding, top_k=top_k,
        )

    def close(self) -> None:
        """Close the database connection."""
        self._store.close()
