# API Reference

## SeamlessRAG

The main facade class. Holds all dependencies and exposes the high-level API.

```python
from seamless_rag import SeamlessRAG

rag = SeamlessRAG(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="seamless",
    database="seamless_rag",
    table="chunks",           # default table for ask()
)
```

Supports context manager for automatic cleanup:

```python
with SeamlessRAG(host="localhost") as rag:
    result = rag.ask("question")
```

### Methods

#### `init(dimensions=None)`

Create database schema (documents + chunks tables with VECTOR columns and HNSW index).

If `dimensions` is not specified, uses the embedding provider's native dimensions.

#### `embed_table(table, text_column, batch_size=64)`

Bulk-embed all rows in a table that lack embeddings.

```python
# Single column
rag.embed_table("articles", text_column="content")

# Multi-column — values concatenated with " — " for richer embeddings
rag.embed_table("products", text_column=["name", "category", "price"])
# Internally: "Widget — Tools — 29.99"
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `table` | `str` | `None` (uses default) | Table name |
| `text_column` | `str \| list[str]` | `"content"` | Column(s) to embed |
| `batch_size` | `int` | `64` | Rows per embedding batch |

**Returns:** `dict` with keys `embedded`, `failed`, `total`.

#### `ask(question, top_k=5, where="", mmr=False, mmr_lambda=0.5, context_window=0)`

Full RAG query: embed question → vector search → TOON format → LLM answer → benchmark.

```python
# Basic
result = rag.ask("What are the main findings?")

# Hybrid: semantic + SQL filter
result = rag.ask("affordable tools", where="price < 50")

# MMR diversity
result = rag.ask("war movies", mmr=True, mmr_lambda=0.3)

# Context window (include neighboring chunks)
result = rag.ask("details about section 3", context_window=2)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `question` | `str` | — | Natural language query |
| `top_k` | `int` | `5` | Number of results |
| `where` | `str` | `""` | SQL WHERE filter for hybrid search |
| `mmr` | `bool` | `False` | Apply MMR diversity selection |
| `mmr_lambda` | `float` | `0.5` | 0 = diverse, 1 = relevant |
| `context_window` | `int` | `0` | Include N neighboring chunks |

**Returns:** `RAGResult`

#### `export(query)`

Execute a SQL SELECT query and return results as TOON format.

```python
toon = rag.export("SELECT region, SUM(revenue) FROM sales GROUP BY region")
```

Supports SELECT, UNION ALL, INTERSECT, EXCEPT. Writes/DDL are blocked by sqlglot validation.

#### `ingest(title, texts)`

Create a document and embed all text chunks.

```python
doc_id = rag.ingest("Research Paper", ["chunk1...", "chunk2..."])
```

#### `watch(table, text_column, interval=2.0)`

Poll for new rows and auto-embed. Blocks until interrupted.

#### `close()`

Close the database connection pool.

---

## RAGResult

Returned by `SeamlessRAG.ask()`.

| Field | Type | Description |
|-------|------|-------------|
| `answer` | `str` | LLM-generated answer (empty if no LLM) |
| `context_toon` | `str` | TOON-formatted context sent to LLM |
| `context_json` | `str` | Equivalent compact JSON (for comparison) |
| `toon_tokens` | `int` | Token count of TOON context |
| `json_tokens` | `int` | Token count of JSON context |
| `savings_pct` | `float` | Percentage of tokens saved |
| `json_cost_usd` | `float` | Estimated JSON cost (GPT-4o pricing) |
| `toon_cost_usd` | `float` | Estimated TOON cost |
| `savings_cost_usd` | `float` | Cost saved per query |
| `sources` | `list[dict]` | Source rows with distance scores |

---

## Settings

Pydantic Settings class. Configure via environment variables or `.env` file.

| Setting | Env Var | Default | Description |
|---------|---------|---------|-------------|
| `mariadb_host` | `MARIADB_HOST` | `127.0.0.1` | Database host |
| `mariadb_port` | `MARIADB_PORT` | `3306` | Database port |
| `mariadb_user` | `MARIADB_USER` | `root` | Database user |
| `mariadb_password` | `MARIADB_PASSWORD` | `seamless` | Database password |
| `mariadb_database` | `MARIADB_DATABASE` | `seamless_rag` | Database name |
| `embedding_provider` | `EMBEDDING_PROVIDER` | `sentence-transformers` | Provider name |
| `embedding_model` | `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Model name |
| `embedding_dimensions` | `EMBEDDING_DIMENSIONS` | `384` | Vector dimensions |
| `embedding_api_key` | `EMBEDDING_API_KEY` | `""` | API key (gemini/openai) |
| `llm_provider` | `LLM_PROVIDER` | `ollama` | LLM provider |
| `llm_model` | `LLM_MODEL` | `qwen3:8b` | LLM model name |
| `llm_api_key` | `LLM_API_KEY` | `""` | LLM API key |
| `llm_base_url` | `LLM_BASE_URL` | `""` | Custom Ollama endpoint |
| `watch_interval` | `WATCH_INTERVAL` | `2.0` | Polling interval (seconds) |
| `watch_batch_size` | `WATCH_BATCH_SIZE` | `64` | Batch size for embedding |

---

## TOON Encoder (standalone)

```python
from seamless_rag.toon.encoder import encode_tabular

toon = encode_tabular([
    {"id": 1, "name": "Alice", "score": 95},
    {"id": 2, "name": "Bob",   "score": 87},
])
# [2,]{id,name,score}:
#   1,Alice,95
#   2,Bob,87
```

---

## CLI Commands

```
seamless-rag init                                    # Create schema
seamless-rag embed [--table T] [--columns "a,b,c"]  # Bulk embed
seamless-rag watch [--table T] [--interval 2]        # Auto-embed
seamless-rag ask "question" [--where "x"] [--mmr]   # RAG query
seamless-rag export "SELECT ..."                     # SQL → TOON
seamless-rag benchmark [--rows 50] [--cols 6]        # Token comparison
seamless-rag ingest <path> [--chunk-size 500]        # Load text files
seamless-rag web [--port 7860] [--share]             # Gradio web UI
seamless-rag demo                                    # End-to-end demo
```

Global options: `--host`, `--port`, `--user`, `--password`, `--database`, `--provider`, `--model`, `--log-level`
