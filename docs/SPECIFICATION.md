# Seamless-RAG — Live Specification

> This document is LIVE — it reflects the current state of the implementation.
> Last updated: 2026-04-11

## Status: P0 COMPLETE, P1/P2 IMPLEMENTED — 99.5% test pass rate

All core modules implemented. 432/434 tests passing.

## Architecture

```
SeamlessRAG (core.py)              ← facade: holds all dependencies
├── SentenceTransformersProvider   ← all-MiniLM-L6-v2 (384d, local)
├── MariaDBVectorStore             ← VECTOR columns + HNSW search
├── AutoEmbedder (pipeline/)       ← watch mode + batch mode
├── RAGEngine (pipeline/)          ← search + TOON format + token benchmark
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

### Embedding Provider
- SentenceTransformers with all-MiniLM-L6-v2 (384 dimensions)
- Single and batch embedding
- Protocol-based: any provider satisfying EmbeddingProvider works

### RAG Engine
- Embed question → vector search → TOON format → token metrics
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
Overall: 99.5% (432/434 passed)
  lint:  100% (1/1)
  unit:  99.6% (253/254)
  spec:  100% (166/166)
  props: 91.7% (11/12)
  eval:  100% (1/1)
```

## Known Limitations
- 1 property test edge case: very large floats without scientific notation
  can make TOON marginally longer than JSON for 2-row tables
- Integration tests require Docker MariaDB
