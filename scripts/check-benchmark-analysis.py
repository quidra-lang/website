#!/usr/bin/env python3
"""Offline consistency gate: all rows, correct rivals, matching scores, pinned evidence."""
import json
import sys
import unittest
from pathlib import Path

from benchmark_analysis.validation import validate_analysis

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    try:
        data = json.loads((ROOT / "src/data/benchmarks.json").read_text(encoding="utf-8"))
        analysis = json.loads((ROOT / "src/data/benchmark-analysis.json").read_text(encoding="utf-8"))
        validate_analysis(data, analysis)
    except (ValueError, KeyError, OSError) as error:
        print(f"benchmark analysis: {error}", file=sys.stderr)
        return 1
    suite = unittest.defaultTestLoader.discover(str(ROOT / "scripts/benchmark_analysis"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        return 1
    requirements = sum(len(e["requirements"]) for e in analysis["evaluations"])
    comparisons = sum(len(r["languages"]) for e in analysis["evaluations"] for r in e["requirements"])
    print(f"benchmark analysis: {len(analysis['evaluations'])} evaluations, {requirements} requirements, "
          f"{comparisons} cited language explanations; all scores and tied leaders match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
