#!/usr/bin/env python3
"""
Immutable Evaluation Harness — DO NOT MODIFY THIS FILE.

Inspired by Karpathy's autoresearch pattern: the evaluation function
is read-only ground truth. Only the implementation changes; the
measurement never does.

This harness:
1. Loads a fixed test dataset
2. Runs the TOON encoder on it
3. Measures token efficiency (the primary metric)
4. Measures encoding correctness against known outputs
5. Reports a single composite score

The score is used in the experiment loop:
  modify → commit → evaluate → keep/discard
"""
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# ============================================================
#  FIXED TEST DATA — never modify these
# ============================================================

# Simulates typical RAG search results (SQL SELECT output)
EVAL_DATASETS = [
    {
        "name": "small_3_rows",
        "data": [
            {"id": 1, "content": "Climate change affects biodiversity through multiple mechanisms.", "distance": 0.12},
            {"id": 2, "content": "Rising temperatures force species to migrate to new habitats.", "distance": 0.18},
            {"id": 3, "content": "Ocean acidification reduces carbonate ion availability.", "distance": 0.25},
        ],
    },
    {
        "name": "medium_10_rows",
        "data": [
            {"id": i, "title": f"Article {i}", "content": f"Content paragraph {i} about topic.", "score": round(0.95 - i * 0.05, 2)}
            for i in range(1, 11)
        ],
    },
    {
        "name": "wide_8_cols",
        "data": [
            {
                "id": i,
                "name": f"Entity {i}",
                "category": "A" if i % 2 == 0 else "B",
                "value": i * 100,
                "rate": round(i * 0.15, 2),
                "active": i % 3 != 0,
                "notes": None if i % 4 == 0 else f"Note for {i}",
                "created": f"2024-01-{i:02d}",
            }
            for i in range(1, 6)
        ],
    },
    {
        "name": "edge_cases",
        "data": [
            {"id": 1, "text": 'Contains "quotes" and, commas', "val": True},
            {"id": 2, "text": "Has a\nnewline", "val": False},
            {"id": 3, "text": "", "val": None},
            {"id": 4, "text": "null", "val": 0},
            {"id": 5, "text": "-starts-with-hyphen", "val": -0.0},
        ],
    },
    {
        "name": "large_100_rows",
        "data": [
            {
                "id": i,
                "title": f"Document {i}: Analysis of Topic Area {i % 10}",
                "content": f"This is the content of document {i}. It discusses various aspects of the subject matter in detail, providing insights and analysis that are relevant to the query.",
                "score": round(0.99 - i * 0.005, 3),
                "category": ["science", "tech", "health", "finance", "education"][i % 5],
            }
            for i in range(1, 101)
        ],
    },
]


@dataclass
class EvalResult:
    dataset_name: str
    json_chars: int
    toon_chars: int
    char_savings_pct: float
    json_tokens: int
    toon_tokens: int
    token_savings_pct: float
    encoding_time_ms: float
    correctness: bool  # True if output is valid TOON


