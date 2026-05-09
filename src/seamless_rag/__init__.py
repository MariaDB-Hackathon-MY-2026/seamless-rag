"""Seamless-RAG: TOON-Native Auto-Embedding & RAG Toolkit for MariaDB."""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

# Single source of truth: the version declared in pyproject.toml. Read at
# import time from package metadata so it can never desync with what PyPI
# served. The fallback only fires for editable installs that haven't been
# pip-installed yet (rare; CI does pip install -e first).
try:
    __version__ = _pkg_version("seamless-rag")
except PackageNotFoundError:  # pragma: no cover — only hit before install
    __version__ = "0.0.0+unknown"

__all__ = ["SeamlessRAG", "__version__"]


def __getattr__(name: str):
    if name == "SeamlessRAG":
        from seamless_rag.core import SeamlessRAG

        return SeamlessRAG
    raise AttributeError(f"module 'seamless_rag' has no attribute {name!r}")
