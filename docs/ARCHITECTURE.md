# Architecture

Seamless-RAG follows a layered architecture with pluggable protocols at each boundary.

![Pipeline](assets/architecture.svg)

## Pipeline Flow

1. **MariaDB** -- Source tables with text data stored alongside VECTOR columns
2. **Embedding** -- Text is embedded using a configurable provider (local or cloud)
3. **Vector Search** -- HNSW cosine similarity retrieves the top-K relevant rows
4. **TOON Format** -- Results are serialized using TOON v3 tabular encoding
5. **LLM** -- TOON context is sent to a language model for answer generation
6. **Answer** -- The response includes the answer, TOON context, and token benchmarks

## Component Overview

```
SeamlessRAG (facade)
+-- EmbeddingProvider (Protocol)     <- pluggable
|   +-- SentenceTransformersProvider <- local, free (384d)
|   +-- GeminiEmbeddingProvider      <- google-genai SDK (768d)
|   +-- OpenAIEmbeddingProvider      <- openai SDK (3072d)
+-- LLMProvider (Protocol)           <- pluggable
|   +-- OllamaLLMProvider            <- local REST (default)
|   +-- GeminiLLMProvider            <- gemini-2.5-flash
|   +-- OpenAILLMProvider            <- gpt-4o
+-- MariaDBVectorStore               <- VECTOR + HNSW cosine search
+-- AutoEmbedder                     <- watch + batch with retry
+-- RAGEngine                        <- search -> TOON -> LLM -> benchmark
+-- TOONEncoder                      <- full v3 spec (166/166)
+-- TokenBenchmark                   <- tiktoken cl100k_base
```

## Protocol-Based Design

Both `EmbeddingProvider` and `LLMProvider` are defined as `typing.Protocol` classes. Any object that implements the required methods works -- no inheritance needed.

This means you can add a new provider by writing a class with the right method signatures and registering it in the factory.

## Storage Layer

`MariaDBVectorStore` uses MariaDB's native VECTOR column type with HNSW indexing for cosine similarity search. Embeddings are stored as binary arrays using `array.array('f', ...)` for efficient transfer over the native protocol.

## TOON Encoder

The TOON v3 tabular encoder converts structured query results into a compact text format. Field names appear once in a header row, and data rows contain only values. This eliminates the per-row key repetition found in JSON, saving 30-58% of tokens depending on the number of rows.
