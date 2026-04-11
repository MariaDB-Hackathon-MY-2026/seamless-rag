# Real-World Benchmark: JSON vs TOON Token Savings

> Measured on real public datasets, not synthetic data.
> Date: 2026-04-11 | Tokenizer: tiktoken cl100k_base | Cost model: GPT-4o $2.50/1M input tokens

## Datasets

| Dataset | Source | Rows | Columns | Domain |
|---------|--------|------|---------|--------|
| **MovieLens ml-latest-small** | [GroupLens](https://grouplens.org/datasets/movielens/) | 9,742 movies | 7 (id, title, genres, year, rating, count, tags) | Entertainment |
| **SF Restaurant Health Scores** | [DataSF](https://data.sfgov.org/Health-and-Social-Services/Restaurant-Scores-LIVES-Standard/pyih-qa8i) | 53,973 inspections | 9 (name, address, zip, date, score, type, violation, risk, neighborhood) | Public Health |

## Key Findings

### Token Savings Summary

| Dataset | Query Type | Rows | JSON Tokens | TOON Tokens | Savings |
|---------|-----------|------|-------------|-------------|---------|
| MovieLens | Full columns | 50 | 3,684 | 2,938 | **20.2%** |
| MovieLens | Metadata only (numeric) | 100 | 2,258 | 1,364 | **39.6%** |
| MovieLens | Filtered (Comedy 2000s) | 50 | 2,413 | 1,544 | **36.0%** |
| Restaurant | Full columns | 50 | 3,482 | 2,132 | **38.8%** |
| Restaurant | High risk violations | 50 | 3,437 | 2,076 | **39.6%** |
| Restaurant | Metadata (4 cols) | 100 | 3,147 | 2,036 | **35.3%** |

**Takeaway**: TOON saves **20-40% tokens** on real structured data. Savings are highest on metadata-heavy queries (short values, many columns) and lowest on text-heavy content (long tag strings).

## Detailed Results

### MovieLens

| Query | Rows | JSON tok | TOON tok | Savings | JSON cost | TOON cost |
|-------|------|----------|----------|---------|-----------|-----------|
| Top 10 rated (7 cols) | 10 | 695 | 559 | 19.6% | $0.0017 | $0.0014 |
| Top 20 rated (7 cols) | 20 | 1,339 | 1,050 | 21.6% | $0.0033 | $0.0026 |
| Top 50 rated (7 cols) | 50 | 3,684 | 2,938 | 20.2% | $0.0092 | $0.0073 |
| Top 100 rated (7 cols) | 100 | 6,540 | 5,019 | 23.3% | $0.0163 | $0.0125 |
| Top 200 rated (7 cols) | 200 | 11,817 | 8,749 | 26.0% | $0.0295 | $0.0219 |
| ID+title+rating (3 cols) | 50 | 1,263 | 965 | 23.6% | $0.0032 | $0.0024 |
| Metadata: ID+year+rating+count (4 cols) | 100 | 2,258 | 1,364 | **39.6%** | $0.0056 | $0.0034 |
| Comedy 2000s (7 cols) | 50 | 2,413 | 1,544 | **36.0%** | $0.0060 | $0.0039 |
| Text-heavy tags (7 cols) | 49 | 4,668 | 3,940 | 15.6% | $0.0117 | $0.0098 |

### Restaurant Inspections

| Query | Rows | JSON tok | TOON tok | Savings | JSON cost | TOON cost |
|-------|------|----------|----------|---------|-----------|-----------|
| 10 low-score (9 cols) | 10 | 689 | 438 | 36.4% | $0.0017 | $0.0011 |
| 20 low-score (9 cols) | 20 | 1,405 | 873 | 37.9% | $0.0035 | $0.0022 |
| 50 low-score (9 cols) | 50 | 3,482 | 2,132 | **38.8%** | $0.0087 | $0.0053 |
| 100 violations (9 cols) | 100 | 7,071 | 4,326 | **38.8%** | $0.0177 | $0.0108 |
| 200 violations (9 cols) | 200 | 14,140 | 8,625 | **39.0%** | $0.0353 | $0.0216 |
| Name+score+violation (3 cols) | 50 | 1,324 | 867 | 34.5% | $0.0033 | $0.0022 |
| High risk only (9 cols) | 50 | 3,437 | 2,076 | **39.6%** | $0.0086 | $0.0052 |
| Metadata (4 cols) | 100 | 3,147 | 2,036 | 35.3% | $0.0079 | $0.0051 |

## Scaling: How Savings Grow with Row Count

### MovieLens (7 columns)

| Rows | JSON Tokens | TOON Tokens | Savings % | Bytes Saved |
|------|-------------|-------------|-----------|-------------|
| 5 | 255 | 194 | 23.9% | 299 |
| 10 | 632 | 495 | 21.7% | 659 |
| 20 | 1,190 | 900 | 24.4% | 1,365 |
| 50 | 3,391 | 2,644 | 22.0% | 3,501 |
| 100 | 6,306 | 4,789 | 24.1% | 7,064 |
| 200 | 11,646 | 8,578 | 26.3% | 14,218 |
| 500 | 26,674 | 18,927 | **29.0%** | 35,638 |

### Restaurant Inspections (9 columns)

| Rows | JSON Tokens | TOON Tokens | Savings % | Bytes Saved |
|------|-------------|-------------|-----------|-------------|
| 5 | 361 | 251 | 30.5% | 709 |
| 10 | 723 | 473 | 34.6% | 1,563 |
| 20 | 1,431 | 905 | 36.8% | 3,273 |
| 50 | 3,541 | 2,190 | 38.2% | 8,403 |
| 100 | 7,071 | 4,326 | 38.8% | 16,952 |
| 200 | 14,140 | 8,625 | 39.0% | 34,052 |
| 500 | 35,663 | 21,787 | **38.9%** | 85,330 |

**Pattern**: Savings increase with row count and stabilize around the dataset's natural ceiling. More columns with shorter values = higher savings.

## Agent Workflow Simulation

A typical AI agent queries a database at each reasoning step. Over a 20-step workflow (50 rows per query):

### MovieLens (7 columns)

| Format | Total Tokens | Total Cost | Savings |
|--------|-------------|------------|---------|
| JSON | 73,680 | $0.1842 | - |
| TOON | 58,760 | $0.1469 | **14,920 tokens / $0.037** |

### Restaurant (9 columns)

| Format | Total Tokens | Total Cost | Savings |
|--------|-------------|------------|---------|
| JSON | 69,640 | $0.1741 | - |
| TOON | 42,640 | $0.1066 | **27,000 tokens / $0.068** |

At scale (1000 queries/day), the restaurant dataset alone would save **~540K tokens/day** ($1.35/day, ~$40/month).

## What Drives the Difference

| Factor | Effect on Savings | Why |
|--------|------------------|-----|
| More columns | Higher savings | TOON writes field names once; JSON repeats per row |
| Short values | Higher savings | Structure overhead dominates content |
| More rows | Higher savings (to a ceiling) | Fixed header cost amortized over more rows |
| Long text values | Lower savings | Content tokens dominate, structure is small fraction |
| Numeric-only data | Highest savings (35-40%) | Minimal content, maximum structural redundancy |
| Mixed text+numeric | Moderate savings (20-30%) | Balanced content and structure |

## Side-by-Side Example

### JSON (207 tokens, 653 bytes)

```json
[{"movie_id":318,"title":"Shawshank Redemption, The (1994)","genres":"Crime, Drama","year":1994,"avg_rating":4.43,"num_ratings":317},{"movie_id":858,"title":"Godfather, The (1972)","genres":"Crime, Drama","year":1972,"avg_rating":4.29,"num_ratings":192},{"movie_id":2959,"title":"Fight Club (1999)","genres":"Action, Crime, Drama, Thriller","year":1999,"avg_rating":4.27,"num_ratings":218},{"movie_id":1221,"title":"Godfather: Part II, The (1974)","genres":"Crime, Drama","year":1974,"avg_rating":4.26,"num_ratings":129},{"movie_id":48516,"title":"Departed, The (2006)","genres":"Crime, Drama, Thriller","year":2006,"avg_rating":4.25,"num_ratings":107}]
```

### TOON (157 tokens, 396 bytes) — 24.2% fewer tokens

```
[5,]{movie_id,title,genres,year,avg_rating,num_ratings}:
  318,"Shawshank Redemption, The (1994)","Crime, Drama",1994,4.43,317
  858,"Godfather, The (1972)","Crime, Drama",1972,4.29,192
  2959,Fight Club (1999),"Action, Crime, Drama, Thriller",1999,4.27,218
  1221,"Godfather: Part II, The (1974)","Crime, Drama",1974,4.26,129
  48516,"Departed, The (2006)","Crime, Drama, Thriller",2006,4.25,107
```

### JSON (165 tokens, 756 bytes)

```json
[{"business_name":"Lollipot","inspection_score":45,"violation_description":"Unclean or degraded floors walls or ceilings","risk_category":"Low Risk"},{"business_name":"Lollipot","inspection_score":45,"violation_description":"Improper thawing methods","risk_category":"Moderate Risk"},{"business_name":"Lollipot","inspection_score":45,"violation_description":"High risk food holding temperature","risk_category":"High Risk"},{"business_name":"Lollipot","inspection_score":45,"violation_description":"Unclean or unsanitary food contact surfaces","risk_category":"High Risk"},{"business_name":"Lollipot","inspection_score":45,"violation_description":"Inadequate food safety knowledge or lack of certified food safety manager","risk_category":"Moderate Risk"}]
```

### TOON (119 tokens, 423 bytes) — 27.9% fewer tokens

```
[5,]{business_name,inspection_score,violation_description,risk_category}:
  Lollipot,45,Unclean or degraded floors walls or ceilings,Low Risk
  Lollipot,45,Improper thawing methods,Moderate Risk
  Lollipot,45,High risk food holding temperature,High Risk
  Lollipot,45,Unclean or unsanitary food contact surfaces,High Risk
  Lollipot,45,Inadequate food safety knowledge or lack of certified food safety manager,Moderate Risk
```

## Methodology

- **Tokenizer**: tiktoken `cl100k_base` (GPT-4o tokenizer)
- **JSON encoding**: `json.dumps(data, separators=(",", ":"))` — compact, no whitespace
- **TOON encoding**: Seamless-RAG `encode_tabular()` — TOON v3 tabular format
- **Cost model**: GPT-4o input pricing at $2.50 per 1M tokens
- **Data**: Real query results from MariaDB, not synthetic
- **Reproducibility**: Raw results saved in `datasets/benchmark_results.json`; import script in `datasets/import_datasets.py`
