---
name: text-to-sql
description: "Translate a natural-language data question into a safe SELECT query against MariaDB and return the result in TOON tabular format (token-efficient context for LLMs/agents). Trigger this skill whenever the user has structured tables in MariaDB and asks a question that maps to precise SQL — revenue/sales reports, top-N rankings, GROUP BY aggregations, exact-value filters, JOINs across tables, counts, averages, percentile-style queries — rather than fuzzy/semantic search. Also trigger when the user explicitly says 'write SQL for…', 'query the DB for…', or hands you a schema and asks a question. Pairs with the seamless-rag skill: this one handles the precise-SQL leg, seamless-rag handles the semantic / vector-search leg, and they combine via `seamless-rag ask … --where` for hybrid queries."
---

# Text-to-SQL Skill

Turn natural language into SQL → execute → return TOON-formatted results.

This skill is the **precise query** complement to `seamless-rag ask` (semantic search). Use this when the user's question maps to exact SQL — numbers, aggregations, filters, JOINs.

```
User: "What's the average rating of comedy movies from the 2000s?"
  ↓
Agent: discover schema → generate SQL → execute via seamless-rag export → TOON result
```

The skill assumes the `seamless-rag` CLI is on the user's PATH (install via `pip install "seamless-rag[mariadb]"`). The CLI is used both for schema introspection and SQL execution because it already enforces safe, SELECT-only access via sqlglot AST validation.

## When to Use This vs `seamless-rag ask`

| Signal | Use **text-to-sql** | Use **seamless-rag ask** |
|--------|---------------------|--------------------------|
| Numbers, aggregations | "average revenue", "count of", "top 10 by" | — |
| Exact filters | "where price > 100", "in Q3 2025" | — |
| JOINs, GROUP BY | "revenue by region" | — |
| Fuzzy / semantic | — | "movies similar to Inception" |
| Hybrid | Generate the SQL, then pass it as a `--where` clause to `seamless-rag ask` | `ask "query" --where "price < 50"` |

## Workflow

### Step 1 — Discover schema

`seamless-rag export` only accepts SELECT queries, but you can read the full MariaDB catalog through `information_schema`, which IS queryable as plain SELECT. Replace `<DB>` with the database the user is targeting and `<TBL>` with the table name.

```bash
# Pick the target database (skip the system schemas)
seamless-rag export "
  SELECT schema_name
  FROM information_schema.schemata
  WHERE schema_name NOT IN ('mysql','information_schema','performance_schema','sys')
  ORDER BY schema_name
"

# List tables and approximate row counts in a database
seamless-rag --database <DB> export "
  SELECT table_name, table_rows
  FROM information_schema.tables
  WHERE table_schema = '<DB>'
  ORDER BY table_rows DESC
"

# Describe a table's columns
seamless-rag --database <DB> export "
  SELECT column_name, data_type, is_nullable, column_key, column_default
  FROM information_schema.columns
  WHERE table_schema = '<DB>' AND table_name = '<TBL>'
  ORDER BY ordinal_position
"

# Sample a few real rows so you see actual values, not just types
seamless-rag --database <DB> export "SELECT * FROM <TBL> LIMIT 3"
```

If the user has set `MARIADB_DATABASE` (env var or `.env`) you can omit `--database` after the first call.

### Step 2 — Generate SQL

Given the schema you just discovered, write a SELECT query. Rules to internalize:

- **SELECT only** — never generate INSERT, UPDATE, DELETE, DROP, ALTER. The CLI rejects them, but generating one wastes a round-trip.
- **Always bound the result** — add a `LIMIT` (typically 10–100) unless the user explicitly asks for "all rows" or for a count/aggregation that returns one row.
- **Validate column names against what you discovered** — don't guess. If the schema didn't surface a column, ask the user.
- **Use aliases for readability** — `AVG(price) AS avg_price`, especially for computed expressions, so the TOON column header is human-readable.
- **MariaDB dialect** — `LIMIT` (not `TOP`), backtick identifiers if they collide with reserved words.

