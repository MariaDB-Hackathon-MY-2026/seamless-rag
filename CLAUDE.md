# Seamless-RAG — Autonomous Development Protocol

## Mission

Build a championship-winning TOON-Native Auto-Embedding & RAG Toolkit for MariaDB.
Grade A evaluation. "One of the strongest submissions across both batches."
Target: 100% test pass rate → submit to hackathon repo → win.

## Environment

- **Conda env**: `seamless-rag` (activate with `conda activate seamless-rag`)
- **Docker**: MariaDB 11.8 via `docker compose up -d` (dev) or `docker compose -f docker-compose.test.yml up -d` (test with tmpfs)
- **Package**: installed editable via `pip install -e ".[dev]"` in the conda env
- **NEVER install to global Python** — always use the conda env

## Test Commands

```bash
make test-quick       # unit tests, stop on first failure (hook calls this)
make test-unit        # all unit tests
make test-spec        # TOON spec conformance (358 official fixtures)
make test-props       # hypothesis property-based tests
make test-all         # lint + unit + spec (fast, no Docker)
make test-full        # all suites including integration (needs Docker)
make score            # quality score dashboard
make lint             # ruff check
python eval/harness.py # immutable evaluation (composite score)
```

## IRON RULES

### 1. Never Stop
Do NOT stop to ask the user questions. Do NOT ask "shall I continue?" or "what next?".
When you finish a task, pick the next highest-priority unfinished item and continue.
Only stop if the user explicitly types STOP in the terminal.

### 2. Research Before Implementing
When facing a non-trivial problem, use these tools (NOT trial-and-error):

**Codebase exploration:**
```
Agent(subagent_type="Explore", prompt="Find how X works in /path/to/reference/")
```

**Web search for current docs/patterns:**
```
WebSearch(query="mariadb vector python insert example 2026")
```

**Read a specific doc page:**
```
WebFetch(url="https://mariadb.com/kb/en/vector-overview/")
```

**Parallel research team for complex decisions:**
```
Launch 3 Agent tools simultaneously:
  Agent 1: Research option A
  Agent 2: Research option B
  Agent 3: Check winner reference implementations
```

**TOON spec questions — always read the source:**
```
Read /Users/sunfl/Documents/study/MSrag/references/p0-core/toon-spec/SPEC.md
Read /Users/sunfl/Documents/study/MSrag/references/p0-core/toon-official/packages/toon/src/encode/
Check tests/fixtures/toon_spec/ for concrete examples
```

### 3. Test-Driven Development
- The PostToolUse hook auto-runs RELEVANT tests based on which file you edited:
  - Edit `src/seamless_rag/toon/*` → runs `test_toon_encoder.py` + `test_toon_properties.py`
  - Edit `src/seamless_rag/benchmark/*` → runs `test_token_benchmark.py`
  - Edit `src/seamless_rag/pipeline/*` → runs `test_rag_pipeline.py`
  - Edit `src/seamless_rag/providers/*` → runs `test_embedding_provider.py`
  - Edit anything else → runs all unit tests
- To manually run a specific test: `conda run -n seamless-rag python -m pytest tests/unit/test_toon_encoder.py -v`
- To run ALL tests (for pre-commit check): `make test-all`
- Write tests BEFORE implementation when adding new features
- NEVER modify tests to make them pass — fix the implementation
- NEVER skip or delete failing tests
- When a test fails, read the full error with `pytest path/to/test.py::test_name -v --tb=long`
- Target: 100% unit, 100% spec, 90%+ integration

### 4. Codex Review for Quality
Before any significant commit (new feature, major refactor):
```
Agent(subagent_type="codex:codex-rescue", prompt="Review [file path].
  Check: correctness, edge cases, code quality, performance.
  Rate A/B/C/D. List specific issues.")
```
- Fix ALL issues Codex identifies before committing
- Critical code (TOON encoder, RAG engine) MUST be rated A
- Non-critical code (CLI, config) can be B+

