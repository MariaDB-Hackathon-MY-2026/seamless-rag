"""Gemini LLM provider — uses google-genai SDK."""
from __future__ import annotations

import logging

from google import genai

from seamless_rag.llm import RAG_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class GeminiLLMProvider:
    """LLM provider using Gemini models via google-genai SDK."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._client = genai.Client(api_key=api_key)
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
