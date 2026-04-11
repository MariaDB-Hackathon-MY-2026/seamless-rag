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

This starts MariaDB 11.8 with VECTOR support enabled. The default credentials are configured in `docker-compose.yml`.

## Initialize and Ingest

```bash
# Create the schema
seamless-rag init

# Ingest text files
seamless-rag ingest ./data/articles/
```

## Your First Query

```bash
seamless-rag ask "What are the key findings?"
```

The output includes the LLM answer, TOON-formatted context, and a token comparison showing savings vs JSON.

## Python API

```python
from seamless_rag import SeamlessRAG

with SeamlessRAG(host="localhost", database="seamless_rag") as rag:
    rag.init()
    rag.embed_table("articles", text_column="content")
    result = rag.ask("What are the main topics?")
    print(result.answer)
    print(f"Saved {result.savings_pct:.1f}% tokens")
```

## Configuration

Seamless-RAG uses Pydantic Settings. Configure via environment variables or a `.env` file:

```bash
# .env
MARIADB_HOST=127.0.0.1
MARIADB_PASSWORD=seamless
EMBEDDING_PROVIDER=sentence-transformers  # or gemini, openai
LLM_PROVIDER=ollama                       # or gemini, openai
```

See [Providers](providers.md) for provider-specific setup.

## Watch Mode

Monitor a table for new rows and auto-embed them:

```bash
seamless-rag watch --table articles --column content --interval 2
```

## Running Tests

```bash
make test-all    # lint + unit + spec (no Docker needed)
make test-full   # all suites including integration
```
