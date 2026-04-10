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


class SeamlessRAG:
    """Top-level facade for Seamless-RAG toolkit.

    Manages lifecycle of all dependencies and exposes a clean public API.
    """

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
        raise NotImplementedError("SeamlessRAG facade not yet implemented")

    def embed_table(self, table: str, text_column: str, batch_size: int = 64) -> None:
        """Bulk-embed all rows in a table that lack embeddings."""
        raise NotImplementedError

    def watch(self, table: str, text_column: str, interval: float = 2.0) -> None:
        """Watch a table for new inserts and auto-embed them."""
        raise NotImplementedError

    def ask(self, question: str, top_k: int = 5) -> object:
        """RAG query: embed question → search → TOON format → LLM → answer."""
        raise NotImplementedError

    def export(self, query: str) -> str:
        """Export a SQL query's results as TOON format."""
        raise NotImplementedError

    def benchmark(self, query: str, n_queries: int = 10) -> object:
        """Run token comparison benchmark."""
        raise NotImplementedError
