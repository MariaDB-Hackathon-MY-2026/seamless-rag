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
    model="all-MiniLM-L6-v2",
)
```

Supports context manager usage for automatic cleanup:

```python
with SeamlessRAG(host="localhost") as rag:
    result = rag.ask("question")
```

### Methods

| Method | Description |
|--------|-------------|
| `init()` | Create database schema and vector tables |
| `embed_table(table, text_column, ...)` | Embed all rows in a table |
| `watch(table, text_column, interval)` | Poll for new rows and auto-embed |
| `ask(question) -> RAGResult` | Run a full RAG query |
| `ingest(doc_id, chunks)` | Insert and embed text chunks |
| `export_toon(sql) -> str` | Execute SQL and return TOON-formatted output |

## RAGResult

Returned by `SeamlessRAG.ask()`.

| Field | Type | Description |
|-------|------|-------------|
| `answer` | `str` | LLM-generated answer |
| `context_toon` | `str` | TOON-formatted context sent to the LLM |
| `context_json` | `str` | Equivalent JSON context (for comparison) |
| `toon_tokens` | `int` | Token count of TOON context |
| `json_tokens` | `int` | Token count of JSON context |
| `savings_pct` | `float` | Percentage of tokens saved |
| `sources` | `list[dict]` | Source rows with distance scores |

## Settings

Pydantic Settings class. Configure via constructor, environment variables, or `.env` file.

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
| `llm_provider` | `LLM_PROVIDER` | `ollama` | LLM provider name |
| `llm_model` | `LLM_MODEL` | `qwen3:8b` | LLM model name |
| `watch_interval` | `WATCH_INTERVAL` | `2.0` | Polling interval (seconds) |
| `watch_batch_size` | `WATCH_BATCH_SIZE` | `64` | Batch size for embedding |

## TOON Encoder

```python
from seamless_rag.toon.encoder import encode_tabular

toon_str = encode_tabular(
    rows=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
)
# Output:
# [2,]{id,name}:
#   1,Alice
#   2,Bob
```
