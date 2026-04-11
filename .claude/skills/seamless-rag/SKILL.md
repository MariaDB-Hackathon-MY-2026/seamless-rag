---
name: seamless-rag
description: "Work with the Seamless-RAG toolkit — MariaDB vector search, TOON encoding, auto-embedding, and RAG queries. Use this skill when the user works in the seamless-rag project, asks about MariaDB vector operations, TOON format encoding, embedding providers, or RAG pipeline tasks. Also trigger when the user wants to query databases via vector search, convert data to TOON format, or manage MariaDB embedding workflows."
---

# Seamless-RAG Agent Skill

Seamless-RAG is a **thin bridging layer** between MariaDB and LLMs/agents. It does NOT replace SQL — it complements it with vector search for semantic queries, and provides TOON format for token-efficient data consumption.

```
Agent (intent, strategy, judgment)
  ↕ CLI / Python API
Seamless-RAG (embed rows, vector search, format as TOON)
  ↕ mariadb-connector-python
MariaDB (store, index, execute SQL + VEC_DISTANCE)
```

## When to Use What

- **Precise query** ("Q3 revenue > 1M", aggregations, JOINs): use the **text-to-sql** skill → generates SQL → `export()` → TOON
- **Semantic query** ("find similar products"): `rag.ask(question)` for vector search
- **Hybrid** ("waterproof watches under $50"): `rag.ask(question, where="price < 50")`
- **Any SQL result → LLM**: always use `export()` to convert to TOON before feeding to LLM

> **Routing rule**: if the user's question involves numbers, aggregations, GROUP BY, or exact filters → route to `text-to-sql` skill. If it's fuzzy/semantic → use `ask`. If both → use `ask --where`.

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
- Header `[N,]{...}:` tells you row count and column names
- Each indented line is one row, values in column order
- `null` = no value, `true`/`false` = booleans
- Quoted values (`"Smith, John"`) contain commas or special characters
- Unquoted values are plain text, numbers, or booleans
- Numbers are canonical: no scientific notation, no trailing zeros

**Why TOON over JSON**: 10-55% fewer tokens vs compact JSON for structured data. Field names appear once in the header instead of repeating per row. Savings are highest with many rows and short values.

## Project Location

```
/Users/sunfl/Documents/study/MSrag/workspace/
```

**Conda env**: `seamless-rag` — always prefix commands with `conda run -n seamless-rag`.

## CLI Commands

Global options: `--host`, `--port`, `--user`, `--password`, `--database`, `--provider`, `--model`, `--log-level`

```bash
# Core: data already in MariaDB → add vectors
seamless-rag init                                            # VECTOR columns + HNSW index
seamless-rag embed [--table chunks] [--column content]       # Bulk-embed single column
seamless-rag embed --table products --columns "name,category,price"  # Multi-column embed
seamless-rag watch [--table chunks] [--columns "name,desc"]  # Auto-embed new inserts

# Query
seamless-rag ask "question" [--top-k 5] [--where "price<50"] [--mmr] [--context-window 1]
seamless-rag export "SELECT ... FROM ..."                    # Any SQL → TOON format

# Tools
seamless-rag benchmark [--rows 50] [--cols 6]                # JSON vs TOON comparison
seamless-rag web [--port 7860] [--share]                     # Gradio web UI (localhost-only by default)
seamless-rag demo                                            # End-to-end demo
seamless-rag ingest <path> [--chunk-size 500] [--overlap 50] # Load text files for testing
```

## Python API

```python
from seamless_rag import SeamlessRAG

with SeamlessRAG(host="127.0.0.1", database="seamless_rag") as rag:
    rag.init()                                        # create schema

    # Single-column embed (default)
    rag.embed_table("articles", text_column="content")

    # Multi-column embed — richer semantics
    rag.embed_table("products", text_column=["name", "category", "price"])
    # Internally: "Widget — Tools — 29.99" → searches match name AND price

    # Semantic search with hybrid filter
    result = rag.ask("waterproof watches", top_k=5, where="price < 500", mmr=True)
    # result.answer           : str       — LLM answer
    # result.context_toon     : str       — TOON context (feed to next LLM call)
    # result.savings_pct      : float     — token savings vs compact JSON
    # result.sources          : list[dict] — raw results

    # SQL → TOON (for precise queries, agent tools)
    toon = rag.export("SELECT region, SUM(revenue) FROM sales GROUP BY region")
```

## TOON Encoder (standalone)

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
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Model name for chosen provider |
| `LLM_PROVIDER` | `ollama` | `ollama`, `gemini`, `openai` |
| `LLM_MODEL` | `qwen3:8b` | Model name for chosen provider |
| `EMBEDDING_API_KEY` | (empty) | Required for gemini/openai embedding |
| `LLM_API_KEY` | (empty) | Required for gemini LLM |
| `OPENAI_API_KEY` | (empty) | Required for openai LLM |
| `LLM_BASE_URL` | (empty) | Custom Ollama endpoint |
| `SEAMLESS_WEB_USER` | (empty) | Web UI auth username (required for --share) |
| `SEAMLESS_WEB_PASSWORD` | (empty) | Web UI auth password (required for --share) |

## Security

- **SQL injection prevention**: WHERE filters validated via sqlglot AST — blocks writes, DDL, subqueries, dangerous functions
- **Web UI**: localhost-only by default; `--share` requires auth env vars
- **LLM**: context truncated to 20K chars; retry with jitter for transient errors

## Testing

```bash
conda run -n seamless-rag make test-all    # lint + unit + spec (no Docker)
conda run -n seamless-rag make test-full   # includes integration
conda run -n seamless-rag make score       # quality dashboard
```

538/538 tests passing (100%). TOON spec: 166/166.

## Agent Workflow Patterns

### Pattern 1: SQL results as agent context
```python
# Agent generates SQL, seamless-rag formats as TOON
toon = rag.export("SELECT product, revenue, margin FROM sales WHERE quarter='Q3'")
# Feed toon to next LLM call — 60% fewer tokens than JSON
```

### Pattern 2: Semantic search on text columns
```python
# When the question is fuzzy, not expressible as SQL
result = rag.ask("products customers complained about", top_k=10, mmr=True)
```

### Pattern 3: Hybrid filter + semantic
```python
# Combine SQL precision with vector semantics
result = rag.ask("reliable laptops", where="price < 1000 AND category = 'electronics'")
```

### Pattern 4: Multi-column embedding for rich search
```python
# Embed multiple columns for searches that span fields
rag.embed_table("products", text_column=["name", "category", "price", "rating"])
# Internal: "Widget — Tools — 29.99 — 4.5"
# Now "cheap high-rated tools" matches on ALL fields, not just description
result = rag.ask("cheap high-rated tools", where="price < 50")
```

### Pattern 5: Multi-step agent with accumulated TOON context
```python
# Each step: query DB → TOON → feed to LLM → next decision
# TOON saves 15-30% per step, compounding over 20 steps
step1 = rag.export("SELECT region, SUM(revenue) FROM sales GROUP BY region")
# LLM analyzes, decides to drill into worst region
step2 = rag.export("SELECT product, units FROM sales WHERE region='EMEA' AND quarter='Q3'")
```