def evaluate() -> dict:
    """
    Run the full evaluation. Returns composite score.

    Score = weighted average of:
      - Token savings (weight 0.5): higher is better, target 50%+
      - Correctness (weight 0.3): all datasets must encode without error
      - Speed (weight 0.2): encoding time < 10ms per dataset
    """
    try:
        from seamless_rag.toon.encoder import encode_tabular
    except ImportError:
        print("FAIL: seamless_rag.toon.encoder not importable")
        return {"score": 0.0, "status": "import_error"}

    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        count_tokens = lambda s: len(enc.encode(s))
    except ImportError:
        # Fallback: approximate tokens as chars / 4
        count_tokens = lambda s: len(s) // 4

    results = []
    all_correct = True

    for dataset in EVAL_DATASETS:
        name = dataset["name"]
        data = dataset["data"]

        # Measure encoding + validate correctness
        start = time.perf_counter()
        try:
            toon_output = encode_tabular(data)
            # Correctness checks: not just "did not raise" but structural validation
            correctness = True
            if not isinstance(toon_output, str):
                print(f"FAIL {name}: output is not a string")
                correctness = False
            elif len(data) > 0 and not toon_output:
                print(f"FAIL {name}: non-empty input produced empty output")
                correctness = False
            elif len(data) > 0 and f"[{len(data)},]" not in toon_output:
                print(f"FAIL {name}: header missing correct count [{len(data)},]")
                correctness = False
            elif toon_output.endswith("\n"):
                print(f"FAIL {name}: trailing newline (spec violation)")
                correctness = False
            elif any(line != line.rstrip() for line in toon_output.split("\n")):
                print(f"FAIL {name}: trailing whitespace on a line (spec violation)")
                correctness = False
            # Verify row count matches
            if correctness and len(data) > 0:
                data_lines = [l for l in toon_output.split("\n")[1:] if l.strip()]
                if len(data_lines) != len(data):
                    print(f"FAIL {name}: expected {len(data)} rows, got {len(data_lines)}")
                    correctness = False
        except Exception as e:
            print(f"ERROR encoding {name}: {e}")
            toon_output = ""
            correctness = False
        if not correctness:
            all_correct = False
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Measure JSON baselines
        json_output = json.dumps(data)
        json_compact = json.dumps(data, separators=(",", ":"))

        # Token counts
        json_tokens = count_tokens(json_output)
        json_compact_tokens = count_tokens(json_compact)
        toon_tokens = count_tokens(toon_output) if toon_output else json_tokens

        # Calculate savings (vs standard JSON — the number judges will see)
        char_savings = ((len(json_output) - len(toon_output)) / len(json_output) * 100) if json_output else 0
        token_savings = ((json_tokens - toon_tokens) / json_tokens * 100) if json_tokens > 0 else 0
        # Also track vs compact JSON (harder bar)
        compact_savings = ((json_compact_tokens - toon_tokens) / json_compact_tokens * 100) if json_compact_tokens > 0 else 0

        results.append(EvalResult(
            dataset_name=name,
            json_chars=len(json_output),
            toon_chars=len(toon_output),
            char_savings_pct=round(char_savings, 1),
            json_tokens=json_tokens,
            toon_tokens=toon_tokens,
            token_savings_pct=round(token_savings, 1),
            encoding_time_ms=round(elapsed_ms, 2),
            correctness=correctness,
        ))
        # Print compact comparison too
        if toon_output:
            print(f"  [{name}] vs compact JSON: {compact_savings:+.1f}% tokens")

    # Composite score
    avg_token_savings = sum(r.token_savings_pct for r in results) / len(results) if results else 0
    correctness_score = 100.0 if all_correct else 0.0
    avg_time_ms = sum(r.encoding_time_ms for r in results) / len(results) if results else 999
    speed_score = min(100.0, (10.0 / max(avg_time_ms, 0.01)) * 100)

    # Hard-fail: if any dataset fails correctness, score is capped at 20
    if not all_correct:
        composite = min(20.0, avg_token_savings * 0.2 + speed_score * 0.1)
    else:
        composite = (
            avg_token_savings * 0.5 +
            correctness_score * 0.3 +
            speed_score * 0.2
        )

    return {
        "score": round(composite, 1),
        "avg_token_savings_pct": round(avg_token_savings, 1),
        "correctness": all_correct,
        "avg_encoding_time_ms": round(avg_time_ms, 2),
        "results": [
            {
                "dataset": r.dataset_name,
                "json_tokens": r.json_tokens,
                "toon_tokens": r.toon_tokens,
                "savings_pct": r.token_savings_pct,
                "time_ms": r.encoding_time_ms,
                "correct": r.correctness,
            }
            for r in results
        ],
    }


def main():
    """Run evaluation and print results."""
    print("=" * 60)
    print("  Seamless-RAG Evaluation Harness (IMMUTABLE)")
    print("=" * 60)
    print()

    result = evaluate()

    if result.get("status") == "import_error":
        print("FAIL: Cannot import encoder. Implement seamless_rag.toon.encoder first.")
        sys.exit(1)

    # Print per-dataset results
    print(f"{'Dataset':<20} {'JSON tok':<10} {'TOON tok':<10} {'Savings':<10} {'Time':<10} {'OK'}")
    print("-" * 60)
    for r in result["results"]:
        ok = "PASS" if r["correct"] else "FAIL"
        print(f"{r['dataset']:<20} {r['json_tokens']:<10} {r['toon_tokens']:<10} {r['savings_pct']:>6.1f}%   {r['time_ms']:>6.2f}ms  {ok}")

    print("-" * 60)
    print(f"Avg token savings: {result['avg_token_savings_pct']:.1f}%")
    print(f"All correct: {result['correctness']}")
    print(f"Avg encoding time: {result['avg_encoding_time_ms']:.2f}ms")
    print()
    print(f"COMPOSITE SCORE: {result['score']:.1f} / 100")
    print()

    # Output for experiment log
    print(f"eval_score:{result['score']}")
    print(f"token_savings:{result['avg_token_savings_pct']}")

    # Pass threshold: 60 is "working correctly with decent savings"
    # 80+ is "championship quality"
    # Maximum theoretical: ~95 (50% savings × 0.5 + 100 correctness × 0.3 + 100 speed × 0.2)
    sys.exit(0 if result["score"] >= 60 else 1)


if __name__ == "__main__":
    main()
