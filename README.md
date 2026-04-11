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

Field names appear once in the header. Values are comma-separated without quotes (unless needed). More rows = more savings.

| Dataset Size | Token Savings |
|-------------|---------------|
| 3 rows      | ~34%          |
| 10 rows     | ~42%          |
| 100 rows    | ~52%          |

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

## Key Technical Decisions

- **TOON tabular header**: `[N,]{field1,field2}:` — comma in brackets signals tabular mode
- **Vector binary protocol**: `array.array('f', embedding)` for zero-copy insert
- **HNSW tuning**: `SET mhnsw_ef_search = 100` for demo-quality recall
- **CTE context window**: neighboring chunks via `JOIN ... BETWEEN` for better context
- **Observation layer**: token benchmark woven into every RAG query, not bolted on

## Project Structure

```
src/seamless_rag/
├── toon/
│   └── encoder.py           # TOON v3 encoder (full spec)
├── benchmark/
│   └── compare.py           # Token comparison (tiktoken)
├── providers/
│   ├── protocol.py          # EmbeddingProvider protocol
│   ├── sentence_transformers.py
│   ├── gemini.py            # Gemini via google-genai SDK
│   ├── openai_provider.py   # OpenAI via openai SDK
│   └── factory.py           # Auto-select from settings
├── llm/
│   ├── protocol.py          # LLMProvider protocol
│   ├── gemini.py            # Gemini LLM
│   ├── openai_provider.py   # OpenAI LLM
│   ├── ollama.py            # Ollama REST API
│   └── factory.py           # Auto-select from settings
├── storage/
│   └── mariadb.py           # VectorStore with HNSW
├── pipeline/
│   ├── embedder.py          # Auto-embed (batch + watch)
│   └── rag.py               # RAG engine + benchmark + LLM
├── core.py                  # SeamlessRAG facade
├── cli.py                   # Typer CLI
└── config.py                # Pydantic Settings
```

## License

Apache-2.0
