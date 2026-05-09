---
name: seamless-rag
description: "Use Seamless-RAG (the MariaDB-native vector + RAG toolkit) to embed table rows, run vector search with VEC_DISTANCE_COSINE/HNSW, and return query results in TOON tabular format that costs 10–55% fewer LLM tokens than JSON. Trigger this skill whenever the user is working with the seamless-rag CLI or Python package, mentions MariaDB VECTOR columns, asks to embed/index/search rows in MariaDB, wants to convert SQL output into a token-efficient context for an LLM, asks about TOON v3 format, or sets up auto-embedding/watch-mode against a MariaDB table — even if they don't say 'seamless-rag' by name. Also use when the user pairs this with the text-to-sql skill for hybrid (precise filter + semantic) queries."
---

# Seamless-RAG Skill

Seamless-RAG is a **thin bridging layer** between MariaDB and LLMs/agents. It does NOT replace SQL — it complements it with vector search for semantic queries, and provides TOON format for token-efficient data consumption.

```
Agent (intent, strategy, judgment)
  ↕ CLI / Python API
Seamless-RAG (embed rows, vector search, format as TOON)
  ↕ mariadb-connector-python
MariaDB 11.7+ (store, index, execute SQL + VEC_DISTANCE)
```

**Companion skill**: when the user asks a question that maps to a precise SQL query (numbers, aggregations, JOINs, exact filters), route to the **text-to-sql** skill instead, then optionally feed its TOON output back through this skill for further semantic work.

## Setup (run once if seamless-rag is not already installed)

```bash
pip install "seamless-rag[mariadb,embeddings]"
```

The `mariadb` extra needs the MariaDB Connector/C system library. If pip fails to build it:

- **macOS**: `brew install mariadb-connector-c`
- **Debian/Ubuntu**: `sudo apt install libmariadb-dev`
- **RHEL/Fedora**: `sudo dnf install mariadb-connector-c-devel`

Then point at a MariaDB **11.7.2 or newer** instance — the VECTOR type and HNSW indexes only exist from that version onward. The fastest way is `docker run -d -p 3306:3306 -e MARIADB_ROOT_PASSWORD=seamless mariadb:11.8`.

## When to Use What

- **Precise query** ("Q3 revenue > 1M", aggregations, JOINs): hand off to the **text-to-sql** skill → it generates SQL → `seamless-rag export "..."` → TOON.
- **Semantic query** ("find similar products"): `seamless-rag ask "..."` for vector search.
- **Hybrid** ("waterproof watches under $50"): `seamless-rag ask "..." --where "price < 50"` — SQL pre-filter + vector ranking in one MariaDB query.
- **Any SQL result fed to an LLM**: always use `seamless-rag export "..."` first to convert to TOON.

> **Routing rule**: if the user's question involves numbers, aggregations, GROUP BY, or exact filters → route to `text-to-sql`. If it's fuzzy/semantic → use `ask`. If both → use `ask --where`.

## Reading TOON Format

When you receive TOON output from seamless-rag tools, read it like this:

```
[N,]{col1,col2,col3}:     ← header: N rows, column names in order
  val1,val2,val3           ← row 1: values match column positions
  val4,val5,val6           ← row 2
```

**Example — this TOON:**
```
[3,]{id,name,price,in_stock}:
  1,Widget,29.99,true
  2,"Smith, John",19.99,false
  3,Gizmo,null,true
```

**Means the same as this JSON:**
```json
[{"id":1,"name":"Widget","price":29.99,"in_stock":true},
 {"id":2,"name":"Smith, John","price":19.99,"in_stock":false},
 {"id":3,"name":"Gizmo","price":null,"in_stock":true}]
```

**TOON rules:**
- Header `[N,]{...}:` tells you row count and column names.
- Each indented line is one row, values in column order.
- `null` = no value, `true`/`false` = booleans.
- Quoted values (`"Smith, John"`) contain commas or special characters.
- Unquoted values are plain text, numbers, or booleans.
- Numbers are canonical: no scientific notation, no trailing zeros.

**Why TOON over JSON**: 10–55% fewer tokens vs compact JSON for structured data. Field names appear once in the header instead of repeating per row. Savings are highest with many rows and short values.

## CLI Commands

Global options: `--host`, `--port`, `--user`, `--password`, `--database`, `--provider`, `--model`, `--log-level`.
Defaults come from environment (`MARIADB_HOST`, `MARIADB_PORT`, `MARIADB_USER`, `MARIADB_PASSWORD`, `MARIADB_DATABASE`) or a local `.env` file — pass flags only when you need to override them for a single command.

```bash
# Core: data already in MariaDB → add vectors
seamless-rag init                                            # VECTOR columns + HNSW index
seamless-rag embed --table chunks --column content           # Bulk-embed single column
seamless-rag embed --table products --columns "name,category,price"  # Multi-column
seamless-rag watch --table chunks --columns "name,desc"      # Auto-embed new inserts

# Query
seamless-rag ask "question" --top-k 5 --where "price<50" --mmr --context-window 1
seamless-rag export "SELECT ... FROM ..."                    # Any SQL → TOON format

# Tools
seamless-rag schema                                          # Show VECTOR/HNSW/VEC_DISTANCE config
seamless-rag benchmark --rows 50 --cols 6                    # JSON vs TOON comparison
seamless-rag web --port 7860                                 # Gradio web UI (localhost-only by default)
seamless-rag demo                                            # End-to-end demo
seamless-rag ingest <path> --chunk-size 500 --overlap 50     # Load text files for testing
```

