"""OpenAI embedding provider — uses openai SDK."""
from __future__ import annotations

from openai import OpenAI


class OpenAIEmbeddingProvider:
    """Embedding provider using OpenAI models via openai SDK.

    Default model: text-embedding-3-large (3072 dimensions).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-large",
        dimensions: int = 3072,
    ) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, text: str) -> list[float]:
        response = self._client.embeddings.create(
            model=self._model,
            input=text,
            dimensions=self._dimensions,
        )
        return list(response.data[0].embedding)

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        if not texts:
            return []
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            response = self._client.embeddings.create(
                model=self._model,
                input=chunk,
                dimensions=self._dimensions,
            )
            for item in response.data:
                all_embeddings.append(list(item.embedding))
        return all_embeddings
