"""OpenAI LLM provider — uses openai SDK."""
from __future__ import annotations

import logging

from openai import OpenAI

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question based on the provided context. "
    "The context is in TOON format (a compact tabular notation). "
    "If the context doesn't contain enough information, say so honestly."
)


class OpenAILLMProvider:
    """LLM provider using OpenAI models via openai SDK."""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(self, prompt: str, context: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"},
                ],
            )
        except Exception as e:
            logger.error("OpenAI chat.completions.create failed: %s", e)
            raise RuntimeError(f"OpenAI LLM call failed: {e}") from e
        if not response.choices:
            logger.warning("OpenAI returned no choices for prompt: %s", prompt[:100])
            return ""
        content = response.choices[0].message.content
        if content is None:
            logger.warning("OpenAI returned null content for prompt: %s", prompt[:100])
            return ""
        return content
