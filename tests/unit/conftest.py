"""
Unit test fixtures — Protocol-based mocks, no external dependencies.

All unit tests must pass without:
- Running MariaDB
- Internet access
- API keys
"""
import array
from typing import Protocol, runtime_checkable
from unittest.mock import Mock

import pytest


# ============================================================
#  Protocol definitions (same as production code)
# ============================================================

@runtime_checkable
class EmbeddingProvider(Protocol):
    @property
    def dimensions(self) -> int: ...
    def embed(self, text: str) -> list[float]: ...
    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]: ...


@runtime_checkable
class StorageProtocol(Protocol):
    def insert_embedding(self, table: str, row_id: int, embedding: list[float]) -> None: ...
    def search(self, table: str, query_vec: list[float], top_k: int) -> list[dict]: ...
    def get_new_rows(self, table: str, last_id: int) -> list[dict]: ...


# ============================================================
#  Mock fixtures
# ============================================================

@pytest.fixture
def mock_provider() -> Mock:
    """Mock embedding provider returning deterministic 384-dim vectors."""
    provider = Mock(spec=EmbeddingProvider)
    provider.dimensions = 384
    provider.embed.return_value = [0.1] * 384
    provider.embed_batch.return_value = [[0.1] * 384, [0.2] * 384]
    return provider


@pytest.fixture
def mock_storage() -> Mock:
    """Mock storage returning sample search results."""
    storage = Mock(spec=StorageProtocol)
    storage.search.return_value = [
        {"id": 1, "content": "Climate change affects biodiversity", "distance": 0.12},
        {"id": 2, "content": "Recent studies show temperature rise", "distance": 0.18},
        {"id": 3, "content": "Ocean acidification impacts marine life", "distance": 0.25},
    ]
    storage.get_new_rows.return_value = [
        {"id": 10, "content": "New research published today"},
        {"id": 11, "content": "Another document to embed"},
    ]
    return storage


@pytest.fixture
def sample_search_results() -> list[dict]:
    """Canonical search results for TOON encoding tests."""
    return [
        {"id": 1, "content": "Climate change affects biodiversity", "distance": 0.12},
        {"id": 2, "content": "Recent studies show temperature rise", "distance": 0.18},
        {"id": 3, "content": "Ocean acidification impacts marine life", "distance": 0.25},
    ]


@pytest.fixture
def sample_vector_384() -> array.array:
    """Sample 384-dimensional float32 vector."""
    return array.array("f", [0.1] * 384)


# ============================================================
#  TOON test data
# ============================================================

@pytest.fixture
def toon_tabular_cases() -> dict[str, tuple[list[dict], str]]:
    """Canonical input/output pairs for TOON tabular encoding.

    Returns dict of {name: (input_data, expected_toon_output)}.
    """
    return {
        "single_row": (
            [{"id": 1, "name": "Ada"}],
            "[1,]{id,name}:\n  1,Ada",
        ),
        "multi_row": (
            [
                {"id": 1, "name": "Ada", "score": 95},
                {"id": 2, "name": "Bob", "score": 87},
            ],
            "[2,]{id,name,score}:\n  1,Ada,95\n  2,Bob,87",
        ),
        "with_null": (
            [{"id": 1, "value": None}],
            "[1,]{id,value}:\n  1,null",
        ),
        "with_bool": (
            [{"id": 1, "active": True, "deleted": False}],
            "[1,]{id,active,deleted}:\n  1,true,false",
        ),
        "needs_quoting_comma": (
            [{"id": 1, "name": "Smith, John"}],
            '[1,]{id,name}:\n  1,"Smith, John"',
        ),
        "needs_quoting_colon": (
            [{"id": 1, "time": "12:30:00"}],
            '[1,]{id,time}:\n  1,"12:30:00"',
        ),
        "empty_string": (
            [{"id": 1, "val": ""}],
            '[1,]{id,val}:\n  1,""',
        ),
        "string_looks_like_number": (
            [{"id": 1, "code": "42"}],
            '[1,]{id,code}:\n  1,"42"',
        ),
        "string_looks_like_bool": (
            [{"id": 1, "val": "true"}],
            '[1,]{id,val}:\n  1,"true"',
        ),
        "string_looks_like_null": (
            [{"id": 1, "val": "null"}],
            '[1,]{id,val}:\n  1,"null"',
        ),
        "unicode": (
            [{"id": 1, "text": "Hello world"}],
            "[1,]{id,text}:\n  1,Hello world",
        ),
        "newline_in_value": (
            [{"id": 1, "text": "line1\nline2"}],
            '[1,]{id,text}:\n  1,"line1\\nline2"',
        ),
    }
