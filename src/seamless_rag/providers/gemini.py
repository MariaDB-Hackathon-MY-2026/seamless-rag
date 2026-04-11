"""Gemini embedding provider — uses google-genai SDK."""
from __future__ import annotations

from google import genai
from google.genai import types


class GeminiEmbeddingProvider:
    """Embedding provider using Gemini models via google-genai SDK.

    Default model: gemini-embedding-001 (3072 dims, configurable via MRL).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-001",
        dimensions: int = 768,
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._dimensions = dimensions
        self._config = types.EmbedContentConfig(output_dimensionality=dimensions)

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, text: str) -> list[float]:
        result = self._client.models.embed_content(
            model=self._model,
            contents=text,
            config=self._config,
        )
        if not result.embeddings:
            raise RuntimeError("Gemini returned empty embeddings response")
        vec = list(result.embeddings[0].values)
        if len(vec) != self._dimensions:
            raise RuntimeError(
                f"Gemini returned {len(vec)} dims, expected {self._dimensions}"
            )
        return vec

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        if not texts:
            return []
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            result = self._client.models.embed_content(
                model=self._model,
                contents=chunk,
                config=self._config,
            )
            if len(result.embeddings) != len(chunk):
                raise RuntimeError(
                    f"Gemini returned {len(result.embeddings)} embeddings "
                    f"for {len(chunk)} inputs"
                )
            for emb in result.embeddings:
                vec = list(emb.values)
                if len(vec) != self._dimensions:
                    raise RuntimeError(
                        f"Gemini returned {len(vec)} dims, expected {self._dimensions}"
                    )
                all_embeddings.append(vec)
        return all_embeddings
