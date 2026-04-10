# Seamless-RAG — TODO

> Updated: 2026-04-11 (initial)
> Status: 0/259 tests passing

## P0 — Core (unit tests)
- [ ] TOON v3 tabular encoder (`src/seamless_rag/toon/encoder.py`)
- [ ] Token benchmark module (`src/seamless_rag/benchmark/compare.py`)
- [ ] SentenceTransformers provider (`src/seamless_rag/providers/sentence_transformers.py`)
- [ ] Pydantic Settings config (`src/seamless_rag/config.py`)

## P1 — Storage + Pipeline (integration tests)
- [ ] MariaDB VectorStore (`src/seamless_rag/storage/mariadb.py`)
- [ ] Auto-embedder watch + batch (`src/seamless_rag/pipeline/embedder.py`)
- [ ] RAG engine with token observation (`src/seamless_rag/pipeline/rag.py`)

## P2 — User Interface
- [ ] SeamlessRAG facade (`src/seamless_rag/core.py`)
- [ ] Typer CLI (`src/seamless_rag/cli.py`)
- [ ] Docker Compose end-to-end
- [ ] Dockerfile

## P3 — Polish & Delivery
- [ ] README.md (judge-facing)
- [ ] JUDGES_TESTING_GUIDE.md
- [ ] Demo script (2-4 min)
- [ ] Demo video recording
- [ ] Performance benchmarks with charts
- [ ] Push to hackathon remote
- [ ] Optional: Gradio web UI
