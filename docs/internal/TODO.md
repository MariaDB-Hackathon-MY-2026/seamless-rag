# Seamless-RAG — TODO

> Updated: 2026-04-12
> Status: 520/522 tests passing (99.6%)
> Codex Grade: A (95.85/100)

---

## MariaDB Ecosystem — Complete

All features required for a complete MariaDB vector toolkit are implemented.

### Core Engine
- [x] TOON v3 encoder — 774 lines, 166/166 spec conformance
- [x] Token benchmark — tiktoken cl100k_base, GPT-4o cost calculation
- [x] RAG pipeline — search -> TOON -> LLM -> benchmark observation layer
- [x] MMR diversity selection (Carbonell & Goldstein 1998, numpy)
- [x] Filter + vector hybrid search (WHERE clause + VEC_DISTANCE)
- [x] CTE context windowing (neighboring chunks)
- [x] Dynamic column detection for custom tables
- [x] Decimal/date/datetime type support in TOON encoder
- [x] UNION ALL / INTERSECT / EXCEPT support in SQL export

### Embedding Providers
- [x] SentenceTransformers — local, free, 384d (default)
- [x] Gemini — google-genai SDK, 768d, MRL dimension control
- [x] OpenAI — openai SDK, 3072d
- [x] Ollama — REST API, nomic-embed-text 768d
- [x] Factory with foreign model auto-correction

### LLM Providers
- [x] Ollama — local REST, qwen3:8b (default)
- [x] Gemini — gemini-2.5-flash
- [x] OpenAI — gpt-4o
- [x] Factory with foreign model auto-correction

### Storage
- [x] MariaDB VectorStore — VECTOR columns, HNSW index
- [x] Connection pool (mariadb.ConnectionPool, size=5)
- [x] Version check (>= 11.7.2)
- [x] SQL injection protection (sqlglot AST validation)
- [x] Context manager support
- [x] executemany batch operations

### CLI (9 commands)
- [x] init — create schema with VECTOR + HNSW
- [x] embed — bulk-embed existing rows, single or multi-column
- [x] watch — auto-embed new inserts (Rich live display)
- [x] ask — RAG query with --where, --mmr, --context-window
- [x] export — SQL SELECT / UNION -> TOON
- [x] benchmark — JSON vs TOON comparison
- [x] web — Gradio web UI (6 tabs, Polanyi design)
- [x] demo — end-to-end with sample data
- [x] ingest — convenience file loader

### Testing
- [x] 520/522 tests (99.6%)
- [x] TOON spec: 166/166 (100%)
- [x] Unit: 329/330 (99.7%)
- [x] Integration: 17/17 (100%)
- [x] Property-based (Hypothesis): 11/12
- [x] Real-data benchmark: MovieLens + Restaurant datasets
- [x] CLI end-to-end: 12/12 commands pass
- [x] RAG quality: 15/16 queries with grounded LLM answers

### Docs & Deployment
- [x] README.md — real benchmark data, honest positioning
- [x] MkDocs Material site — 8 pages, GitHub Pages deployed
- [x] CONTRIBUTING.md
- [x] JUDGES_TESTING_GUIDE.md
- [x] Docker Compose (MariaDB 11.8)
- [x] Dockerfile
- [x] Apache-2.0 LICENSE
- [x] Agent skills (seamless-rag + text-to-sql)

---

## Future Roadmap — Decouple & Distribute

> Roadmap for evolving from hackathon project to open-source ecosystem tool.
> Ordered by priority.

### P0 — Distribution Infrastructure (Lifeline of Open Source)
- [ ] PyPI release — `pip install seamless-rag` direct install
- [ ] GitHub Actions CI — auto-run `make test-all` on PRs, green badge
- [ ] Issue templates — bug report / feature request / question
- [ ] PR template — checklist (tests pass, lint clean, docs updated)

### P1 — TOON Decoupling (Highest Growth Leverage)
- [ ] Extract `toon-format` as standalone package — zero dependencies, pure Python
  - `pip install toon-format`
  - Support `list[dict]` / pandas DataFrame / CSV input
  - Separate README, PyPI, repository
  - This is the true differentiator, should not be tied to MariaDB
- [ ] TOON decoder — currently encoder only, need `decode(toon_str) -> list[dict]`
- [ ] TOON CLI — `toon encode data.json` / `toon decode data.toon`

### P2 — Zero-Infrastructure Trial (Lower Onboarding Barrier)
- [ ] SQLite vector backend — sqlite-vec or in-memory backend
  - Let users `pip install seamless-rag && seamless-rag demo` with zero Docker
- [ ] In-memory VectorStore — for testing and quick prototyping
- [ ] `seamless-rag quickstart` command — auto-detect available backend

### P3 — LLM Quality Validation (Complete the Token Savings Narrative)
- [ ] LLM comprehension comparison — same question, same data:
  - JSON context vs TOON context vs Markdown table context
  - Run 50 questions each on GPT-4o + Gemini, compare answer quality
  - Publish results to README (data-backed claims are compelling)
- [ ] Few-shot TOON prompt — optimal system prompt for teaching LLMs to read TOON
- [ ] TOON as tool output format — declare return format in agent tool descriptions

### P4 — Ecosystem Integration
- [ ] LangChain Retriever adapter — `SeamlessRAGRetriever`
- [ ] LlamaIndex VectorStore adapter
- [ ] MCP Server — expose as Model Context Protocol tool
- [ ] pandas integration — `df.to_toon()` / `toon.read_toon()`

### P5 — Advanced Retrieval
- [ ] Rerank — integrate cross-encoder (e.g. ms-marco-MiniLM)
- [ ] Hybrid search — BM25 + vector fusion
- [ ] Async support — `async embed()`, `async ask()`
- [ ] Streaming LLM output — token-by-token response

### P6 — Brand & Community
- [ ] Rename consideration — "seamless-rag" is too generic, "toon-db"/"mariadb-rag" more searchable
- [ ] Demo video (2-4 min) — terminal recording + narration
- [ ] Blog post — "Why You Shouldn't Feed Structured Data to LLMs as JSON"
- [ ] MariaDB official ecosystem submission — mariadb.org ecosystem page
- [ ] Conference talk proposal — MariaDB Server Fest / PyCon
