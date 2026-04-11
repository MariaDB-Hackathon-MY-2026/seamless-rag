# Architecture

Seamless-RAG follows a layered architecture with pluggable protocols at each boundary.

## Pipeline Flow

```
"Q3 revenue by region?"           "Find products similar to X"
        │                                    │
   Text-to-SQL                        Vector Search
   (LLM generates SQL)              (cosine similarity)
        │                                    │
        └──────────┬─────────────────────────┘
                   ▼
           MariaDB executes
                   ▼
           list[dict] results
                   ▼
        Seamless-RAG → TOON format     ← saves 20-40% tokens
                   ▼
           LLM / Agent consumes
```

1. **MariaDB** — Source tables with text data stored alongside VECTOR columns
2. **Embedding** — Text is embedded using a configurable provider (local or cloud)
3. **Vector Search** — HNSW cosine similarity retrieves the top-K relevant rows
4. **Hybrid Filter** — Optional SQL WHERE clause combined with vector search
5. **MMR Diversity** — Optional Maximal Marginal Relevance reranking
6. **TOON Format** — Results are serialized using TOON v3 tabular encoding
7. **LLM** — TOON context is sent to a language model for answer generation
8. **Benchmark** — Every query automatically computes JSON vs TOON token comparison

## Component Overview

```
SeamlessRAG (facade)
├── EmbeddingProvider (Protocol)     ← pluggable
│   ├── SentenceTransformersProvider ← local, free (384d)
│   ├── GeminiEmbeddingProvider      ← google-genai SDK (768d)
│   ├── OpenAIEmbeddingProvider      ← openai SDK (3072d)
│   └── OllamaEmbeddingProvider      ← REST API (768d)
├── LLMProvider (Protocol)           ← pluggable
│   ├── OllamaLLMProvider            ← local REST (default)
│   ├── GeminiLLMProvider            ← gemini-2.5-flash
│   └── OpenAILLMProvider            ← gpt-4o
├── MariaDBVectorStore               ← VECTOR + HNSW cosine search
│     ├── Connection pool (size=5)
│     ├── SQL injection protection (sqlglot AST validation)
│     └── Dynamic column detection for custom tables
├── AutoEmbedder                     ← watch + batch with retry
│     ├── Multi-column concatenation ("name — category — price")
│     └── Error isolation (failed rows don't block pipeline)
├── RAGEngine                        ← search → TOON → LLM → benchmark
│     ├── Hybrid search (WHERE + VEC_DISTANCE)
│     ├── MMR diversity selection (Carbonell & Goldstein 1998)
│     └── LLM retry with exponential backoff
├── TOONEncoder                      ← full v3 spec (166/166)
│     └── Supports Decimal, date, datetime types
└── TokenBenchmark                   ← tiktoken cl100k_base
```

## Protocol-Based Design

Both `EmbeddingProvider` and `LLMProvider` are `typing.Protocol` classes with `runtime_checkable`. Any object implementing the required methods works — no inheritance needed.

```python
class EmbeddingProvider(Protocol):
    @property
    def dimensions(self) -> int: ...
    def embed(self, text: str) -> list[float]: ...
    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]: ...
```

Add a new provider by writing a class with these methods and registering it in the factory.

## Storage Layer

`MariaDBVectorStore` uses MariaDB's native VECTOR column type (11.7+) with HNSW indexing. Key features:

- **Binary protocol**: embeddings as `array.array('f', ...)` for efficient transfer
- **Connection pool**: thread-safe pool of 5 connections
- **Dynamic search**: auto-detects all non-VECTOR columns, works with any table schema
- **SQL safety**: all WHERE clauses and export queries validated via sqlglot AST parsing — blocks writes, DDL, subqueries, and dangerous functions

## TOON Encoder

The TOON v3 tabular encoder converts `list[dict]` into compact text. Field names appear once in a header, data rows contain only values. Measured savings on real data:

- MovieLens (7 columns, 100 rows): **24.1%** fewer tokens
- Restaurant (9 columns, 100 rows): **38.8%** fewer tokens
- Numeric-only metadata: up to **39.6%** fewer tokens

## Retrieval Strategies

### Hybrid Search

Combines exact SQL filters with vector similarity:

```python
result = rag.ask("waterproof watches", where="price < 500 AND brand = 'Casio'")
```

The WHERE clause is validated via sqlglot AST parsing and appended to the vector search query.

### MMR Diversity

Maximal Marginal Relevance (Carbonell & Goldstein 1998) balances relevance and diversity:

```python
result = rag.ask("war movies", mmr=True, mmr_lambda=0.3)
# lambda=1.0 → pure relevance, lambda=0.0 → pure diversity
```
