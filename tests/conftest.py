"""
Root conftest.py — shared fixtures and quality scoring plugin.

This file is automatically loaded by pytest for ALL test suites.
"""
from pathlib import Path

import pytest

SCORE_FILE = Path(__file__).parent.parent / ".test-scores.json"


# ============================================================
#  Auto-apply markers based on directory
# ============================================================

def pytest_collection_modifyitems(config, items):
    """Auto-apply markers based on test file location."""
    for item in items:
        rel = Path(item.fspath).relative_to(Path(__file__).parent)
        parts = rel.parts

        if "unit" in parts:
            item.add_marker(pytest.mark.unit)
        if "integration" in parts:
            item.add_marker(pytest.mark.integration)
        if "eval" in parts:
            item.add_marker(pytest.mark.eval)

        # Auto-mark spec and props tests
        if "test_toon_spec_fixtures" in item.nodeid:
            item.add_marker(pytest.mark.spec)
        if "test_toon_properties" in item.nodeid:
            item.add_marker(pytest.mark.props)


# ============================================================
#  Quality score summary (printed after every test run)
# ============================================================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print quality score summary after test run."""
    stats = terminalreporter.stats
    passed = len(stats.get("passed", []))
    failed = len(stats.get("failed", []))
    errors = len(stats.get("error", []))
    total = passed + failed + errors

    if total == 0:
        return

    score = (passed / total) * 100

    # Categorize by directory
    categories = {}
    for status_key in ("passed", "failed", "error"):
        for report in stats.get(status_key, []):
            fspath = str(report.fspath)
            cat = "other"
            if "/unit/" in fspath:
                cat = "unit"
            elif "/integration/" in fspath:
                cat = "integration"
            elif "/eval/" in fspath:
                cat = "eval"

            if cat not in categories:
                categories[cat] = {"passed": 0, "total": 0}
            categories[cat]["total"] += 1
            if status_key == "passed":
                categories[cat]["passed"] += 1

    terminalreporter.section("Seamless-RAG Quality Score")
    terminalreporter.write_line(f"Overall: {score:.1f}% ({passed}/{total} passed)")

    for cat in ("unit", "integration", "eval", "other"):
        if cat in categories:
            c = categories[cat]
            pct = (c["passed"] / c["total"] * 100) if c["total"] > 0 else 0
            bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
            terminalreporter.write_line(f"  {cat:15s} [{bar}] {pct:.0f}% ({c['passed']}/{c['total']})")
