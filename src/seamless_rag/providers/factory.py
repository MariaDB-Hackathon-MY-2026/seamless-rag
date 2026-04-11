"""Embedding provider factory — create the right provider from Settings."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from seamless_rag.config import Settings
    from seamless_rag.providers.protocol import EmbeddingProvider


_GEMINI_DEFAULTS = {"model": "gemini-embedding-001", "dimensions": 768}
_OPENAI_DEFAULTS = {"model": "text-embedding-3-large", "dimensions": 3072}
_LOCAL_MODEL = "BAAI/bge-small-en-v1.5"
_LOCAL_DIMENSIONS = 384

# Prefixes that identify each provider's models
_GEMINI_PREFIXES = ("gemini-",)
_OPENAI_PREFIXES = ("text-embedding-",)
_LOCAL_PREFIXES = ("BAAI/", "all-", "sentence-transformers/")


def _is_foreign_model(model: str, provider: str) -> bool:
    """Check if model name belongs to a different provider."""
    if provider == "gemini":
        return model.startswith(_OPENAI_PREFIXES + _LOCAL_PREFIXES)
    if provider == "openai":
        return model.startswith(_GEMINI_PREFIXES + _LOCAL_PREFIXES)
    if provider == "sentence-transformers":
        return model.startswith(_GEMINI_PREFIXES + _OPENAI_PREFIXES)
    return False


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Create an embedding provider based on settings.embedding_provider.

    Supported providers:
        - "sentence-transformers": Local model (default, no API key needed)
        - "gemini": Google Gemini via google-genai SDK
        - "openai": OpenAI via openai SDK
    """
    provider = settings.embedding_provider.lower().strip()
    model = settings.embedding_model.strip()
    dims = settings.embedding_dimensions

    if provider == "sentence-transformers":
        from seamless_rag.providers.sentence_transformers import SentenceTransformersProvider

        if _is_foreign_model(model, provider):
            model = "BAAI/bge-small-en-v1.5"
        return SentenceTransformersProvider(model_name=model)

    # Detect if user left everything at local defaults (no explicit config)
    is_unconfigured = model == _LOCAL_MODEL and dims == _LOCAL_DIMENSIONS

    if provider == "gemini":
        from seamless_rag.providers.gemini import GeminiEmbeddingProvider

        if not settings.embedding_api_key:
            raise ValueError("EMBEDDING_API_KEY required for Gemini provider")
        if _is_foreign_model(model, provider) or is_unconfigured:
            model = _GEMINI_DEFAULTS["model"]
            dims = _GEMINI_DEFAULTS["dimensions"]
        return GeminiEmbeddingProvider(
            api_key=settings.embedding_api_key, model=model, dimensions=dims,
        )

    if provider == "openai":
        from seamless_rag.providers.openai_provider import OpenAIEmbeddingProvider

        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY required for OpenAI embedding provider")
        if _is_foreign_model(model, provider) or is_unconfigured:
            model = _OPENAI_DEFAULTS["model"]
            dims = _OPENAI_DEFAULTS["dimensions"]
        return OpenAIEmbeddingProvider(
            api_key=api_key, model=model, dimensions=dims,
        )

    raise ValueError(
        f"Unknown embedding provider: {provider!r}. "
        f"Supported: sentence-transformers, gemini, openai"
    )
