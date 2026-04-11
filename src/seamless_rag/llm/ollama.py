"""Ollama LLM provider — uses REST API (no SDK dependency)."""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question based on the provided context. "
    "The context is in TOON format (a compact tabular notation). "
    "If the context doesn't contain enough information, say so honestly."
)


class OllamaLLMProvider:
    """LLM provider using Ollama REST API.

    Default base URL: http://localhost:11434
    Uses urllib instead of requests to avoid an extra dependency.
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
        payload = json.dumps({
            "model": self._model,
            "system": _SYSTEM_PROMPT,
            "prompt": user_message,
            "stream": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self._base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            logger.error("Ollama request failed: %s", e)
            raise RuntimeError(f"Ollama LLM call failed: {e}") from e
        except json.JSONDecodeError as e:
            logger.error("Ollama returned invalid JSON: %s", e)
            raise RuntimeError(f"Ollama returned invalid JSON: {e}") from e

        answer = body.get("response", "")
        if not answer:
            logger.warning("Ollama returned empty response for prompt: %s", prompt[:100])
        return answer
