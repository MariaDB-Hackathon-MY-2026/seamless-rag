"""OpenAI LLM provider — uses openai SDK."""
from __future__ import annotations

from openai import OpenAI

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
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"},
            ],
        )
        return response.choices[0].message.content or ""
