"""Gemini LLM provider — uses google-genai SDK."""
from __future__ import annotations

import logging

from google import genai

from seamless_rag.llm import RAG_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def _is_vertex_key(api_key: str) -> bool:
    """Vertex AI Express Mode keys start with 'AQ.'; AI Studio keys start with 'AIza'."""
    return api_key.startswith("AQ.")


class GeminiLLMProvider:
    """LLM provider using Gemini models via google-genai SDK.

    Auto-detects Vertex AI keys (AQ. prefix) vs AI Studio keys (AIza prefix).
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        client_kwargs = {"api_key": api_key}
        if _is_vertex_key(api_key):
            client_kwargs["vertexai"] = True
        self._client = genai.Client(**client_kwargs)
        self._model = model

    def generate(self, prompt: str, context: str) -> str:
        user_message = f"Context:\n{context}\n\nQuestion: {prompt}"
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=user_message,
                config={"system_instruction": RAG_SYSTEM_PROMPT},
            )
        except Exception as e:
            logger.error("Gemini generate_content failed: %s", e)
            raise RuntimeError(f"Gemini LLM call failed: {e}") from e
        if not response.text:
            logger.warning("Gemini returned empty response for prompt: %s", prompt[:100])
            return ""
        return response.text
