"""
TOON spec conformance tests — run against official toon-format/spec fixtures.

These fixtures are the ground truth. The encoder must match them exactly.
Download fixtures with: make fetch-toon-fixtures
"""
import json
from pathlib import Path

import pytest

from seamless_rag.toon.encoder import encode

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "toon_spec"


def _load_fixtures(subdir: str) -> list[tuple[str, dict]]:
    """Load all fixture files from encode/ or decode/ directory."""
    fixture_dir = FIXTURES_DIR / subdir
    if not fixture_dir.exists():
        return []

    fixtures = []
    for f in sorted(fixture_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        for test in data.get("tests", []):
            test_id = f"{f.stem}::{test.get('name', 'unnamed')}"
            fixtures.append((test_id, test))
    return fixtures


# ============================================================
#  Encode conformance
# ============================================================

_encode_fixtures = _load_fixtures("encode")

if _encode_fixtures:
    @pytest.mark.spec
    @pytest.mark.parametrize(
        "name,case",
        _encode_fixtures,
        ids=[f[0] for f in _encode_fixtures],
    )
    def test_encode_spec_conformance(name: str, case: dict):
        """Verify encoder output matches official TOON spec fixture."""
        if case.get("shouldError"):
            with pytest.raises(Exception):
                encode(case["input"], case.get("options", {}))
        else:
            result = encode(case["input"], case.get("options", {}))
            expected = case["expected"]
            assert result == expected, (
                f"Spec fixture '{name}' failed.\n"
                f"Input:    {json.dumps(case['input'])[:200]}\n"
                f"Expected: {expected[:200]}\n"
                f"Got:      {result[:200]}"
            )
else:
    @pytest.mark.spec
    def test_encode_fixtures_exist():
        """Verify TOON spec fixtures are downloaded."""
        pytest.skip(
            "TOON spec fixtures not found. Run 'make fetch-toon-fixtures' to download."
        )


# ============================================================
#  Tabular-specific fixtures (our primary use case)
# ============================================================

_tabular_fixtures = [
    (name, case)
    for name, case in _load_fixtures("encode")
    if "tabular" in name.lower()
]

if _tabular_fixtures:
    @pytest.mark.spec
    @pytest.mark.parametrize(
        "name,case",
        _tabular_fixtures,
        ids=[f[0] for f in _tabular_fixtures],
    )
    def test_tabular_spec_conformance(name: str, case: dict):
        """Verify tabular encoding matches official spec fixtures."""
        if not case.get("shouldError"):
            result = encode(case["input"], case.get("options", {}))
            assert result == case["expected"], f"Tabular fixture '{name}' failed"