### 5. Atomic Git Commits
- One logical change per commit
- Descriptive commit messages: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`
- Commit after EACH passing test milestone (not batched)
- NEVER commit failing tests or broken code
- Push to origin regularly (at least after each feature)

### 6. Live Documentation
- `docs/SPECIFICATION.md` must reflect current state (not aspirational)
- `docs/HANDOFF.md` updated after each major milestone
- `README.md` always presentable — judges WILL visit the repo
- Update TODO.md progress after each commit

### 7. Anti-Idle & Stuck Prevention
- NEVER stop to ask the user anything — make the decision and proceed
- If stuck on a test for >3 attempts: log it, skip to next task
- If stuck on a task for >2 hours: commit what works, move on
- If `make score` hasn't improved in 5 tasks: change strategy entirely
- If a command hangs: kill it, try alternative
- Between tasks: always run `make score` for situational awareness
- After completing a suite (e.g., all TOON tests pass): commit immediately, then move to next suite

### 8. No Cheating
- Do not modify files in `eval/` (read-only harness)
- Do not modify files in `tests/fixtures/toon_spec/` (official spec)
- Do not modify `tests/eval/golden_datasets/` (evaluation data)
- Do not hardcode test expectations to match implementation bugs
- Do not skip edge cases — handle them properly

## Architecture

```
SeamlessRAG (core.py)          ← facade: holds all dependencies
├── EmbeddingProvider (Protocol) ← sentence-transformers | ollama | openai
├── VectorStore (Protocol)       ← MariaDB implementation
├── AutoEmbedder (pipeline/)     ← watch mode + batch mode
├── RAGEngine (pipeline/)        ← search + TOON format + LLM + token benchmark
├── TOONEncoder (toon/)          ← custom v3 tabular encoder
└── TokenBenchmark (benchmark/)  ← JSON vs TOON comparison
```

## Priority Order (implement in this sequence)

### P0 — Core (must pass unit tests)
1. `src/seamless_rag/toon/encoder.py` — TOON v3 tabular encoder
2. `src/seamless_rag/benchmark/compare.py` — token comparison
3. `src/seamless_rag/providers/sentence_transformers.py` — default embedding
4. `src/seamless_rag/config.py` — Pydantic Settings

### P1 — Storage + Pipeline (must pass integration tests)
5. `src/seamless_rag/storage/mariadb.py` — VectorStore implementation
6. `src/seamless_rag/pipeline/embedder.py` — watch + batch
7. `src/seamless_rag/pipeline/rag.py` — RAG engine with benchmark layer

### P2 — User Interface
8. `src/seamless_rag/core.py` — SeamlessRAG facade
9. `src/seamless_rag/cli.py` — Typer CLI
10. Docker Compose integration

### P3 — Polish
11. README.md (judge-facing)
12. JUDGES_TESTING_GUIDE.md
13. Demo script + recording
14. Optional: Gradio web UI

## Key Technical Decisions

- TOON tabular header format: `[N,]{field1,field2}:` (comma in brackets for tabular)
- Vector insert: `array.array('f', embedding)` via native binary protocol
- Vector read: `array.array('f').frombytes(raw_bytes)`
- Search SQL: `VEC_DISTANCE_COSINE(embedding, ?) ... ORDER BY distance LIMIT ?`
- Default embedding: all-MiniLM-L6-v2 (384d, local, free)
- HNSW tuning: `SET mhnsw_ef_search = 100` for demo

## Reference Materials

Located at `/Users/sunfl/Documents/study/MSrag/references/`:
- `FINAL_SPECIFICATION.md` — comprehensive spec with all technical details
- `p0-core/toon-spec/SPEC.md` — TOON v3 normative specification
- `p0-core/toon-official/packages/toon/src/encode/` — TypeScript reference encoder
- `p1-reference/yt-semantic-search-winner/` — winner architecture reference
- `p1-reference/adaptive-query-optimizer-winner/` — winner judge strategy reference
