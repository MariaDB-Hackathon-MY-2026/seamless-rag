#!/usr/bin/env python3
"""
Post-hoc experiment analysis — reads eval/results.tsv and shows trends.

Inspired by Karpathy's autoresearch analysis.ipynb pattern:
- Shows experiment trajectory over time
- Identifies which changes improved scores
- Prints running best score
"""
from pathlib import Path

RESULTS_FILE = Path(__file__).parent / "results.tsv"


def main():
    if not RESULTS_FILE.exists():
        print("No results.tsv found. Run 'make score' to generate experiment data.")
        return

    lines = RESULTS_FILE.read_text().strip().split("\n")
    if len(lines) < 2:
        print("Not enough data points. Keep running experiments.")
        return

    header = lines[0].split("\t")
    rows = [dict(zip(header, line.split("\t"))) for line in lines[1:]]

    print("=" * 60)
    print("  Experiment Trajectory Analysis")
    print("=" * 60)
    print()

    # Show all experiments
    print(f"{'#':<4} {'Timestamp':<22} {'Overall':<10} {'Unit':<8} {'Spec':<8} {'Status'}")
    print("-" * 60)

    best_overall = 0.0
    for i, row in enumerate(rows, 1):
        overall = float(row.get("overall_pct", 0))
        best_overall = max(best_overall, overall)
        marker = " *" if overall >= best_overall and overall > 0 else ""
        print(
            f"{i:<4} "
            f"{row.get('timestamp', '?')[:19]:<22} "
            f"{overall:>6.1f}%   "
            f"{row.get('unit', '?'):>5}%  "
            f"{row.get('spec', '?'):>5}%  "
            f"{row.get('status', '?')}{marker}"
        )

    print("-" * 60)
    print(f"Total experiments: {len(rows)}")
    print(f"Best overall: {best_overall:.1f}%")

    # Count pass/partial/fail
    pass_count = sum(1 for r in rows if r.get("status") == "pass")
    partial_count = sum(1 for r in rows if r.get("status") == "partial")
    print(f"Passes: {pass_count}, Partial: {partial_count}, Other: {len(rows) - pass_count - partial_count}")


if __name__ == "__main__":
    main()
