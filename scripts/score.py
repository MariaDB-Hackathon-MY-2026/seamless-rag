#!/usr/bin/env python3
"""
Seamless-RAG Quality Score Dashboard.

Runs all test suites and produces a unified quality score.
Inspired by Karpathy's autoresearch single-metric evaluation pattern.
"""
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

RESULTS_FILE = Path(__file__).parent.parent / "eval" / "results.tsv"
SCORE_FILE = Path(__file__).parent.parent / ".test-scores.json"


@dataclass
class SuiteResult:
    name: str
    passed: int
    failed: int
    errors: int
    total: int

    @property
    def pct(self) -> float:
        return (self.passed / self.total * 100) if self.total > 0 else 0.0

    @property
    def bar(self) -> str:
        filled = int(self.pct / 5)
        return "#" * filled + "." * (20 - filled)


def run_suite(name: str, cmd: list[str], timeout: int = 120) -> SuiteResult:
    """Run a test suite and parse results."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent.parent,
        )
        output = result.stdout + result.stderr

        # Parse pytest short summary
        passed = failed = errors = 0
        for line in output.splitlines():
            line = line.strip()
            # Match patterns like "5 passed", "2 failed,", "1 error"
            if "passed" in line or "failed" in line or "error" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    # Strip trailing punctuation (commas, parens)
                    clean = part.rstrip(",)")
                    if clean == "passed" and i > 0:
                        try:
                            passed = int(parts[i - 1].rstrip(",)"))
                        except ValueError:
                            pass
                    elif clean == "failed" and i > 0:
                        try:
                            failed = int(parts[i - 1].rstrip(",)"))
                        except ValueError:
                            pass
                    elif clean in ("error", "errors") and i > 0:
                        try:
                            errors = int(parts[i - 1].rstrip(",)"))
                        except ValueError:
                            pass

        total = passed + failed + errors
        return SuiteResult(name, passed, failed, errors, total)

    except subprocess.TimeoutExpired:
        return SuiteResult(name, 0, 0, 1, 1)
    except Exception:
        return SuiteResult(name, 0, 0, 1, 1)


def run_lint() -> SuiteResult:
    """Run ruff linter and count issues."""
    try:
        result = subprocess.run(
            ["python", "-m", "ruff", "check", "src/", "tests/", "--quiet"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent,
        )
        issues = len([l for l in result.stdout.strip().splitlines() if l.strip()])
        if result.returncode == 0:
            return SuiteResult("lint", 1, 0, 0, 1)
        return SuiteResult("lint", 0, 1, 0, 1)
    except Exception:
        return SuiteResult("lint", 0, 0, 1, 1)


def show_cached() -> int:
    """Print the most recent cached scores without re-running tests."""
    if not SCORE_FILE.exists():
        print(f"No cached scores at {SCORE_FILE}. Run `python scripts/score.py` first.")
        return 1
    data = json.loads(SCORE_FILE.read_text())
    print("=" * 50)
    print("  Seamless-RAG Quality Score Dashboard (cached)")
    print(f"  {data['timestamp']}")
    print("=" * 50)
    print()
    print(f"Overall: {data['overall_pct']:.1f}% ({data['total_passed']}/{data['total_tests']} passed)")
    print("-" * 50)
    for name, suite in data["suites"].items():
        pct = suite["pct"]
        filled = int(pct / 5)
        bar = "#" * filled + "." * (20 - filled)
        status = "PASS" if pct == 100 else ("PARTIAL" if pct > 0 else "FAIL")
        color = "\033[32m" if pct == 100 else ("\033[33m" if pct > 0 else "\033[31m")
        print(f"  {name:15s} [{bar}] {color}{pct:5.1f}\033[0m% ({suite['passed']}/{suite['total']}) {status}")
    print("-" * 50)
    print("\n\033[32mAll targets met!\033[0m" if data["overall_pct"] >= 99 else "")
    return 0


def main():
    if "--cached" in sys.argv:
        sys.exit(show_cached())

    print("=" * 50)
    print("  Seamless-RAG Quality Score Dashboard")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print()

    # -o addopts= clears any global -x from pyproject.toml so we see full results
    override = ["-o", "addopts="]
    suites = [
        ("unit", ["python", "-m", "pytest", "tests/unit", "-q", "--tb=no", "--no-header", "-m", "not slow"] + override),
        ("spec", ["python", "-m", "pytest", "tests/unit/test_toon_spec_fixtures.py", "-q", "--tb=no", "--no-header"] + override),
        ("props", ["python", "-m", "pytest", "tests/unit/test_toon_properties.py", "-q", "--tb=no", "--no-header"] + override),
        ("integration", ["python", "-m", "pytest", "tests/integration", "-q", "--tb=no", "--no-header", "-m", "integration"] + override),
        ("eval", ["python", "-m", "pytest", "tests/eval", "-q", "--tb=no", "--no-header", "-m", "eval"] + override),
    ]

    results: list[SuiteResult] = []

    # Run lint
    lint_result = run_lint()
    results.append(lint_result)

    # Run test suites
    for name, cmd in suites:
        r = run_suite(name, cmd)
        results.append(r)

    # Calculate overall score
    total_passed = sum(r.passed for r in results)
    total_all = sum(r.total for r in results)
    overall_pct = (total_passed / total_all * 100) if total_all > 0 else 0.0

    # Display
    print(f"Overall: {overall_pct:.1f}% ({total_passed}/{total_all} passed)")
    print("-" * 50)

    for r in results:
        status = "PASS" if r.pct == 100 else ("PARTIAL" if r.pct > 0 else "FAIL")
        color = "\033[32m" if r.pct == 100 else ("\033[33m" if r.pct > 0 else "\033[31m")
        reset = "\033[0m"
        print(f"  {r.name:15s} [{r.bar}] {color}{r.pct:5.1f}%{reset} ({r.passed}/{r.total}) {status}")

    print("-" * 50)

    # Targets
    targets = {
        "unit": 100.0,
        "spec": 100.0,
        "props": 95.0,
        "integration": 90.0,
        "eval": 70.0,
        "lint": 100.0,
    }

    missed = []
    for r in results:
        target = targets.get(r.name, 80.0)
        if r.pct < target:
            missed.append(f"  {r.name}: {r.pct:.0f}% < {target:.0f}% target")

    if missed:
        print("\nTargets NOT met:")
        for m in missed:
            print(f"  \033[31m{m}\033[0m")
    else:
        print(f"\n\033[32mAll targets met!\033[0m")

    # Save scores to JSON
    scores = {
        "timestamp": datetime.now().isoformat(),
        "overall_pct": round(overall_pct, 1),
        "total_passed": total_passed,
        "total_tests": total_all,
        "suites": {r.name: {"passed": r.passed, "total": r.total, "pct": round(r.pct, 1)} for r in results},
    }
    SCORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCORE_FILE.write_text(json.dumps(scores, indent=2))

    # Append to results.tsv (autoresearch pattern)
    if RESULTS_FILE.parent.exists():
        header_needed = not RESULTS_FILE.exists()
        with open(RESULTS_FILE, "a") as f:
            if header_needed:
                f.write("timestamp\toverall_pct\tunit\tspec\tprops\tintegration\teval\tstatus\n")
            suite_map = {r.name: r for r in results}
            status = "pass" if not missed else "partial"
            f.write(
                f"{datetime.now().isoformat()}\t"
                f"{overall_pct:.1f}\t"
                f"{suite_map.get('unit', SuiteResult('', 0, 0, 0, 0)).pct:.0f}\t"
                f"{suite_map.get('spec', SuiteResult('', 0, 0, 0, 0)).pct:.0f}\t"
                f"{suite_map.get('props', SuiteResult('', 0, 0, 0, 0)).pct:.0f}\t"
                f"{suite_map.get('integration', SuiteResult('', 0, 0, 0, 0)).pct:.0f}\t"
                f"{suite_map.get('eval', SuiteResult('', 0, 0, 0, 0)).pct:.0f}\t"
                f"{status}\n"
            )

    print(f"\nScores saved to {SCORE_FILE}")
    print(f"History appended to {RESULTS_FILE}")

    sys.exit(0 if not missed else 1)


if __name__ == "__main__":
    main()
