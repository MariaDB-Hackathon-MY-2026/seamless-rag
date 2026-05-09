"""Seamless-RAG: TOON-Native Auto-Embedding & RAG Toolkit for MariaDB."""

__version__ = "0.1.3"

__all__ = ["SeamlessRAG"]


def __getattr__(name: str):
    if name == "SeamlessRAG":
        from seamless_rag.core import SeamlessRAG

        return SeamlessRAG
    raise AttributeError(f"module 'seamless_rag' has no attribute {name!r}")
