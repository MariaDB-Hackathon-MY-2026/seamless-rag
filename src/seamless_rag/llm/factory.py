"""LLM provider factory — create the right provider from Settings."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from seamless_rag.config import Settings
    from seamless_rag.llm.protocol import LLMProvider

logger = logging.getLogger(__name__)

# Known model prefixes per provider (anchored with separator)
_GEMINI_MODELS = {"gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"}
_OPENAI_MODELS = {"gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o1-mini", "o3-mini"}
_OLLAMA_DEFAULT = "qwen3:8b"


def _is_foreign_model(model: str, provider: str) -> bool:
    """Check if model name belongs to a different provider."""
    m = model.lower()
    if provider == "gemini":
        return m in _OPENAI_MODELS or m.startswith(("gpt-", "qwen", "llama", "mistral"))
    if provider == "openai":
        return m in _GEMINI_MODELS or m.startswith(("gemini-", "qwen", "llama", "mistral"))
    if provider == "ollama":
        return m in _GEMINI_MODELS or m in _OPENAI_MODELS or m.startswith(("gemini-", "gpt-"))
    return False


def create_llm_provider(settings: Settings) -> LLMProvider:
    """Create an LLM provider based on settings.llm_provider.

    Supported providers:
        - "ollama": Local Ollama (default, no API key needed)
        - "gemini": Google Gemini via google-genai SDK
        - "openai": OpenAI via openai SDK
    """
    provider = settings.llm_provider.lower().strip()
    model = settings.llm_model.strip()

    if provider == "ollama":
        from seamless_rag.llm.ollama import OllamaLLMProvider

        if _is_foreign_model(model, provider):
            logger.warning("Model %r not compatible with Ollama, using qwen3:8b", model)
            model = "qwen3:8b"
        return OllamaLLMProvider(
            model=model,
            base_url=settings.llm_base_url or "http://localhost:11434",
        )

    if provider == "gemini":
        from seamless_rag.llm.gemini import GeminiLLMProvider

        api_key = settings.llm_api_key or settings.embedding_api_key
        if not api_key:
            raise ValueError("LLM_API_KEY or EMBEDDING_API_KEY required for Gemini LLM")
        if _is_foreign_model(model, provider):
            model = "gemini-2.5-flash"
        return GeminiLLMProvider(api_key=api_key, model=model)

    if provider == "openai":
        from seamless_rag.llm.openai_provider import OpenAILLMProvider

        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY required for OpenAI LLM")
        if _is_foreign_model(model, provider):
            model = "gpt-4o"
        return OpenAILLMProvider(api_key=api_key, model=model)

    raise ValueError(
        f"Unknown LLM provider: {provider!r}. "
        f"Supported: ollama, gemini, openai"
    )
