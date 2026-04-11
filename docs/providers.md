# Providers

Seamless-RAG uses pluggable providers for both embedding and LLM operations. Switch providers via environment variables or `.env` file.

## Embedding Providers

### SentenceTransformers (default)

Local inference, no API key required. Uses `all-MiniLM-L6-v2` (384 dimensions).

```bash
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

Best for: quick start, offline use, CI/testing.

### Gemini

Google's embedding API via the `google-genai` SDK. Supports MRL dimension control.

```bash
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_API_KEY=your-gemini-api-key
EMBEDDING_DIMENSIONS=768
```

Best for: production quality, free tier available.

### OpenAI

OpenAI's embedding API. Highest dimensionality.

```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_API_KEY=your-openai-api-key
EMBEDDING_DIMENSIONS=3072
```

### Ollama

Local embedding via Ollama REST API. No API key needed.

```bash
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
LLM_BASE_URL=http://localhost:11434
EMBEDDING_DIMENSIONS=768
```

### Foreign Model Auto-Correction

When switching providers, model names are automatically corrected. If you switch from `gemini` to `sentence-transformers` but forget to change the model name, the factory detects the mismatch and uses the correct default.

## LLM Providers

### Ollama (default)

Local LLM via Ollama REST API. No API key required.

```bash
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:8b
LLM_BASE_URL=http://localhost:11434
```

### Gemini

```bash
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
LLM_API_KEY=your-gemini-api-key
```

### OpenAI

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_API_KEY=your-openai-api-key
```

## Custom Providers

Both layers use `typing.Protocol`. Implement the interface and it works without inheritance:

### Embedding Protocol

```python
class MyEmbeddingProvider:
    @property
    def dimensions(self) -> int:
        return 1024

    def embed(self, text: str) -> list[float]:
        return my_api.embed(text)

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        return [self.embed(t) for t in texts]
```

### LLM Protocol

```python
class MyLLMProvider:
    def generate(self, prompt: str, context: str) -> str:
        return my_api.generate(prompt=prompt, context=context)
```

Register your provider in the factory module or pass it directly to `SeamlessRAG`.

## Recommended Configurations

| Use Case | Embedding | LLM | Notes |
|----------|-----------|-----|-------|
| Quick start / offline | sentence-transformers | ollama | No API keys needed |
| Best quality | gemini | gemini | Free tier, strong models |
| Enterprise | openai | openai | Highest dimensions |
| Mixed | gemini (embed) | ollama (LLM) | Cloud embeddings, local inference |
