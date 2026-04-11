"""Ollama embedding provider — uses REST API (no SDK dependency)."""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider:
    """Embedding provider using Ollama REST API.

    Default model: nomic-embed-text (768 dimensions).
    Uses /api/embed endpoint which returns L2-normalized vectors.
    """

    def __init__(
        self,
        model: str = "nomic-embed-text",
        dimensions: int = 768,
        base_url: str = "http://localhost:11434",
    ) -> None:
        self._model = model
        self._dimensions = dimensions
        self._base_url = base_url.rstrip("/")

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def _request(self, inputs: list[str]) -> list[list[float]]:
        """Send embedding request to Ollama /api/embed endpoint."""
        payload = json.dumps({"model": self._model, "input": inputs}).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/api/embed",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama embed request failed: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Ollama returned invalid JSON: {e}") from e

        embeddings = body.get("embeddings", [])
        if len(embeddings) != len(inputs):
            raise RuntimeError(
                f"Ollama returned {len(embeddings)} embeddings for {len(inputs)} inputs"
            )
        return [list(e) for e in embeddings]

    def embed(self, text: str) -> list[float]:
        results = self._request([text])
        return results[0]

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        if not texts:
            return []
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            all_embeddings.extend(self._request(chunk))
        return all_embeddings
