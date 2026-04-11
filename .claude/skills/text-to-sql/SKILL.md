---
name: text-to-sql
description: "Convert natural language questions into SQL, execute against MariaDB, and return results in TOON format. Use when the user asks a data question that needs a precise SQL query — revenue reports, aggregations, filtered lookups, JOINs — rather than semantic/vector search. Works with any MariaDB database the user has access to."
---

# Text-to-SQL Agent Skill

Turn natural language into SQL → execute → return TOON-formatted results.

This skill is the **precise query** complement to `seamless-rag ask` (semantic search). Use this when the user's question maps to exact SQL — numbers, aggregations, filters, JOINs.

```
User: "What's the average rating of comedy movies from the 2000s?"
  ↓
Agent: inspect schema → generate SQL → execute via seamless-rag export → TOON result
```

## When to Use This vs `seamless-rag ask`

| Signal | Use text-to-sql | Use `seamless-rag ask` |
|--------|----------------|----------------------|
| Numbers, aggregations | "average revenue", "count of", "top 10 by" | - |
| Exact filters | "where price > 100", "in Q3 2025" | - |
| JOINs, GROUP BY | "revenue by region" | - |
| Fuzzy / semantic | - | "movies similar to Inception" |
| Hybrid | Generate SQL with WHERE, pass to `ask --where` | `ask "query" --where "price < 50"` |

## Workflow

### Step 1: Discover schema

```bash
# List databases
conda run -n seamless-rag python -c "
import mariadb
conn = mariadb.connect(host='127.0.0.1', port=3306, user='root', password='seamless')
cur = conn.cursor()
cur.execute('SHOW DATABASES')
for row in cur: print(row[0])
cur.close(); conn.close()
"

# List tables in a database
conda run -n seamless-rag python -c "
import mariadb
conn = mariadb.connect(host='127.0.0.1', port=3306, user='root', password='seamless', database='DATABASE_NAME')
cur = conn.cursor()
cur.execute('SHOW TABLES')
for row in cur: print(row[0])
cur.close(); conn.close()
"

# Get table schema
conda run -n seamless-rag python -c "
import mariadb
conn = mariadb.connect(host='127.0.0.1', port=3306, user='root', password='seamless', database='DATABASE_NAME')
cur = conn.cursor()
cur.execute('DESCRIBE TABLE_NAME')
for row in cur: print(f'{row[0]:20s} {row[1]:20s} {row[2] or \"\"}')
cur.close(); conn.close()
"

# Sample data (first 3 rows)
conda run -n seamless-rag seamless-rag --database DATABASE_NAME export "SELECT * FROM TABLE_NAME LIMIT 3"
```

### Step 2: Generate SQL

Given the schema, write a SELECT query. Rules:
- **SELECT only** — never generate INSERT, UPDATE, DELETE, DROP, ALTER
- **Use LIMIT** — always add LIMIT unless the user asks for "all"
- **Validate column names** against the schema — don't guess
- **Use aliases** for readability: `AVG(price) AS avg_price`
- **MariaDB dialect** — use `LIMIT` not `TOP`, backtick identifiers if needed

### Step 3: Execute and return TOON

```bash
conda run -n seamless-rag seamless-rag --database DATABASE_NAME export "YOUR_SQL_HERE"
```

The `export` command:
- Validates the SQL (rejects writes/DDL via sqlglot AST parsing)
- Executes the query
- Converts results to TOON tabular format
- Prints to stdout

### Step 4: Present results

Show the TOON output directly. If the user needs analysis, feed the TOON to your next reasoning step — it's already token-efficient.

## Examples

### Simple aggregation
```
User: "What genres have the highest average rating?"

→ Schema check: movielens.top_movies has (id, title, genres, year, avg_rating, num_ratings, tags)

→ SQL: SELECT genres, ROUND(AVG(avg_rating), 2) AS avg_score, COUNT(*) AS count
       FROM top_movies GROUP BY genres ORDER BY avg_score DESC LIMIT 10

→ Execute: seamless-rag --database movielens export "SELECT genres, ..."
```

### Filtered lookup
```
User: "Show me high-risk restaurant violations in 94110"

→ Schema check: restaurant.violations has (id, business_name, ..., postal_code, ..., risk_category)

→ SQL: SELECT business_name, violation_description, inspection_score
       FROM violations WHERE risk_category = 'High Risk' AND postal_code = '94110'
       ORDER BY inspection_score ASC LIMIT 20

→ Execute: seamless-rag --database restaurant export "SELECT ..."
```

### Multi-table JOIN
```
User: "Which documents have the most chunks?"

→ SQL: SELECT d.title, COUNT(c.id) AS chunk_count
       FROM documents d JOIN chunks c ON c.document_id = d.id
       GROUP BY d.id ORDER BY chunk_count DESC LIMIT 10

→ Execute: seamless-rag --database seamless_rag export "SELECT ..."
```

## Available Databases

Check what's available by running `SHOW DATABASES`. Common ones in this project:

| Database | Tables | Description |
|----------|--------|-------------|
| `seamless_rag` | documents, chunks | Default RAG database (demo data) |
| `movielens` | movies, top_movies | 9.7K movies with ratings and tags |
| `restaurant` | inspections, violations | 54K SF restaurant health inspections |

## Security

The `seamless-rag export` command validates all SQL via sqlglot AST parsing:
- Only SELECT queries are allowed
- INSERT/UPDATE/DELETE/DROP/ALTER are blocked
- Subqueries with writes are blocked
- Dangerous functions (SLEEP, BENCHMARK, LOAD_FILE) are blocked

This means you can safely pass user-influenced queries through `export`.

## Connection Config

Default connection (from `.env` or CLI flags):
- Host: `127.0.0.1`
- Port: `3306`
- User: `root`
- Password: `seamless`

Override with: `seamless-rag --host X --port Y --user Z --password W --database DB export "SQL"`
