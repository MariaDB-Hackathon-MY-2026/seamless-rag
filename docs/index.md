# Seamless-RAG

**TOON-Native Auto-Embedding & RAG Toolkit for MariaDB**

Automatically embed your MariaDB tables and query them with RAG -- results formatted in TOON v3 for 30-58% token savings over JSON.

![Architecture](assets/architecture.svg)

## Features

- **Auto-Embed** -- Point at any MariaDB table, embed text columns with local or cloud models
- **Watch Mode** -- Polls for new inserts and auto-embeds them in real time
- **RAG Query** -- Vector search, TOON-formatted context, LLM answer in one call
- **Token Savings** -- Every query reports JSON vs TOON token comparison
- **Model-Agnostic** -- Swap embedding/LLM providers via config or environment variables

## Quick Example

```python
from seamless_rag import SeamlessRAG

rag = SeamlessRAG(host="localhost", database="mydb", password="secret")
rag.embed_table("articles", text_column="content")

result = rag.ask("What are the main topics?")
print(result.context_toon)
print(f"Tokens saved: {result.savings_pct:.1f}%")
```

## Token Savings

![JSON vs TOON](assets/toon-comparison.svg)

TOON v3 tabular format eliminates key repetition in structured data. More rows means more savings -- up to 58% fewer tokens at scale.

## Next Steps

- [Getting Started](getting-started.md) -- Install and run your first query in 5 minutes
- [Architecture](architecture.md) -- Understand the pipeline
- [API Reference](api-reference.md) -- Full Python API
- [Providers](providers.md) -- Configure embedding and LLM providers
