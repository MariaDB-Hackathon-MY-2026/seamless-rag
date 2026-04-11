# Getting Started

Get Seamless-RAG running and execute your first query in under 5 minutes.

## Prerequisites

- Python 3.12+
- Docker (for MariaDB)
- conda (recommended) or virtualenv

## Installation

```bash
git clone https://github.com/SunflowersLwtech/seamless-rag.git
cd seamless-rag

# Create environment
conda create -n seamless-rag python=3.12 -y
conda activate seamless-rag

# Install with all extras
pip install -e ".[dev,mariadb,embeddings]"
```

## Start MariaDB

```bash
docker compose up -d
```

This starts MariaDB 11.8 with VECTOR support. Default credentials are in `docker-compose.yml`.

## Initialize and Ingest

```bash
# Create the schema (documents + chunks tables with VECTOR columns)
seamless-rag init

# Ingest text files — split at paragraph boundaries
seamless-rag ingest ./data/articles/
```

## Your First Query

```bash
seamless-rag ask "What are the key findings?"
```

The output includes the LLM answer, TOON-formatted context, and a token comparison showing savings vs JSON.

## Embed Existing Tables

If your data is already in MariaDB, skip `ingest` and embed directly:

```bash
# Single column (default)
seamless-rag embed --table products --column description

# Multi-column — concatenated for richer vector search
seamless-rag embed --table products --columns "name,category,price,rating"
# Internally: "Widget — Tools — 29.99 — 4.5"

# Now semantic + SQL filter queries work
seamless-rag ask "cheap high-rated tools" --where "price < 50"
```

## Python API

```python
from seamless_rag import SeamlessRAG

with SeamlessRAG(host="localhost", database="seamless_rag") as rag:
    rag.init()

    # Single-column embed
    rag.embed_table("articles", text_column="content")

    # Multi-column embed — richer semantics
    rag.embed_table("products", text_column=["name", "category", "price"])

    # Semantic search
    result = rag.ask("What are the main topics?")
    print(result.answer)
    print(f"Saved {result.savings_pct:.1f}% tokens")

    # Hybrid: semantic + SQL filter
    result = rag.ask("affordable tools", where="price < 50", mmr=True)

    # Export any SQL query as TOON
    toon = rag.export("SELECT name, price FROM products ORDER BY price LIMIT 10")
    print(toon)
```

## SQL Export

Convert any SELECT query result to TOON format:

```bash
seamless-rag export "SELECT id, title, avg_rating FROM movies ORDER BY avg_rating DESC LIMIT 10"
```

Output:

```
[10,]{id,title,avg_rating}:
  1,"Shawshank Redemption, The (1994)",4.43
  2,"Godfather, The (1972)",4.29
  3,Fight Club (1999),4.27
  ...
```

## Web UI

Launch a Gradio web interface with 6 tabs:

```bash
seamless-rag web              # localhost only
seamless-rag web --share      # public link (requires auth env vars)
```

Tabs: Ask, Benchmark, JSON → TOON, SQL Export, Data, Status.

## Watch Mode

Monitor a table for new rows and auto-embed them:

```bash
seamless-rag watch --table articles --column content --interval 2
```

Features: high-water mark tracking, exponential backoff retry, error isolation, Rich live display.

## Configuration

Configure via environment variables or a `.env` file:

```bash
# .env
MARIADB_HOST=127.0.0.1
MARIADB_PASSWORD=seamless
EMBEDDING_PROVIDER=sentence-transformers  # or gemini, openai, ollama
LLM_PROVIDER=ollama                       # or gemini, openai
```

See [Providers](providers.md) for provider-specific setup.

## Running Tests

```bash
make test-all    # lint + unit + spec (no Docker needed)
make test-full   # all suites including integration
make score       # quality dashboard
```
