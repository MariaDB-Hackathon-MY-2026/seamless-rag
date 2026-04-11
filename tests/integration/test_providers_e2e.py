"""
Integration tests for embedding and LLM providers with real API keys.

These tests are marked @pytest.mark.slow and require:
- EMBEDDING_API_KEY (Google) in .env
- OPENAI_API_KEY in .env

Run with: pytest tests/integration/test_providers_e2e.py -v -m slow
"""

import pytest

from seamless_rag.config import Settings


def _has_google_key() -> bool:
    try:
        s = Settings()
        return bool(s.embedding_api_key)
    except Exception:
        return False


def _has_openai_key() -> bool:
    try:
        s = Settings()
        return bool(s.openai_api_key)
    except Exception:
        return False


@pytest.mark.slow
@pytest.mark.skipif(not _has_google_key(), reason="EMBEDDING_API_KEY not set")
class TestGeminiEmbeddingE2E:
    """End-to-end tests for Gemini embedding provider."""

    def test_embed_returns_correct_dimensions(self):
        from seamless_rag.providers.gemini import GeminiEmbeddingProvider

        s = Settings()
        provider = GeminiEmbeddingProvider(
            api_key=s.embedding_api_key,
            model="gemini-embedding-001",
            dimensions=768,
        )
        vec = provider.embed("hello world")
        assert len(vec) == 768
        assert all(isinstance(v, float) for v in vec)

    def test_embed_batch(self):
        from seamless_rag.providers.gemini import GeminiEmbeddingProvider

        s = Settings()
        provider = GeminiEmbeddingProvider(
            api_key=s.embedding_api_key,
            model="gemini-embedding-001",
            dimensions=768,
        )
        vecs = provider.embed_batch(["hello", "world", "test"])
        assert len(vecs) == 3
        assert all(len(v) == 768 for v in vecs)

    def test_different_texts_different_embeddings(self):
        from seamless_rag.providers.gemini import GeminiEmbeddingProvider

        s = Settings()
        provider = GeminiEmbeddingProvider(
            api_key=s.embedding_api_key,
            model="gemini-embedding-001",
            dimensions=768,
        )
        v1 = provider.embed("The cat sat on the mat")
        v2 = provider.embed("Quantum physics explains the universe")
        assert v1 != v2


@pytest.mark.slow
@pytest.mark.skipif(not _has_google_key(), reason="EMBEDDING_API_KEY not set")
class TestGeminiLLME2E:
    """End-to-end tests for Gemini LLM provider."""

    def test_generate_returns_string(self):
        from seamless_rag.llm.gemini import GeminiLLMProvider

        s = Settings()
        api_key = s.llm_api_key or s.embedding_api_key
        provider = GeminiLLMProvider(api_key=api_key, model="gemini-2.5-flash")
        answer = provider.generate("What is 2+2?", "The answer is 4.")
        assert isinstance(answer, str)
        assert len(answer) > 0


@pytest.mark.slow
@pytest.mark.skipif(not _has_openai_key(), reason="OPENAI_API_KEY not set")
class TestOpenAIEmbeddingE2E:
    """End-to-end tests for OpenAI embedding provider."""

    def test_embed_returns_correct_dimensions(self):
        from seamless_rag.providers.openai_provider import OpenAIEmbeddingProvider

        s = Settings()
        provider = OpenAIEmbeddingProvider(
            api_key=s.openai_api_key,
            model="text-embedding-3-large",
            dimensions=3072,
        )
        vec = provider.embed("hello world")
        assert len(vec) == 3072
        assert all(isinstance(v, float) for v in vec)

    def test_embed_batch(self):
        from seamless_rag.providers.openai_provider import OpenAIEmbeddingProvider

        s = Settings()
        provider = OpenAIEmbeddingProvider(
            api_key=s.openai_api_key,
            model="text-embedding-3-large",
            dimensions=3072,
        )
        vecs = provider.embed_batch(["hello", "world"])
        assert len(vecs) == 2
        assert all(len(v) == 3072 for v in vecs)


@pytest.mark.slow
@pytest.mark.skipif(not _has_openai_key(), reason="OPENAI_API_KEY not set")
class TestOpenAILLME2E:
    """End-to-end tests for OpenAI LLM provider."""

    def test_generate_returns_string(self):
        from seamless_rag.llm.openai_provider import OpenAILLMProvider

        s = Settings()
        provider = OpenAILLMProvider(api_key=s.openai_api_key, model="gpt-4o")
        answer = provider.generate("What is 2+2?", "The answer is 4.")
        assert isinstance(answer, str)
        assert len(answer) > 0
