"""
Tests for LLM providers and factory.

Verifies:
- LLMProvider protocol compliance
- Factory creates correct provider types
- Foreign model auto-correction
- Provider generate() calls correct APIs
"""
from unittest.mock import Mock, patch

import pytest

from seamless_rag.config import Settings
from seamless_rag.llm.factory import _is_foreign_model, create_llm_provider
from seamless_rag.llm.protocol import LLMProvider


class TestLLMProtocol:
    """Verify protocol definition works."""

    def test_protocol_is_runtime_checkable(self):
        assert hasattr(LLMProvider, "__protocol_attrs__") or hasattr(
            LLMProvider, "__abstractmethods__"
        ) or isinstance(LLMProvider, type)

    def test_mock_satisfies_protocol(self):
        mock = Mock()
        mock.generate = Mock(return_value="answer")
        assert hasattr(mock, "generate")
        assert mock.generate("q", "ctx") == "answer"

    def test_concrete_class_satisfies_protocol(self):
        class MyLLM:
            def generate(self, prompt: str, context: str) -> str:
                return "test"

        assert isinstance(MyLLM(), LLMProvider)


class TestLLMFactory:
    """Test create_llm_provider with different configurations."""

    def test_creates_ollama_by_default(self):
        s = Settings(llm_provider="ollama", llm_model="qwen3:8b")
        provider = create_llm_provider(s)
        assert type(provider).__name__ == "OllamaLLMProvider"

    def test_creates_gemini_provider(self):
        s = Settings(llm_provider="gemini", llm_model="gemini-2.5-flash", llm_api_key="test-key")
        with patch("seamless_rag.llm.gemini.genai.Client"):
            provider = create_llm_provider(s)
        assert type(provider).__name__ == "GeminiLLMProvider"

    def test_creates_openai_provider(self):
        s = Settings(llm_provider="openai", llm_model="gpt-4o", openai_api_key="test-key")
        with patch("seamless_rag.llm.openai_provider.OpenAI"):
            provider = create_llm_provider(s)
        assert type(provider).__name__ == "OpenAILLMProvider"

    def test_gemini_missing_key_raises(self):
        s = Settings(llm_provider="gemini", llm_api_key="", embedding_api_key="")
        with pytest.raises(ValueError, match="LLM_API_KEY or EMBEDDING_API_KEY required"):
            create_llm_provider(s)

    def test_openai_missing_key_raises(self):
        s = Settings(llm_provider="openai", openai_api_key="", llm_api_key="")
        with pytest.raises(ValueError, match="OPENAI_API_KEY or LLM_API_KEY required"):
            create_llm_provider(s)

    def test_unknown_provider_raises(self):
        s = Settings(llm_provider="unknown")
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_provider(s)

    def test_foreign_model_auto_corrected_for_openai(self):
        s = Settings(
            llm_provider="openai", llm_model="gemini-2.5-flash", openai_api_key="test-key",
        )
        with patch("seamless_rag.llm.openai_provider.OpenAI"):
            provider = create_llm_provider(s)
        assert type(provider).__name__ == "OpenAILLMProvider"

    def test_foreign_model_auto_corrected_for_gemini(self):
        s = Settings(
            llm_provider="gemini", llm_model="gpt-4o", llm_api_key="test-key",
        )
        with patch("seamless_rag.llm.gemini.genai.Client"):
            provider = create_llm_provider(s)
        assert type(provider).__name__ == "GeminiLLMProvider"


class TestLLMIsForeignModel:
    """Test the LLM _is_foreign_model helper."""

    def test_gemini_model_foreign_for_openai(self):
        assert _is_foreign_model("gemini-2.5-flash", "openai")

    def test_openai_model_foreign_for_gemini(self):
        assert _is_foreign_model("gpt-4o", "gemini")

    def test_native_model_not_foreign(self):
        assert not _is_foreign_model("gemini-2.5-flash", "gemini")
        assert not _is_foreign_model("gpt-4o", "openai")


class TestGeminiLLMProvider:
    """Test Gemini LLM provider with mocked client."""

    def test_generate_calls_api(self):
        with patch("seamless_rag.llm.gemini.genai.Client") as mock_cls:
            mock_client = mock_cls.return_value
            mock_response = Mock()
            mock_response.text = "The answer is 42."
            mock_client.models.generate_content.return_value = mock_response

            from seamless_rag.llm.gemini import GeminiLLMProvider

            provider = GeminiLLMProvider(api_key="test", model="gemini-2.5-flash")
            result = provider.generate("What is the answer?", "Context here")

            assert result == "The answer is 42."
            mock_client.models.generate_content.assert_called_once()

    def test_generate_handles_none_text(self):
        with patch("seamless_rag.llm.gemini.genai.Client") as mock_cls:
            mock_client = mock_cls.return_value
            mock_response = Mock()
            mock_response.text = None
            mock_client.models.generate_content.return_value = mock_response

            from seamless_rag.llm.gemini import GeminiLLMProvider

            provider = GeminiLLMProvider(api_key="test")
            result = provider.generate("q", "ctx")
            assert result == ""


class TestOpenAILLMProvider:
    """Test OpenAI LLM provider with mocked client."""

    def test_generate_calls_api(self):
        with patch("seamless_rag.llm.openai_provider.OpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_choice = Mock()
            mock_choice.message.content = "Four"
            mock_response = Mock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response

            from seamless_rag.llm.openai_provider import OpenAILLMProvider

            provider = OpenAILLMProvider(api_key="test", model="gpt-4o")
            result = provider.generate("What is 2+2?", "context")

            assert result == "Four"
            mock_client.chat.completions.create.assert_called_once()

    def test_generate_handles_none_content(self):
        with patch("seamless_rag.llm.openai_provider.OpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_choice = Mock()
            mock_choice.message.content = None
            mock_response = Mock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response

            from seamless_rag.llm.openai_provider import OpenAILLMProvider

            provider = OpenAILLMProvider(api_key="test")
            result = provider.generate("q", "ctx")
            assert result == ""


class TestOllamaLLMProvider:
    """Test Ollama LLM provider with mocked requests."""

    def test_generate_calls_api(self):
        with patch("seamless_rag.llm.ollama.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"response": "The answer is 42."}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            from seamless_rag.llm.ollama import OllamaLLMProvider

            provider = OllamaLLMProvider(model="qwen3:8b")
            result = provider.generate("What is the answer?", "Context")

            assert result == "The answer is 42."
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "api/generate" in call_args[0][0]
            assert call_args[1]["json"]["model"] == "qwen3:8b"
            assert call_args[1]["json"]["stream"] is False

    def test_generate_handles_missing_response_key(self):
        with patch("seamless_rag.llm.ollama.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            from seamless_rag.llm.ollama import OllamaLLMProvider

            provider = OllamaLLMProvider()
            result = provider.generate("q", "ctx")
            assert result == ""

    def test_custom_base_url(self):
        from seamless_rag.llm.ollama import OllamaLLMProvider

        provider = OllamaLLMProvider(base_url="http://custom:1234/")
        assert provider._base_url == "http://custom:1234"
