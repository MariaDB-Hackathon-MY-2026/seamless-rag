![Seamless-RAG](docs/assets/logo.svg)

# Seamless-RAG

**Vector Search & Structured-Data RAG Toolkit for MariaDB**

> Turn any MariaDB table into a searchable vector store. Query results come back in TOON v3 tabular format — a compact wire format that saves 30-68% of tokens when feeding structured data to LLMs or agents.

![Powered by MariaDB](docs/assets/badge-mariadb.svg)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![TOON v3](https://img.shields.io/badge/TOON%20v3-166%2F166%20conformance-blue)]()
[![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-520%2F522%20passing-brightgreen)]()

---

## Why

LLMs and agents consume structured data as context. The standard approach — dumping JSON — wastes tokens on repeated field names and structural characters:

```json
[{"id":1,"name":"Widget","category":"Tools","price":29.99,"stock":150,"supplier":"Acme","rating":4.5},
 {"id":2,"name":"Gadget","category":"Tools","price":19.99,"stock":300,"supplier":"Acme","rating":4.2}]
```

TOON tabular writes field names once, values as compact rows:

```
[2,]{id,name,category,price,stock,supplier,rating}:
  1,Widget,Tools,29.99,150,Acme,4.5
  2,Gadget,Tools,19.99,300,Acme,4.2
```

**Where it matters most:**

| Scenario | Token savings | Why |
|----------|--------------|-----|
| DB query results (50 rows, 7 cols) | **55-65%** | Short values, many repeated field names |
| Agent multi-step context (20 steps) | **40-60% per step, compounding** | Structured state carried across steps |
| Metadata tables (booleans, IDs) | **60-68%** | Minimal content, maximum structure |
| Text-heavy RAG chunks | **10-25%** | Content dominates, structure overhead small |

TOON is not magic — it shines on **structured tabular data**, which is exactly what comes out of database queries.

## Quick Start

```bash
pip install -e ".[mariadb,embeddings]"    # or: pip install seamless-rag
docker compose up -d                       # MariaDB 11.8
seamless-rag init                          # create schema
seamless-rag ingest ./data/docs/           # chunk + embed files
seamless-rag ask "What are the key trends?" # vector search → TOON → LLM
```

## CLI Commands

```
seamless-rag init             Set up MariaDB schema (VECTOR columns + HNSW index)
seamless-rag ingest <path>    Chunk files at sentence boundaries, embed, store
seamless-rag embed            Bulk-embed existing table rows
seamless-rag watch            Auto-embed new inserts (Rich live display)
seamless-rag ask <question>   RAG query → answer + token/cost comparison
seamless-rag export <sql>     SELECT → TOON format
seamless-rag benchmark        Run JSON vs TOON token comparison
seamless-rag web              Launch Gradio web UI
seamless-rag demo             End-to-end demo with sample data
```

Global options: `--host`, `--port`, `--database`, `--provider`, `--model`, `--log-level`

## As Agent Tools

Seamless-RAG commands work as agent tools. An LLM agent can call these to interact with MariaDB:

```python
# Agent tool: search MariaDB and get compact context
result = rag.ask("quarterly revenue by region", top_k=10)
# result.context_toon → compact tabular format for next LLM call
# result.savings_pct → 55% fewer tokens than JSON

# Agent tool: export any SQL query as TOON
toon = rag.export("SELECT region, revenue, quarter FROM sales")
# Feed to next agent step with minimal token overhead
```

In a 20-step agent workflow querying a database at each step:
- **JSON context**: ~2000 tokens/step × 20 = 40,000 input tokens
- **TOON context**: ~850 tokens/step × 20 = 17,000 input tokens
- **Savings**: 23,000 tokens = faster inference + lower cost + more room in context window

## Python API

```python
from seamless_rag import SeamlessRAG

with SeamlessRAG(host="localhost", database="mydb") as rag:
    rag.init()
    rag.ingest("research.txt", ["chunk1...", "chunk2..."])
    rag.embed_table("articles", text_column="content")

    result = rag.ask("What are the main findings?")
    print(result.answer)           # LLM-generated answer
    print(result.context_toon)     # compact context
    print(f"Saved {result.savings_pct:.0f}% tokens")
```

## Pluggable Providers

Both embedding and LLM layers use `typing.Protocol` — no base class needed:

| Layer | Providers | Default |
|-------|-----------|---------|
| Embedding | SentenceTransformers, Gemini, OpenAI, Ollama | SentenceTransformers (local, free) |
| LLM | Ollama, Gemini, OpenAI | Ollama (local, free) |

Switch via env vars: `EMBEDDING_PROVIDER=gemini LLM_PROVIDER=openai seamless-rag ask "..."`

See [Providers guide](docs/providers.md) for adding custom providers.

## Architecture

```
seamless-rag CLI / Python API / Agent Tools
    │
    ├── EmbeddingProvider (Protocol)     ← 4 built-in, add your own
    ├── LLMProvider (Protocol)           ← 3 built-in, add your own
    ├── VectorStore (Protocol)           ← MariaDB with connection pool
    │     └── VECTOR(N) + HNSW index + VEC_DISTANCE_COSINE
    ├── AutoEmbedder                     ← batch + watch with Rich live
    ├── RAGEngine                        ← search → TOON → LLM → benchmark
    ├── TOONEncoder                      ← full v3 spec (166/166)
    └── TokenBenchmark                   ← tiktoken + GPT-4o cost calc
```

## Test Results

```
520/522 tests passing (99.6%)
  lint:        100%
  unit:        99.7% (329/330)
  spec:        100%  (166/166 TOON v3 conformance)
  integration: 100%  (17/17)
  eval:        100%
```

## Built for the MariaDB Ecosystem

<p align="center">
  <img src="docs/assets/mariadb-logo.svg" alt="MariaDB" width="200"/>
</p>

- **MariaDB 11.7+** VECTOR columns, HNSW indexes, VEC_DISTANCE_COSINE
- **Native binary protocol** via `mariadb-connector-python` (array.array float32)
- **Connection pooling** (pool_size=5) for production workloads
- **Version validation** (>= 11.7.2) on init

## License

```
Copyright 2026 LiuWei (SunflowersLwtech)
Licensed under the Apache License, Version 2.0
```

See [LICENSE](LICENSE) | [CONTRIBUTING](CONTRIBUTING.md) | [Documentation](https://sunflowerslwtech.github.io/seamless-rag/)
