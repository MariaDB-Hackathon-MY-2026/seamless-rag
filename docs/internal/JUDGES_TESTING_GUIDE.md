# Judges Testing Guide — Seamless-RAG

## Tier 1: Quick Verification (2 minutes)

```bash
# Clone and setup
git clone <repo-url> && cd seamless-rag
conda create -n seamless-rag python=3.12 -y && conda activate seamless-rag
pip install -e ".[dev,embeddings]"

# Run core tests (no Docker needed)
make test-all
# Expected: 430+ tests passing, 100% spec conformance
```

## Tier 2: Full Test Suite (5 minutes)

```bash
# Start MariaDB
docker compose -f docker-compose.test.yml up -d --wait

# Install MariaDB connector
pip install mariadb

# Run everything
make test-full
# Expected: 440+ tests passing, 100% integration

# Quality dashboard
make score
```

## Tier 3: Live Demo (5 minutes)

```bash
# Start MariaDB with demo data
docker compose up -d --wait

# Bulk-embed a table
seamless-rag embed --table articles --column content
# → Shows: "Embedded: N, Failed: 0, Total: N"

# Ask a question with token benchmark
seamless-rag ask "What are the key findings on climate change?"
# → Shows: TOON context, token comparison table (JSON vs TOON)

# Watch mode (Ctrl+C to stop)
seamless-rag watch articles --column content --interval 2
# → Auto-embeds new inserts in real-time

# Export SQL as TOON
seamless-rag export "SELECT id, title, content FROM articles LIMIT 5"
# → TOON tabular output with 30%+ character savings
```

## Tier 4: Python API (5 minutes)

```python
from seamless_rag import SeamlessRAG

rag = SeamlessRAG(host="localhost", database="seamless_rag", password="seamless")

# Embed table
result = rag.embed_table("articles", text_column="content")
print(f"Embedded: {result['embedded']}, Failed: {result['failed']}")

# RAG query with automatic benchmarking
result = rag.ask("What are the main topics?")
print(f"Context (TOON):\n{result.context_toon}")
print(f"JSON tokens: {result.json_tokens}")
print(f"TOON tokens: {result.toon_tokens}")
print(f"Savings: {result.savings_pct:.1f}%")

# Direct TOON encoding
from seamless_rag.toon import encode_tabular
data = [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]
print(encode_tabular(data))
# → [2,]{id,name}:
#     1,Ada
#     2,Bob

rag.close()
```

## Tier 5: Multi-Provider Testing (5 minutes)

Seamless-RAG supports pluggable embedding and LLM providers. To test with cloud providers, set env vars before running:

```bash
# Gemini (embedding + LLM)
export EMBEDDING_PROVIDER=gemini
export EMBEDDING_API_KEY=<your-gemini-key>
export LLM_PROVIDER=gemini
seamless-rag demo

# OpenAI (embedding + LLM)
export EMBEDDING_PROVIDER=openai
export OPENAI_API_KEY=<your-openai-key>
export LLM_PROVIDER=openai
seamless-rag demo

# Mix and match: Gemini embeddings + OpenAI LLM
export EMBEDDING_PROVIDER=gemini
export EMBEDDING_API_KEY=<your-gemini-key>
export LLM_PROVIDER=openai
export OPENAI_API_KEY=<your-openai-key>
seamless-rag ask "What are the key findings?"
```

The factory auto-selects model names and dimensions per provider. Foreign model names (e.g. a Gemini model with the OpenAI provider) are auto-corrected.

Without any env vars, the default path uses SentenceTransformers (local, free) + Ollama (local) — no API keys needed.

## What to Look For

1. **TOON Spec Conformance**: `make test-spec` → 166/166 official fixtures
2. **Token Savings**: Every `ask()` call reports JSON vs TOON savings (30%+)
3. **Watch Mode**: Auto-embeds new inserts with retry and error isolation
4. **Vector Search**: HNSW cosine search with CTE context windowing
5. **Clean Architecture**: Protocol-based providers, facade pattern, zero coupling
6. **Multi-Provider**: Swap embedding/LLM providers via env vars, no code changes
