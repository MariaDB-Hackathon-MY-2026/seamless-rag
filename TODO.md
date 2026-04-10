# Seamless-RAG — TODO

> Updated: 2026-04-11
> Status: 432/434 tests passing (99.5%)

## P0 — Core (unit tests) ✓
- [x] TOON v3 tabular encoder (`src/seamless_rag/toon/encoder.py`) — 166/166 spec, 44/44 unit
- [x] Token benchmark module (`src/seamless_rag/benchmark/compare.py`) — 9/9 tests
- [x] SentenceTransformers provider (`src/seamless_rag/providers/sentence_transformers.py`) — 12/12 tests
- [x] Pydantic Settings config (`src/seamless_rag/config.py`) — already implemented
- [x] RAG pipeline engine (`src/seamless_rag/pipeline/rag.py`) — 10/10 tests

## P1 — Storage + Pipeline (integration tests)
- [x] MariaDB VectorStore (`src/seamless_rag/storage/mariadb.py`)
- [x] Auto-embedder watch + batch (`src/seamless_rag/pipeline/embedder.py`)
- [x] RAG engine with token observation (`src/seamless_rag/pipeline/rag.py`)
- [ ] Integration tests (needs Docker MariaDB)

## P2 — User Interface
- [x] SeamlessRAG facade (`src/seamless_rag/core.py`)
- [x] Typer CLI (`src/seamless_rag/cli.py`)
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
