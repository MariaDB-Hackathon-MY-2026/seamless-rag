# Judges' Testing Guide — Seamless-RAG

> **For evaluators of the MariaDB Hackathon MY 2026 Innovation Track submission.**
> This guide gives you four progressively deeper ways to verify the project — pick the one that fits your time budget.

If anything below fails, please open an issue or email `TP085412@mail.apu.edu.my` — we'll patch it within hours.

---

## TL;DR — Quickest Verification (90 seconds, no install)

```bash
git clone https://github.com/SunflowersLwtech/seamless-rag.git
cd seamless-rag
docker compose up -d --wait
docker compose exec app seamless-rag demo
```

You will see (against a real MariaDB 11.8 container):
- Schema initialised (documents + chunks + VECTOR(384) + HNSW index)
- 3 sample documents embedded with a local sentence-transformers model
- 3 RAG queries answered, each with a side-by-side **JSON vs TOON token panel**

No API keys required. Local model downloads on first run (~90 MB).

---

## Evaluation Path 1 — Inspect-Only (no setup, 5 minutes)

If you don't want to run anything, the repository ships with everything needed to verify our claims by reading.

| What to read | Why |
|---|---|
| [Project overview (rendered home page)](https://mariadb-hackathon-my-2026.github.io/seamless-rag/) | One-page problem/solution, install matrix, MariaDB features used |
| [Benchmark — real public datasets](https://mariadb-hackathon-my-2026.github.io/seamless-rag/BENCHMARK_REAL_DATA/) | TOON vs JSON token savings on **MovieLens** and **SF Restaurant** — not synthetic |
| [Architecture](https://mariadb-hackathon-my-2026.github.io/seamless-rag/ARCHITECTURE/) | Component diagram, data flow, design decisions |
| [CLI Test Report](https://mariadb-hackathon-my-2026.github.io/seamless-rag/CLI_TEST_REPORT/) | Every CLI command exercised end-to-end with output |
| [`eval/results.tsv`](eval/results.tsv) | Reproducible quality history — every score-run appended |
| `tests/fixtures/toon_spec/` | 358 official TOON v3 conformance fixtures we pass |

---

## Evaluation Path 2 — Docker (recommended, 5 minutes)

**Prerequisite:** Docker Desktop (or Docker Engine + Compose v2). No Python install needed on the host.

```bash
git clone https://github.com/SunflowersLwtech/seamless-rag.git
cd seamless-rag

# Start MariaDB 11.8 + app container
docker compose up -d --wait

# Sanity check — tables and connection
docker compose exec app seamless-rag init

# End-to-end demo: ingest → embed → ask → token panel
docker compose exec app seamless-rag demo
```

**Expected output highlights:**
```
Token & Cost Comparison (GPT-4o pricing)
┏━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Format  ┃ Tokens ┃       Est. Cost ┃
┡━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ JSON    │    158 │       $0.000395 │
│ TOON    │    137 │       $0.000343 │
│ Savings │  13.3% │ $0.000052/query │
└─────────┴────────┴─────────────────┘
```

**Tear-down:**
```bash
docker compose down -v
```

---

## Evaluation Path 3 — Local Python (10 minutes)

Use this if you want to step through the code or run individual CLI commands.

### 3a. Install

```bash
git clone https://github.com/SunflowersLwtech/seamless-rag.git
cd seamless-rag

# Pick ONE of:
pip install -e ".[mariadb,embeddings]"           # standard
uv pip install -e ".[mariadb,embeddings]"        # 10-100x faster (Astral uv)
pipx install "seamless-rag[mariadb,embeddings]"  # isolated CLI
```

Requires Python 3.10+. The `mariadb` extra needs the MariaDB Connector/C library installed system-wide (`brew install mariadb-connector-c` on macOS, `apt install libmariadb-dev` on Debian/Ubuntu).

### 3b. Start MariaDB only

```bash
docker compose -f docker-compose.test.yml up -d --wait
export MARIADB_DATABASE=test_seamless_rag MARIADB_PASSWORD=seamless
```

### 3c. Walk the CLI

```bash
seamless-rag --help          # see every command
seamless-rag init            # create schema
seamless-rag demo            # full end-to-end (ingest + 3 questions)
seamless-rag benchmark       # TOON vs JSON on canned data
seamless-rag export "SELECT id, title FROM documents"   # any SQL → TOON
```

---

## Evaluation Path 4 — Run the test suite (15 minutes)

This is how we measure the project ourselves. The score dashboard is the same one we run in CI.

```bash
# One-shot: lint + unit + spec + properties + integration + eval
make score

# Or break it down:
make test-unit          # 335 tests, no Docker, no API keys
make test-spec          # 166 official TOON v3 conformance fixtures
make test-props         # 12 hypothesis property-based tests
make test-integration   # 10 tests against a real MariaDB container
make lint               # ruff
```

**Expected dashboard** (verbatim from the latest run):

```
==================================================
  Seamless-RAG Quality Score Dashboard
==================================================
Overall: 100.0% (525/525 passed)
--------------------------------------------------
  lint            [####################] 100.0% (1/1)   PASS
  unit            [####################] 100.0% (335/335) PASS
  spec            [####################] 100.0% (166/166) PASS
  props           [####################] 100.0% (12/12)  PASS
  integration     [####################] 100.0% (10/10)  PASS
  eval            [####################] 100.0% (1/1)   PASS
--------------------------------------------------
All targets met!
```

The integration suite needs `docker compose -f docker-compose.test.yml up -d --wait` first; `make test-integration` does this automatically.

---

## What to Look For — Judging Rubric Alignment

| Hackathon Criterion | Where to verify | Concrete artefact |
|---|---|---|
| **Innovation** | `README.md` "Why" section, `docs/ARCHITECTURE.md` | First TOON-native RAG toolkit for MariaDB; both vector and text-to-SQL paths bridged to LLMs |
| **MariaDB integration** | `tests/integration/test_vector_operations.py`, `src/seamless_rag/storage/mariadb.py` | Native VECTOR(N), VEC_DISTANCE_COSINE, HNSW index, CTE context windowing, `array.array('f')` binary protocol |
| **Code quality** | `make score` | 100% lint, 335 unit tests, 100% TOON v3 spec conformance, hypothesis property tests |
| **Real performance** | `docs/BENCHMARK_REAL_DATA.md` | 20–40% token savings on MovieLens + SF Restaurant **public** datasets |
| **Judge friction** | This guide + Docker Compose | First query under 5 minutes, no API key required |
| **Documentation** | `mkdocs.yml`, `docs/` | Full API ref, getting-started, providers, CLI report, benchmark methodology |
| **Tests** | `tests/` | 525 total — unit/spec/property/integration/eval, all passing in CI |

---

## Optional — Live LLM Answers

The demo and `seamless-rag ask` work without an LLM (they show retrieval + token panel only). For live answer generation you can plug in any of:

```bash
export OPENAI_API_KEY=...      # or
export EMBEDDING_API_KEY=...   # Google Gemini
# Ollama needs no key — just `ollama serve` running on localhost
```

The code under `src/seamless_rag/llm/` and `src/seamless_rag/providers/` exposes the same Protocol so you can swap providers via env var without code changes.

---

## Optional — Web UI

```bash
seamless-rag web
# opens http://127.0.0.1:7860 — Gradio interface for live queries
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `mariadb: command not found` (Python install) | `brew install mariadb-connector-c` (macOS) or `apt install libmariadb-dev` (Debian) before `pip install` |
| `Connection refused` on port 3306 | Wait for `docker compose ... --wait` to finish; the healthcheck takes ~10s after first pull |
| Lint failure on `make score` | `conda activate seamless-rag && ruff check src/ tests/` to see specifics |
| `sentence-transformers` first run is slow | One-time download of `all-MiniLM-L6-v2` (~90 MB). Cached for subsequent runs. |
| Integration tests skipped | `docker compose -f docker-compose.test.yml ps` — container must be `healthy` |

---

## Demo Video

A 2–3 minute screencast walking through Paths 2 and 4 lives at [`docs/assets/demo.mp4`](docs/assets/demo.mp4) (also linked from README).

---

## Contact

| | |
|---|---|
| **Author** | Wei Liu (LiuWei) |
| **University** | Asia Pacific University of Technology & Innovation (APU) |
| **Email** | TP085412@mail.apu.edu.my |
| **GitHub** | [SunflowersLwtech](https://github.com/SunflowersLwtech) |

Thank you for evaluating Seamless-RAG.
