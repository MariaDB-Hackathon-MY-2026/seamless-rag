"""Ollama LLM provider — uses REST API (no SDK dependency)."""
from __future__ import annotations

import requests

_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question based on the provided context. "
    "The context is in TOON format (a compact tabular notation). "
    "If the context doesn't contain enough information, say so honestly."
)


class OllamaLLMProvider:
    """LLM provider using Ollama REST API.

    Default base URL: http://localhost:11434
    """

    def __init__(
        self,
        model: str = "qwen3:8b",
        base_url: str = "http://localhost:11434",
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")

    def generate(self, prompt: str, context: str) -> str:
        user_message = f"Context:\n{context}\n\nQuestion: {prompt}"
        response = requests.post(
            f"{self._base_url}/api/generate",
            json={
                "model": self._model,
                "system": _SYSTEM_PROMPT,
                "prompt": user_message,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "")
