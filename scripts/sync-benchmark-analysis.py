#!/usr/bin/env python3
"""Explain the run already selected in benchmarks.json; never start a benchmark.

Usage: python3 scripts/sync-benchmark-analysis.py /path/to/quidra [--check]
Use scripts/sync-benchmarks.py to select a new published run and update both views.
"""
import argparse
import json
from pathlib import Path

from benchmark_analysis import build_analysis

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "src/data/benchmark-analysis.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("core", type=Path)
    parser.add_argument("--check", action="store_true", help="verify reproducibility without writing")
    args = parser.parse_args()
    try:
        site = json.loads((ROOT / "src/data/benchmarks.json").read_text(encoding="utf-8"))
        analysis = build_analysis(args.core.resolve(), site)
        output = json.dumps(analysis, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != output:
                raise ValueError("benchmark-analysis.json differs from its recorded evidence; regenerate it")
        else:
            OUTPUT.write_text(output, encoding="utf-8")
        count = sum(len(e["requirements"]) for e in analysis["evaluations"])
        print(f"benchmark analysis: {'verified' if args.check else 'wrote'} {count} requirements, "
              f"run {site['run_id']}, sources {analysis['source_commit']}")
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"benchmark analysis: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
