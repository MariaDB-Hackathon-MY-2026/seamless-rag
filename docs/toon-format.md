# TOON Format

TOON (Tabular Object-Oriented Notation) v3 is a compact text serialization format designed to reduce token usage when sending structured data to LLMs.

## Why TOON?

When you send query results to an LLM as JSON, every row repeats the same field names:

```json
[{"id":1,"name":"Widget","category":"Tools","price":29.99},
 {"id":2,"name":"Gadget","category":"Tools","price":19.99}]
```

TOON moves field names into a header, so they appear only once:

```
[2,]{id,name,category,price}:
  1,Widget,Tools,29.99
  2,Gadget,Tools,19.99
```

The savings grow with row count and stabilize at the dataset's natural ceiling.

## Real-World Token Savings

Measured on real public datasets using tiktoken `cl100k_base` (GPT-4o tokenizer):

| Dataset | Rows | JSON Tokens | TOON Tokens | Savings |
|---------|------|-------------|-------------|---------|
| MovieLens (7 cols) | 10 | 632 | 495 | 21.7% |
| MovieLens (7 cols) | 100 | 6,306 | 4,789 | 24.1% |
| MovieLens (7 cols) | 500 | 26,674 | 18,927 | **29.0%** |
| Restaurant (9 cols) | 10 | 723 | 473 | 34.6% |
| Restaurant (9 cols) | 100 | 7,071 | 4,326 | 38.8% |
| Restaurant (9 cols) | 500 | 35,663 | 21,787 | **38.9%** |

Savings are highest with: many columns, short values, numeric data. Savings are lowest with: long text content, few rows.

## Format Specification

A TOON tabular document has this structure:

```
[ROW_COUNT,]{field1,field2,...}:
  value1,value2,...
  value1,value2,...
```

- `[N,]` — Row count in square brackets, followed by a comma
- `{field1,field2}` — Field names in curly braces
- `:` — Header terminator
- Each data row is indented with two spaces, values separated by commas

## Value Rules

| Type | Example | TOON |
|------|---------|------|
| String | `"Alice"` | `Alice` (unquoted if safe) |
| String with comma | `"Smith, John"` | `"Smith, John"` (quoted) |
| Number | `29.99` | `29.99` (canonical, no scientific notation) |
| Boolean | `true` | `true` |
| Null | `null` | `null` |
| Empty string | `""` | `""` (quoted) |

## Quoting Rules (Section 7.2)

A string value must be quoted when it:

- Contains the delimiter (comma by default)
- Matches a keyword (`true`, `false`, `null`)
- Looks like a number (`123`, `3.14`)
- Has leading/trailing whitespace
- Is empty

## Escape Sequences (Section 7.1)

| Sequence | Meaning |
|----------|---------|
| `\\` | Backslash |
| `\"` | Double quote |
| `\n` | Newline |
| `\r` | Carriage return |
| `\t` | Tab |

## Conformance

Seamless-RAG's TOON encoder passes **166/166** official TOON v3 specification test fixtures, covering: nested escaping, empty rows, unicode content, mixed types, key folding, delimiter options, and number canonicalization.

## Side-by-Side Example

### JSON (207 tokens)

```json
[{"movie_id":318,"title":"Shawshank Redemption, The (1994)","genres":"Crime, Drama","year":1994,"avg_rating":4.43,"num_ratings":317},{"movie_id":858,"title":"Godfather, The (1972)","genres":"Crime, Drama","year":1972,"avg_rating":4.29,"num_ratings":192},{"movie_id":2959,"title":"Fight Club (1999)","genres":"Action, Crime, Drama, Thriller","year":1999,"avg_rating":4.27,"num_ratings":218}]
```

### TOON (157 tokens — 24.2% saved)

```
[3,]{movie_id,title,genres,year,avg_rating,num_ratings}:
  318,"Shawshank Redemption, The (1994)","Crime, Drama",1994,4.43,317
  858,"Godfather, The (1972)","Crime, Drama",1972,4.29,192
  2959,Fight Club (1999),"Action, Crime, Drama, Thriller",1999,4.27,218
```

## Usage

```python
from seamless_rag.toon.encoder import encode_tabular

rows = [
    {"id": 1, "content": "Climate change affects biodiversity", "score": 0.92},
    {"id": 2, "content": "Recent studies show temperature rise", "score": 0.87},
]
print(encode_tabular(rows))
```

Output:

```
[2,]{id,content,score}:
  1,Climate change affects biodiversity,0.92
  2,Recent studies show temperature rise,0.87
```
