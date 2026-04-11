# Seamless-RAG

**TOON-Native Auto-Embedding & RAG Toolkit for MariaDB**

> Automatically embed your MariaDB tables and query them with RAG — results formatted in TOON v3 for 30-58% token savings over JSON.

[![Tests](https://img.shields.io/badge/tests-489%2F491%20passing-brightgreen)]()
[![TOON Spec](https://img.shields.io/badge/TOON%20v3-166%2F166%20conformance-blue)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()

## What It Does

1. **Auto-Embed**: Point it at any MariaDB table → it embeds text columns (local or cloud models)
2. **Watch Mode**: Polls for new inserts and auto-embeds them in real-time
3. **RAG Query**: Ask questions → vector search → TOON-formatted context → LLM answer
4. **Token Savings**: Every query reports JSON vs TOON token comparison — live proof of savings
5. **Model-Agnostic**: Swap embedding/LLM providers (SentenceTransformers, Gemini, OpenAI, Ollama) via config

## Architecture

```
SeamlessRAG (facade)
├── EmbeddingProvider (Protocol)     ← pluggable
│   ├── SentenceTransformersProvider ← local, free (384d)
│   ├── GeminiEmbeddingProvider      ← google-genai SDK (768d)
│   └── OpenAIEmbeddingProvider      ← openai SDK (3072d)
├── LLMProvider (Protocol)           ← pluggable
│   ├── OllamaLLMProvider            ← local REST (default)
│   ├── GeminiLLMProvider            ← gemini-2.5-flash
│   └── OpenAILLMProvider            ← gpt-4o
├── MariaDBVectorStore               ← VECTOR + HNSW cosine search
├── AutoEmbedder                     ← watch + batch with retry
├── RAGEngine                        ← search → TOON → LLM → benchmark
├── TOONEncoder                      ← full v3 spec (166/166)
└── TokenBenchmark                   ← tiktoken cl100k_base
```

## Quick Start

### Prerequisites
- Python 3.12+
- MariaDB 11.7+ (with VECTOR support)
- Docker (for MariaDB)

### Install

```bash
# Clone and setup
git clone <repo-url> && cd seamless-rag
conda create -n seamless-rag python=3.12 -y
conda activate seamless-rag
pip install -e ".[dev,mariadb,embeddings]"

# Start MariaDB
docker compose up -d
```

### Usage

```bash
# Initialize database schema
seamless-rag init

# Ingest text files (auto-chunks and embeds)
seamless-rag ingest ./data/articles/

# Watch for new rows and auto-embed
seamless-rag watch --table articles --column content --interval 2

# Ask a question (with token benchmark + LLM answer)
seamless-rag ask "What are the key findings on climate change?"

# Export SQL results as TOON
seamless-rag export "SELECT id, title, content FROM articles LIMIT 10"

# Run the full end-to-end demo
seamless-rag demo
```

### Python API

```python
from seamless_rag import SeamlessRAG

rag = SeamlessRAG(host="localhost", database="mydb", password="secret")

# Embed all rows
rag.embed_table("articles", text_column="content")

# RAG query with automatic token benchmarking
result = rag.ask("What are the main topics?")
print(result.context_toon)      # TOON-formatted context
print(f"Tokens saved: {result.savings_pct:.1f}%")
print(f"JSON: {result.json_tokens} → TOON: {result.toon_tokens}")
```

## TOON Format — Why It Matters

TOON v3 tabular format eliminates key repetition in structured data:

**JSON (56 tokens):**
```json
[{"id": 1, "content": "Climate change affects biodiversity", "distance": 0.12},
 {"id": 2, "content": "Recent studies show temperature rise", "distance": 0.18}]
```

**TOON (37 tokens, 34% savings):**
```
[2,]{id,content,distance}:
  1,Climate change affects biodiversity,0.12
  2,Recent studies show temperature rise,0.18
```

Field names appear once in the header. More rows = more savings:

| Queries/day | JSON tokens (GPT-4o) | TOON tokens | Monthly cost @ $2.50/1M | Monthly savings |
|-------------|---------------------|-------------|-------------------------|-----------------|
| 100         | 5,600               | 3,700       | $0.42 → $0.28          | $0.14 (34%)     |
| 1,000       | 56,000              | 36,960      | $4.20 → $2.77          | $1.43 (34%)     |
| 10,000      | 560,000             | 324,800     | $42.00 → $24.36        | $17.64 (42%)    |
| 100,000     | 5,600,000           | 2,688,000   | $420 → $202            | $218 (52%)      |

## Pluggable Provider Architecture

Both embedding and LLM layers use `typing.Protocol` — implement the interface, and it works:

```python
from seamless_rag.providers.protocol import EmbeddingProvider

class CohereProvider:  # no base class needed
    @property
    def dimensions(self) -> int:
        return 1024

    def embed(self, text: str) -> list[float]:
        return cohere.Client(API_KEY).embed(texts=[text]).embeddings[0]

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        return cohere.Client(API_KEY).embed(texts=texts).embeddings
```

LLM providers are even simpler — one method:

```python
from seamless_rag.llm.protocol import LLMProvider

class AnthropicLLM:
    def generate(self, prompt: str, context: str) -> str:
        return anthropic.Anthropic().messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1024,
            messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"}],
        ).content[0].text
```

Register in the factory or pass via `Settings(embedding_provider="cohere")`, then configure in `.env`.

## Test Results

```
Overall: 99.6% (489/491 passed)
  lint:        100%  ✓
  unit:        99.7% (298/299) — includes provider + LLM factory tests
  spec:        100%  (166/166) — full TOON v3 conformance
  props:       91.7% (11/12) — hypothesis property tests
  integration: 100%  (17/17) — MariaDB + API providers
  eval:        100%  ✓
```

Run tests:
```bash
make test-all         # lint + unit + spec (no Docker)
make test-full        # all suites including integration
make score            # quality score dashboard
```

## Project Structure

```
src/seamless_rag/
├── toon/encoder.py          # TOON v3 encoder (166/166 spec)
├── benchmark/compare.py     # Token comparison (tiktoken)
├── providers/               # EmbeddingProvider: ST, Gemini, OpenAI + factory
├── llm/                     # LLMProvider: Ollama, Gemini, OpenAI + factory
├── storage/mariadb.py       # VectorStore with HNSW cosine search
├── pipeline/embedder.py     # Auto-embed (batch + watch)
├── pipeline/rag.py          # RAG engine + benchmark + LLM
├── core.py                  # SeamlessRAG facade
├── cli.py                   # Typer CLI
└── config.py                # Pydantic Settings
```

## License

Apache-2.0
