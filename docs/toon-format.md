# TOON Format

TOON (Tabular Object-Oriented Notation) v3 is a compact text serialization format designed to reduce token usage when sending structured data to LLMs.

## Why TOON?

When you send query results to an LLM as JSON, every row repeats the same field names:

```json
[{"id": 1, "name": "Alice", "role": "engineer"},
 {"id": 2, "name": "Bob", "role": "designer"}]
```

TOON moves field names into a header, so they appear only once:

```
[2,]{id,name,role}:
  1,Alice,engineer
  2,Bob,designer
```

The savings grow with the number of rows. At 10+ rows, TOON typically saves 40-58% of tokens compared to JSON.

## Format Specification

A TOON tabular document has this structure:

```
[ROW_COUNT,]{field1,field2,...}:
  value1,value2,...
  value1,value2,...
```

- `[N,]` -- Row count in square brackets, followed by a comma
- `{field1,field2}` -- Field names in curly braces
- `:` -- Header terminator
- Each data row is indented with two spaces, values separated by commas

## Escaping Rules

- Commas in values are escaped as `\,`
- Backslashes are escaped as `\\`
- Newlines in values are escaped as `\n`
- Empty values are represented as empty strings (no placeholder)

## Conformance

Seamless-RAG's TOON encoder passes 166/166 official TOON v3 specification test fixtures. The encoder handles all edge cases including nested escaping, empty rows, unicode content, and mixed types.

## Token Comparison

| Rows | JSON tokens | TOON tokens | Savings |
|------|-------------|-------------|---------|
| 2    | 56          | 37          | 34%     |
| 10   | 280         | 131         | 53%     |
| 50   | 1,400       | 588         | 58%     |

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
