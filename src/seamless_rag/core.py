"""
SeamlessRAG facade — the single entry point for the toolkit.

Usage:
    rag = SeamlessRAG(host="localhost", database="seamless_rag", password="seamless")
    rag.embed_table("chunks", text_column="content")
    result = rag.ask("What are the key findings?")
    print(result.context_toon)
    print(f"Tokens saved: {result.savings_pct:.1f}%")
"""
from __future__ import annotations

import logging

from seamless_rag.config import Settings
from seamless_rag.pipeline.embedder import AutoEmbedder
from seamless_rag.pipeline.rag import RAGEngine, RAGResult
from seamless_rag.storage.mariadb import MariaDBVectorStore
from seamless_rag.toon.encoder import encode_tabular

logger = logging.getLogger(__name__)


def _make_provider(settings: Settings):
    """Lazy-load embedding provider to avoid slow import at CLI --help time."""
    from seamless_rag.providers.factory import create_embedding_provider

    return create_embedding_provider(settings)


def _make_llm(settings: Settings):
    """Lazy-load LLM provider."""
    from seamless_rag.llm.factory import create_llm_provider

    return create_llm_provider(settings)


class SeamlessRAG:
    """Top-level facade for Seamless-RAG toolkit."""

    _NO_LLM = object()  # sentinel: distinguishes "not tried" from "tried, unavailable"

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
        default_model = self._settings.embedding_model == "BAAI/bge-small-en-v1.5"
        if model != "all-MiniLM-L6-v2" and default_model:
            self._settings.embedding_model = model
        self._store = MariaDBVectorStore(
            host=host, port=port, user=user, password=password, database=database,
        )
        self._provider = None  # lazy
        self._llm = self._NO_LLM  # lazy, sentinel = not yet attempted
        self._embedder = None
        self._rag = None

    def _ensure_provider(self):
        if self._provider is None:
            self._provider = _make_provider(self._settings)
        return self._provider

    def _ensure_embedder(self):
        if self._embedder is None:
            self._embedder = AutoEmbedder(
                provider=self._ensure_provider(), store=self._store,
            )
        return self._embedder

    def _get_llm(self):
        """Get LLM provider, creating it on first call. Returns None if unavailable."""
        if self._llm is self._NO_LLM:
            try:
                self._llm = _make_llm(self._settings)
            except (ValueError, ImportError) as e:
                logger.warning("LLM provider not available: %s", e)
                self._llm = None
        return self._llm

    def _ensure_rag(self):
        if self._rag is None:
            self._rag = RAGEngine(
                provider=self._ensure_provider(), storage=self._store,
                table=self._table, llm=self._get_llm(),
            )
        elif self._rag._llm is None and self._get_llm() is not None:
            # LLM became available after initial RAG creation
            self._rag._llm = self._llm
        return self._rag

    def init(self, dimensions: int = 384) -> None:
        """Create schema (documents + chunks tables) if not exists."""
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
        self, table: str | None = None, text_column: str = "content", batch_size: int = 64,
    ) -> dict:
        """Bulk-embed all rows in a table that lack embeddings."""
        return self._ensure_embedder().batch_embed(
            table or self._table, text_column, batch_size=batch_size,
        )

    def watch(
        self, table: str | None = None, text_column: str = "content", interval: float = 2.0,
    ) -> None:
        """Watch a table for new inserts and auto-embed them."""
        self._ensure_embedder().watch(table or self._table, text_column, interval=interval)

    def ask(self, question: str, top_k: int = 5) -> RAGResult:
        """RAG query: embed question -> search -> TOON format -> answer."""
        return self._ensure_rag().ask(question, top_k=top_k)

    def export(self, query: str) -> str:
        """Export a SQL query's results as TOON format."""
        rows = self._store.execute_query(query)
        return encode_tabular(rows) if rows else "[0,]:"

    def close(self) -> None:
        self._store.close()
