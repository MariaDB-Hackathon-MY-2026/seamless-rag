"""
Tests for the embedding and LLM provider factories.

Verifies:
- Factory creates correct provider types
- Foreign model names are auto-corrected
- Missing API keys raise ValueError
- Unknown providers raise ValueError
"""
from unittest.mock import patch

import pytest

from seamless_rag.config import Settings
from seamless_rag.providers.factory import _is_foreign_model, create_embedding_provider


class TestEmbeddingProviderFactory:
    """Test create_embedding_provider with different configurations."""

    def test_creates_sentence_transformers_by_default(self):
        s = Settings(
            embedding_provider="sentence-transformers",
            embedding_model="all-MiniLM-L6-v2",
        )
        provider = create_embedding_provider(s)
        assert type(provider).__name__ == "SentenceTransformersProvider"

    def test_creates_gemini_provider(self):
        s = Settings(
            embedding_provider="gemini",
            embedding_model="gemini-embedding-001",
            embedding_api_key="test-key",
            embedding_dimensions=768,
        )
        with patch("seamless_rag.providers.gemini.genai.Client"):
            provider = create_embedding_provider(s)
        assert type(provider).__name__ == "GeminiEmbeddingProvider"
        assert provider.dimensions == 768

    def test_creates_openai_provider(self):
        s = Settings(
            embedding_provider="openai",
            openai_api_key="test-key",
            embedding_model="text-embedding-3-large",
            embedding_dimensions=3072,
        )
        with patch("seamless_rag.providers.openai_provider.OpenAI"):
            provider = create_embedding_provider(s)
        assert type(provider).__name__ == "OpenAIEmbeddingProvider"
        assert provider.dimensions == 3072

    def test_gemini_missing_key_raises(self):
        s = Settings(
            embedding_provider="gemini",
            embedding_api_key="",
        )
        with pytest.raises(ValueError, match="EMBEDDING_API_KEY required"):
            create_embedding_provider(s)

    def test_openai_missing_key_raises(self):
        s = Settings(
            embedding_provider="openai",
            openai_api_key="",
            embedding_api_key="",
        )
        with pytest.raises(ValueError, match="OPENAI_API_KEY or EMBEDDING_API_KEY required"):
            create_embedding_provider(s)

    def test_unknown_provider_raises(self):
        s = Settings(embedding_provider="unknown")
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            create_embedding_provider(s)

    def test_foreign_model_auto_corrected_for_openai(self):
        s = Settings(
            embedding_provider="openai",
            embedding_model="gemini-embedding-001",
            embedding_dimensions=768,
            openai_api_key="test-key",
        )
        with patch("seamless_rag.providers.openai_provider.OpenAI"):
            provider = create_embedding_provider(s)
        assert provider.dimensions == 3072

    def test_foreign_model_auto_corrected_for_gemini(self):
        s = Settings(
            embedding_provider="gemini",
            embedding_model="text-embedding-3-large",
            embedding_dimensions=3072,
            embedding_api_key="test-key",
        )
        with patch("seamless_rag.providers.gemini.genai.Client"):
            provider = create_embedding_provider(s)
        assert provider.dimensions == 768


class TestIsForeignModel:
    """Test the _is_foreign_model helper."""

    def test_gemini_model_is_foreign_for_openai(self):
        assert _is_foreign_model("gemini-embedding-001", "openai")

    def test_openai_model_is_foreign_for_gemini(self):
        assert _is_foreign_model("text-embedding-3-large", "gemini")

    def test_native_model_not_foreign(self):
        assert not _is_foreign_model("gemini-embedding-001", "gemini")
        assert not _is_foreign_model("text-embedding-3-large", "openai")

    def test_local_model_is_foreign_for_both(self):
        assert _is_foreign_model("BAAI/bge-small-en-v1.5", "gemini")
        assert _is_foreign_model("BAAI/bge-small-en-v1.5", "openai")
