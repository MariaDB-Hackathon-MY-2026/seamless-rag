# Seamless-RAG

**Vector Search & TOON Format for MariaDB**

Turn any MariaDB table into a searchable vector store. Query results come back in TOON v3 tabular format — a compact wire format that saves 20-40% of tokens when feeding structured data to LLMs or agents.

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