## Python API

```python
from seamless_rag import SeamlessRAG

with SeamlessRAG(host="127.0.0.1", database="seamless_rag") as rag:
    rag.init()                                        # create schema (idempotent)

    # Single-column embed (default)
    rag.embed_table("articles", text_column="content")

    # Multi-column embed — richer semantics
    rag.embed_table("products", text_column=["name", "category", "price"])
    # Internally: "Widget — Tools — 29.99" → searches match name AND price

    # Semantic search with hybrid filter
    result = rag.ask("waterproof watches", top_k=5, where="price < 500", mmr=True)
    # result.answer           : str        — LLM answer
    # result.context_toon     : str        — TOON context (feed to next LLM call)
    # result.savings_pct      : float      — token savings vs compact JSON
    # result.sources          : list[dict] — raw rows

    # SQL → TOON (for precise queries / agent tools)
    toon = rag.export("SELECT region, SUM(revenue) FROM sales GROUP BY region")
```

## TOON Encoder (standalone — no MariaDB needed)

If a user only wants TOON without the MariaDB pieces, the encoder is a pure-Python module and works without the `[mariadb]` extra:

```python
from seamless_rag.toon.encoder import encode_tabular

toon = encode_tabular([
    {"id": 1, "name": "Alice", "score": 95},
    {"id": 2, "name": "Bob",   "score": 87},
])
# → [2,]{id,name,score}:
#     1,Alice,95
#     2,Bob,87
```

## Provider Configuration

| Variable | Default | Options |
|----------|---------|---------|
| `EMBEDDING_PROVIDER` | `sentence-transformers` | `sentence-transformers`, `gemini`, `openai`, `ollama` |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Model name for the chosen provider |
| `EMBEDDING_DIMENSIONS` | `384` | Match the embedding model |
| `LLM_PROVIDER` | `ollama` | `ollama`, `gemini`, `openai` |
| `LLM_MODEL` | `qwen3:8b` | Model name for the chosen provider |
| `EMBEDDING_API_KEY` | (empty) | Required for gemini/openai embedding |
| `LLM_API_KEY` | (empty) | Required for gemini/openai LLM |
| `LLM_BASE_URL` | (empty) | Custom Ollama endpoint |
| `SEAMLESS_WEB_USER` / `SEAMLESS_WEB_PASSWORD` | (empty) | Web UI auth (required for `--share`) |

**Gemini key auto-detection**: keys starting with `AQ.` are routed through Vertex AI Express Mode automatically; `AIza…` keys go through AI Studio. The user does not need a separate flag.

## Security

- **SQL injection prevention**: WHERE filters and `export` SQL validated via sqlglot AST — blocks writes, DDL, subqueries, and dangerous functions (SLEEP, BENCHMARK, LOAD_FILE).
- **Web UI**: localhost-only by default; `--share` requires the auth env vars.
- **LLM**: context truncated to 20K characters; retry with jitter for transient errors.

## Agent Workflow Patterns

### Pattern 1: SQL results as agent context
```python
# Agent generates SQL → seamless-rag formats as TOON
toon = rag.export("SELECT product, revenue, margin FROM sales WHERE quarter='Q3'")
# Feed `toon` to the next LLM call — typically 15–40% fewer tokens than JSON
```

### Pattern 2: Semantic search on text columns
```python
# When the question is fuzzy and not expressible as SQL
result = rag.ask("products customers complained about", top_k=10, mmr=True)
```

### Pattern 3: Hybrid filter + semantic
```python
# Combine SQL precision with vector semantics in a single MariaDB query
result = rag.ask("reliable laptops", where="price < 1000 AND category = 'electronics'")
```

### Pattern 4: Multi-column embedding for rich search
```python
# Embed multiple columns so searches match across fields
rag.embed_table("products", text_column=["name", "category", "price", "rating"])
# Internal: "Widget — Tools — 29.99 — 4.5"
result = rag.ask("cheap high-rated tools", where="price < 50")
```

### Pattern 5: Multi-step agent with accumulated TOON context
```python
# Each step: query DB → TOON → feed to LLM → next decision
# TOON savings compound across many steps
step1 = rag.export("SELECT region, SUM(revenue) FROM sales GROUP BY region")
# LLM analyzes, decides to drill into worst region
step2 = rag.export("SELECT product, units FROM sales WHERE region='EMEA' AND quarter='Q3'")
```

## For Contributors (project-local — skip if you only consume the package)

The repository ships a Makefile and a conda env named `seamless-rag` for development:

```bash
conda activate seamless-rag
make test-all     # ruff + unit + TOON spec conformance (no Docker)
make test-full    # also runs integration tests against a Docker MariaDB
make score        # quality dashboard
```

These targets only matter inside the seamless-rag source tree. End users installing from PyPI never need them.
