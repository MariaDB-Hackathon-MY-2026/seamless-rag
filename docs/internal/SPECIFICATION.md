# Seamless-RAG — Live Specification

> This document is LIVE — it reflects the current state of the implementation.
> Last updated: 2026-04-11

## Status: P0/P1/P2 COMPLETE — 99.6% test pass rate (489/491)

All core modules + multi-provider architecture implemented. 489/491 total tests passing.

## Architecture

```
SeamlessRAG (core.py)              ← facade: uses factory pattern
├── EmbeddingProvider (Protocol)   ← pluggable interface
│   ├── SentenceTransformersProvider ← local, free (384d)
│   ├── GeminiEmbeddingProvider    ← google-genai SDK (768d)
│   └── OpenAIEmbeddingProvider    ← openai SDK (3072d)
├── LLMProvider (Protocol)         ← pluggable interface
│   ├── GeminiLLMProvider          ← gemini-2.5-flash
│   ├── OpenAILLMProvider          ← gpt-4o
│   └── OllamaLLMProvider          ← local REST API
├── MariaDBVectorStore             ← VECTOR columns + HNSW search
├── AutoEmbedder (pipeline/)       ← watch mode + batch mode
├── RAGEngine (pipeline/)          ← search + TOON + LLM answer + benchmark
├── TOONEncoder (toon/)            ← full v3 spec encoder
└── TokenBenchmark (benchmark/)    ← JSON vs TOON token comparison
```

## Implemented Features

### TOON v3 Encoder (166/166 spec conformance)
- Tabular arrays: `[N,]{field1,field2}: row1 row2 ...`
- Object encoding: `key: value` with nesting
- Primitive/mixed/nested array encoding
- Delimiter options: comma (default), tab, pipe
- Key folding (safe mode) with collision avoidance
- All quoting rules (Section 7.2): keywords, numerics, structural chars
- All escape sequences (Section 7.1): `\\`, `\"`, `\n`, `\r`, `\t`
- Number canonicalization: no scientific notation, -0→0, NaN/Inf→null
- Field name quoting (Section 7.3): identifier pattern check

### Token Benchmark
- tiktoken cl100k_base tokenizer
- JSON vs TOON token and byte comparison
- 30%+ savings for 3-row tabular, 40%+ for 100-row

### Embedding Providers (Model-Agnostic)
- **SentenceTransformers** (default): all-MiniLM-L6-v2, 384d, local, free
- **Gemini**: gemini-embedding-001, configurable dims (768 default), google-genai SDK
- **OpenAI**: text-embedding-3-large, configurable dims (3072 default), openai SDK
- Factory pattern: `create_embedding_provider(settings)` auto-selects
- Foreign model auto-correction: switching providers auto-fixes model names
- Protocol-based: any class satisfying EmbeddingProvider works

### LLM Providers (Model-Agnostic)
- **Ollama** (default): local qwen3:8b, no API key needed
- **Gemini**: gemini-2.5-flash, google-genai SDK
- **OpenAI**: gpt-4o, openai SDK
- Factory pattern: `create_llm_provider(settings)` auto-selects
- Foreign model auto-correction for cross-provider switching

### RAG Engine
- Embed question → vector search → TOON format → LLM answer → token metrics
- LLM integration is optional (backward compatible without LLM)
- Observation layer: every query produces benchmark data
- Configurable top_k and context window

### MariaDB VectorStore
- Vector insert via `array.array('f')` binary protocol
- Cosine distance search with HNSW tuning
- CTE-based context windowing for neighboring chunks
- Schema management: ensure_vector_column

### AutoEmbedder
- Batch mode: bulk-embed with progress
- Watch mode: poll for new rows with high-water mark
- Exponential backoff retry on transient failures
- Error isolation: failed rows don't block pipeline

### CLI (Typer + Rich)
- `seamless-rag embed <table>`: bulk embedding
- `seamless-rag watch <table>`: auto-embed watch mode
- `seamless-rag ask "<question>"`: RAG query with benchmark
- `seamless-rag export "<SQL>"`: SQL to TOON export

## Test Results

```
Overall: 99.6% (489/491 total)
  lint:  100% (src/seamless_rag/)
  unit:  99.7% (298/299)
  spec:  100% (166/166)
  props: 91.7% (11/12)
  integration: 100% (17/17)
  eval:  100% (1/1)
```

## Known Limitations
- 1 property test edge case: very large floats without scientific notation
  can make TOON marginally longer than JSON for 2-row tables
- Integration tests require Docker MariaDB
