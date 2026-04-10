"""
Snapshot tests for TOON encoder output stability.

Locks down canonical output format. Any refactor that silently changes
the wire format will break these tests.

Update snapshots: pytest --snapshot-update
"""
import pytest

from seamless_rag.toon.encoder import encode_tabular

CANONICAL_FIXTURES = {
    "rag_search_results": [
        {"id": 1, "content": "Climate change affects biodiversity", "distance": 0.12},
        {"id": 2, "content": "Recent studies show temperature rise", "distance": 0.18},
        {"id": 3, "content": "Ocean acidification impacts marine life", "distance": 0.25},
    ],
    "single_result": [
        {"id": 42, "content": "The answer to everything", "distance": 0.001},
    ],
    "with_nulls": [
        {"id": 1, "title": "Climate Report", "author": None, "score": 0.95},
        {"id": 2, "title": "Ocean Study", "author": "Smith", "score": 0.88},
    ],
    "with_special_chars": [
        {"id": 1, "text": 'He said "hello, world"', "active": True},
        {"id": 2, "text": "line1\nline2", "active": False},
    ],
    "numeric_edge_cases": [
        {"id": 1, "int_val": 0, "float_val": 1.5, "neg": -42},
        {"id": 2, "int_val": 1000000, "float_val": 0.001, "neg": -0.0},
    ],
    "empty_and_keyword_strings": [
        {"id": 1, "val": "", "kw": "true", "nl": "null"},
        {"id": 2, "val": "normal", "kw": "false", "nl": "hello"},
    ],
}


@pytest.mark.parametrize("name", CANONICAL_FIXTURES.keys())
def test_toon_output_snapshot(name, snapshot):
    """TOON output must match stored snapshot."""
    data = CANONICAL_FIXTURES[name]
    result = encode_tabular(data)
    assert result == snapshot
