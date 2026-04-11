# Providers

Seamless-RAG uses pluggable providers for both embedding and LLM operations.

## Embedding Providers

### SentenceTransformers (default)

Local inference, no API key required. Uses `all-MiniLM-L6-v2` (384 dimensions).

```bash
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Gemini

Google's embedding API via the `google-genai` SDK.

```bash
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=models/text-embedding-004
EMBEDDING_API_KEY=your-gemini-api-key
EMBEDDING_DIMENSIONS=768
```

### OpenAI

OpenAI's embedding API.

```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_API_KEY=your-openai-api-key
EMBEDDING_DIMENSIONS=3072
```

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

### Embedding

```python
class MyEmbeddingProvider:
    @property
    def dimensions(self) -> int:
        return 1024

    def embed(self, text: str) -> list[float]:
        return my_api.embed(text)

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        return my_api.embed_batch(texts)
```

### LLM

```python
class MyLLMProvider:
    def generate(self, prompt: str, context: str) -> str:
        return my_api.generate(prompt=prompt, context=context)
```

Register your provider in the factory module or pass it directly to `SeamlessRAG`.
