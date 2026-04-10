"""
SeamlessRAG facade — the single entry point for the toolkit.

Unifies dependency injection: holds connection pool, embedding provider,
TOON encoder, and exposes the public API.

Usage:
    rag = SeamlessRAG(host="localhost", database="mydb")
    rag.embed_table("articles", text_column="content")
    result = rag.ask("What are the key findings?")
    print(result.answer)
    print(f"Tokens saved: {result.savings_pct:.1f}%")
"""
from __future__ import annotations

from seamless_rag.pipeline.embedder import AutoEmbedder
from seamless_rag.pipeline.rag import RAGEngine, RAGResult
from seamless_rag.providers.sentence_transformers import SentenceTransformersProvider
from seamless_rag.storage.mariadb import MariaDBVectorStore
from seamless_rag.toon.encoder import encode_tabular


class SeamlessRAG:
    """Top-level facade for Seamless-RAG toolkit."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "seamless_rag",
        provider: str = "sentence-transformers",
        model: str | None = None,
    ) -> None:
        self._store = MariaDBVectorStore(
            host=host, port=port, user=user, password=password, database=database,
        )
        self._provider = SentenceTransformersProvider(
            model_name=model or "all-MiniLM-L6-v2",
        )
        self._embedder = AutoEmbedder(provider=self._provider, store=self._store)
        self._rag = RAGEngine(provider=self._provider, storage=self._store)

    def embed_table(self, table: str, text_column: str = "content", batch_size: int = 64) -> dict:
        """Bulk-embed all rows in a table that lack embeddings."""
        return self._embedder.batch_embed(table, text_column, batch_size=batch_size)

    def watch(self, table: str, text_column: str = "content", interval: float = 2.0) -> None:
        """Watch a table for new inserts and auto-embed them."""
        self._embedder.watch(table, text_column, interval=interval)

    def ask(self, question: str, top_k: int = 5) -> RAGResult:
        """RAG query: embed question -> search -> TOON format -> answer."""
        return self._rag.ask(question, top_k=top_k)

    def export(self, query: str) -> str:
        """Export a SQL query's results as TOON format."""
        cursor = self._store._dict_cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        return encode_tabular(rows) if rows else "[0,]:"

    def close(self) -> None:
        """Close database connection."""
        self._store.close()