### Step 3 — Execute and return TOON

```bash
seamless-rag --database <DB> export "<your generated SQL>"
```

The `export` command:
- Validates the SQL via sqlglot AST parsing (rejects writes, DDL, dangerous functions, subqueries that hide writes).
- Executes it against MariaDB.
- Streams the result as TOON v3 tabular format on stdout.

### Step 4 — Present results

Return the TOON output directly to the user — it's already token-efficient. If you need to reason over the rows yourself, parse the header line `[N,]{col1,col2,…}:` and treat each indented row as a record with values in column order. See the **seamless-rag** skill for the full TOON read-format reference.

## Examples

### Simple aggregation
```
User: "What genres have the highest average rating?"

→ Discover: <DB>.movies has (id, title, genres, year, avg_rating, num_ratings)

→ SQL:
    SELECT genres,
           ROUND(AVG(avg_rating), 2) AS avg_score,
           COUNT(*)                 AS movie_count
    FROM movies
    GROUP BY genres
    ORDER BY avg_score DESC
    LIMIT 10

→ Execute:
    seamless-rag --database <DB> export "SELECT genres, ROUND(AVG(...))..."
```

### Filtered lookup
```
User: "Show me high-risk restaurant violations in 94110"

→ Discover: <DB>.violations has
    (id, business_name, violation_description, postal_code, risk_category, inspection_score)

→ SQL:
    SELECT business_name, violation_description, inspection_score
    FROM violations
    WHERE risk_category = 'High Risk' AND postal_code = '94110'
    ORDER BY inspection_score ASC
    LIMIT 20

→ Execute:
    seamless-rag --database <DB> export "..."
```

### Multi-table JOIN
```
User: "Which documents have the most chunks?"

→ SQL:
    SELECT d.title, COUNT(c.id) AS chunk_count
    FROM documents d
    JOIN chunks    c ON c.document_id = d.id
    GROUP BY d.id, d.title
    ORDER BY chunk_count DESC
    LIMIT 10

→ Execute:
    seamless-rag --database <DB> export "SELECT d.title, COUNT(c.id) ..."
```

### Hybrid: generate SQL filter, hand off to vector search
```
User: "reliable laptops under $1000"

→ This is hybrid (precise filter + semantic). Generate just the WHERE clause, then
  hand the full question to `seamless-rag ask`:

    seamless-rag --database <DB> ask "reliable laptops" \
      --where "category = 'laptops' AND price < 1000" --top-k 5
```

## Security

The `seamless-rag export` command validates all SQL via sqlglot AST parsing:

- Only top-level SELECT (or UNION/INTERSECT/EXCEPT of SELECTs) is allowed.
- INSERT/UPDATE/DELETE/DROP/ALTER are rejected anywhere in the AST, including inside subqueries.
- `SLEEP`, `BENCHMARK`, `LOAD_FILE`, `INTO_OUTFILE` are rejected.
- Identifier names you pass via `--database` / `--table` must match `^[A-Za-z_][A-Za-z0-9_]*$`.

This means you can pass user-influenced queries through `export` without first sanitizing them yourself — the validator is the trust boundary.

## Connection Configuration

Defaults are read from environment (or a local `.env` file the user loads), in this order:

| Variable | Default |
|----------|---------|
| `MARIADB_HOST` | `127.0.0.1` |
| `MARIADB_PORT` | `3306` |
| `MARIADB_USER` | `root` |
| `MARIADB_PASSWORD` | `seamless` |
| `MARIADB_DATABASE` | `seamless_rag` |

Override per command with CLI flags:

```bash
seamless-rag --host db.example.com --port 3307 --user analyst \
             --password "$DB_PWD" --database analytics \
             export "SELECT ..."
```

If you're not sure where MariaDB is, ask the user. Don't guess.
