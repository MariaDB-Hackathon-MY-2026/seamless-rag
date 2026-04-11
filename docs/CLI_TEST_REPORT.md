# CLI Test Report

> Tested on real public datasets (MovieLens + SF Restaurant Health Scores)
> Date: 2026-04-12 | MariaDB 11.8 | Gemini embeddings (768d) | Gemini 2.5 Flash LLM

## Test Environment

- **MovieLens**: 500 top-rated movies (title, genres, year, avg_rating, num_ratings, tags)
- **Restaurant**: 500 recent violation records (business_name, address, score, violation_description, risk_category)
- **Embedding**: Gemini gemini-embedding-001 (768d)
- **LLM**: Gemini 2.5 Flash

## CLI Command Test Results

| # | Command | Test | Status | Notes |
|---|---------|------|--------|-------|
| 1 | `--help` | Show all commands and options | PASS | 9 commands, 8 global options displayed |
| 2 | `init` | Create schema (documents + chunks) | PASS | Tables created in seamless_rag DB |
| 3 | `embed` | Bulk-embed MovieLens 500 movies | PASS | 500/500 embedded, multi-column (title,genres) |
| 4 | `embed` | Bulk-embed Restaurant 500 violations | PASS | 500/500 embedded, single-column (violation_description) |
| 5 | `ask` | Semantic search + LLM answer | PASS | Accurate answers with TOON context |
| 6 | `ask --where` | Hybrid filter+vector search | PASS | SQL filter + cosine similarity combined |
| 7 | `ask --mmr` | MMR diversity selection | PASS | Diverse results, lambda tuning works |
| 8 | `export` | SQL query → TOON format | PASS | Clean tabular output |
| 9 | `benchmark` | JSON vs TOON comparison | PASS | 42.5% savings on 30-row synthetic data |
| 10 | `ingest` | Text file → chunks → embed | PASS | Sentence-boundary chunking with overlap |
| 11 | `watch` | Auto-embed new inserts | PASS | Rich live table, poll + checkpoint |
| 12 | `demo` | End-to-end demo | PASS | 3/3 questions answered correctly |

**Result: 12/12 commands PASS**

## RAG Quality Test Results (Batch)

### MovieLens (9 queries)

| Query | Type | Sources | Answer Quality | Savings |
|-------|------|---------|---------------|---------|
| Crime drama like Godfather | Plain | 5 relevant | Godfather II, Goodfellas, Bonnie and Clyde | 21.8% |
| Animated children adventure | Plain | 5 relevant | Emperor's New Groove, Up, Zootopia | 19.7% |
| Existential crisis/meaning of life | Plain | 5 relevant | Meaning of Life, Before Sunrise | 20.4% |
| Classic black and white films | Plain | 5 relevant | Arsenic and Old Lace, African Queen | 19.9% |
| Comedy drama, funny+cry | Plain | 5 relevant | Good bye Lenin, Terms of Endearment | 21.2% |
| Thriller with plot twists (k=3) | top_k=3 | 3 relevant | Memento, Old Boy, Collateral | 14.7% |
| Thriller with plot twists (k=10) | top_k=10 | 10 relevant | Usual Suspects, Memento ranked correctly | 20.2% |
| War movies, human cost (MMR 0.5) | MMR | 5 diverse | Hurt Locker, Life Is Beautiful, Pianist | 18.6% |
| War movies, human cost (MMR 0.3) | MMR high div | 5 diverse | Hurt Locker, Life Is Beautiful, Glory | 18.6% |

**MovieLens: 9/9 PASS** — All answers grounded in retrieved context, correct genre matching.

### Restaurant (7 queries)

| Query | Type | Sources | Answer Quality | Savings |
|-------|------|---------|---------------|---------|
| Cockroach/rodent problems | Plain | 5 | Correctly notes no pest-specific results in top-5 | 27.7% |
| Food temperature violations | Plain | 5 relevant | Matched "Improper food storage" | 30.3% |
| Hand washing/hygiene | Plain | 5 relevant | Matched "handwashing facilities" violations | 27.5% |
| Broken kitchen equipment | Plain | 5 relevant | Matched "unmaintained equipment" | 27.5% |
| Sanitation + score < 70 | Hybrid | 0 | No results (no score < 70 in subset) | N/A |
| Contamination + High Risk | Hybrid | 5 relevant | Sewage contamination, improper gloves | 28.7% |
| Various violations (MMR k=8) | MMR | 8 diverse | HAACP, equipment — diverse categories | 29.8% |

**Restaurant: 6/7 PASS, 1 NO_RESULTS** (expected — no data matched the strict WHERE filter)

### Summary

| Metric | Value |
|--------|-------|
| Total queries | 16 |
| Pass | 15 (93.8%) |
| No results | 1 (expected — strict filter) |
| Errors | 0 |
| Avg token savings | 22.8% (MovieLens), 28.6% (Restaurant) |
| Avg latency | 4.6s (includes Gemini API round-trip) |

## Bugs Found and Fixed

### Bug: `search()` hardcoded `content` column name

**Symptom**: `ask` failed with `Unknown column 'content'` on custom tables.

**Root cause**: `MariaDBVectorStore.search()` hardcoded `SELECT id, content, VEC_DISTANCE_COSINE(...)`. Tables like `top_movies` or `violations` don't have a `content` column.

**Fix**: Dynamic column detection via `SHOW COLUMNS FROM table` — returns all non-VECTOR columns automatically. Also fixed `mmr_search` candidate text extraction in `retrieval.py`.

**Files changed**:
- `src/seamless_rag/storage/mariadb.py` — added `_get_non_vector_columns()`, updated `search()`
- `src/seamless_rag/pipeline/retrieval.py` — improved `_candidate_text()` fallback

**Tests**: All 520+ existing tests still pass after fix.

## Feature Observations

### Strengths
- **Multi-column embed** works well — `--columns "title,genres"` produces semantically rich vectors
- **Hybrid search** (`--where` + vector) is powerful for filtered queries
- **MMR diversity** with `--mmr-lambda` tuning produces noticeably different result sets
- **TOON savings** are consistent: 15-30% on mixed text/structured data
- **LLM answers** are well-grounded — they cite specific movies/restaurants from context

### Improvement Opportunities
- `embed` should auto-detect and create the VECTOR column (currently requires manual `ensure_vector_column`)
- `ask` should accept `--table` option for querying custom tables directly
- Restaurant sources display as empty strings — the display could show the violation_description field
