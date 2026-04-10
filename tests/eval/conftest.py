"""
RAG evaluation fixtures — golden datasets for quality scoring.
"""
import json
from pathlib import Path

import pytest

GOLDEN_DATASET = Path(__file__).parent / "golden_datasets" / "rag_eval_set.json"


@pytest.fixture(scope="session")
def golden_qa_pairs():
    """Load golden question-answer pairs for RAG evaluation."""
    if not GOLDEN_DATASET.exists():
        pytest.skip("Golden dataset not found")
    data = json.loads(GOLDEN_DATASET.read_text())
    return data["test_cases"]
