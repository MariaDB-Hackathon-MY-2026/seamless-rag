# Seamless-RAG

**Vector Search & TOON Format for MariaDB**

Turn any MariaDB table into a searchable vector store. Query results come back in TOON v3 tabular format — a compact wire format that saves 20-40% of tokens when feeding structured data to LLMs or agents.

## Quick Start for Judges

Evaluating this submission? Start with the **[Judges' Testing Guide](judges-testing-guide.md)** — four progressive paths from inspect-only (5 min, no install) to full test suite (15 min).

90-second verification:

```bash
git clone https://github.com/MariaDB-Hackathon-MY-2026/seamless-rag.git
cd seamless-rag
docker compose up -d --wait
docker compose exec app seamless-rag demo
```

A 93-second screencast of the same flow:

![Seamless-RAG demo](assets/demo.gif)

---

## MariaDB Features We Use

This project is MariaDB-native end-to-end. The pipeline only works because of features that landed in MariaDB 11.7.2+ and is explicitly tuned for them — no external vector store, no shadow index, no application-side ANN.

| Feature | What we use it for | Source |
|---|---|---|
| **`VECTOR(N)` column type** | First-class storage for float32 embeddings, no `BLOB` workaround | `src/seamless_rag/storage/mariadb.py` (schema, auto-add column) |
| **`VECTOR INDEX … DISTANCE=cosine`** (HNSW) | Sub-linear similarity search; we tune `mhnsw_ef_search = 100` per session for recall/latency | same file |
| **`VEC_DISTANCE_COSINE`** | Distance function in `ORDER BY` so the planner picks the HNSW index | same file |
| **Native binary protocol** via `mariadb-connector-python` | `array.array('f', embedding)` sent verbatim — no `VEC_FromText` round-trip, no string parsing | same file |
| **CTE for context windowing** | Single round-trip retrieval: closest chunks plus their neighbours by `chunk_order` | `WITH closest AS …` |
| **Hybrid SQL filter + vector ORDER BY** | `seamless-rag ask "..." --where "price < 50"` — SQL pre-filter narrows candidates, vector ranks within | validated WHERE clause |
| **Connection pool + autocommit** | `mariadb.ConnectionPool` with per-call lease so the watcher never sees stale snapshots | same file |
| **Foreign keys + composite index** | `chunks.document_id REFERENCES documents(id)` plus `INDEX idx_doc_order(document_id, chunk_order)` keeps the CTE neighbour-join index-only | same file |
| **Auto-schema for arbitrary tables** | `seamless-rag embed --table products --columns name,category` adds a `VECTOR(N)` column and HNSW index to your existing table without touching its other columns | same file |
| **Bare `VEC_DISTANCE()` auto-pick** (MariaDB-only) | When the index has `DISTANCE=cosine`, plain `VEC_DISTANCE(...)` reads it from the index and applies cosine — no other RDBMS does this. Demonstrated live by `seamless-rag schema` | `compare_vec_distance` + integration test asserting 1e-6 equivalence |

**See it for yourself:** `seamless-rag schema` pretty-prints `SHOW CREATE TABLE chunks`, `SHOW INDEX FROM chunks`, and runs a side-by-side `VEC_DISTANCE()` vs `VEC_DISTANCE_COSINE()` query so you can verify the auto-pick parity yourself.

**Tested against MariaDB 11.8** (the version shipped in the official `mariadb:11.8` Docker image). 11/11 integration tests pass against the real server, exercising every feature above. Without MariaDB's VECTOR + HNSW, this project would need a sidecar vector DB (Chroma/Qdrant/pgvector) — neither MariaDB-native, neither benefiting from the same indexes that already serve OLTP traffic.

---

## Features

- **Auto-Embed** — Point at any MariaDB table, embed single or multiple columns
- **Watch Mode** — Polls for new inserts and auto-embeds them in real time
- **RAG Query** — Vector search → TOON context → LLM answer in one call
- **Hybrid Search** — Combine SQL filters (`WHERE price < 50`) with vector similarity
- **MMR Diversity** — Maximal Marginal Relevance for diverse result sets
- **Token Savings** — Every query reports JSON vs TOON token comparison
- **Model-Agnostic** — Swap embedding/LLM providers via environment variables
- **Web UI** — Gradio interface with 6 tabs for interactive exploration

## Quick Example

```python
from seamless_rag import SeamlessRAG

with SeamlessRAG(host="localhost", database="mydb") as rag:
    # Embed multiple columns for richer semantics
    rag.embed_table("products", text_column=["name", "category", "price"])

    # Hybrid search: semantic + SQL filter
    result = rag.ask("affordable tools", where="price < 50", mmr=True)
    print(result.answer)
    print(result.context_toon)
    print(f"Tokens saved: {result.savings_pct:.1f}%")
```

## Real-World Token Savings

Measured on MovieLens (9,742 movies) and SF Restaurant Health Scores (53,973 inspections):

| Dataset | Rows | JSON Tokens | TOON Tokens | Savings |
|---------|------|-------------|-------------|---------|
| MovieLens (7 cols) | 100 | 6,540 | 5,019 | **23.3%** |
| MovieLens metadata (4 cols) | 100 | 2,258 | 1,364 | **39.6%** |
| Restaurant violations (9 cols) | 100 | 7,071 | 4,326 | **38.8%** |

See [Benchmark Results](BENCHMARK_REAL_DATA.md) for the full analysis.

## Next Steps

- [Getting Started](getting-started.md) — Install and run your first query in 5 minutes
- [Architecture](ARCHITECTURE.md) — Understand the pipeline
- [API Reference](api-reference.md) — Full Python API
- [Providers](providers.md) — Configure embedding and LLM providers
- [TOON Format](toon-format.md) — Understand the format specification
- [Benchmark](BENCHMARK_REAL_DATA.md) — Real-world token savings data
