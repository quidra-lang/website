"""Deterministic, source-backed explanations for the website's published run."""
from __future__ import annotations

import subprocess
from pathlib import Path

from .validation import validate_analysis, validate_source_scores


def build_analysis(core: Path, site_data: dict) -> dict:
    from . import llm, quality

    source_commit = subprocess.check_output(
        ["git", "-C", str(core), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(core), "status", "--porcelain", "--untracked-files=no", "--", "benchmark"], text=True)
    if dirty.strip():
        raise ValueError("benchmark sources have uncommitted changes; cannot cite them as an immutable commit")
    validate_source_scores(site_data, core)
    explanations = {e["id"]: e for e in quality.build(core, site_data, source_commit)
                    + llm.build(core, site_data, source_commit)}
    analysis = {
        "schema_version": 1,
        "run_id": site_data["run_id"],
        "evaluated_commit": site_data["evaluated_commit"],
        "source_commit": source_commit,
        "evaluations": [explanations[e["id"]] for e in site_data["evaluations"]],
    }
    validate_analysis(site_data, analysis, core)
    return analysis
