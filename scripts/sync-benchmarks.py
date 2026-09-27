#!/usr/bin/env python3
"""Sync the published Quidra benchmark result into src/data/benchmarks.json.

usage:
    python3 scripts/sync-benchmarks.py /path/to/quidra-core-checkout [--ref main]

The core checkout is https://github.com/quidra-lang/quidra. The script reads only
files that the benchmark itself declares authoritative:

    benchmark/config.json                            comparison-language versions
    benchmark/template/config/benchmark_metadata.json  evaluation ids, display names,
                                                       canonical language order
    benchmark/<run-id>/rankings.json                 published rankings (authoritative)
    benchmark/<run-id>/summary.json                  evaluated commit, compiler version,
                                                       status, display-name rankings
    benchmark/<run-id>/provenance.json               inference model identity
    benchmark/<run-id>/versioned_scores.json         display name -> language id map
    benchmark/<run-id>/breakdown/<evaluation>.json   per-requirement scores

The run directory is the newest ``benchmark/20??-??-??-*/`` directory that contains a
``rankings.json``. Only stdlib is used. Output is deterministic: fixed key order,
2-space indent, trailing newline. Every ranking number written is re-read from the
generated file and asserted equal to rankings.json before the script exits 0.

Structure of breakdown/<evaluation>.json this script relies on (schema_version 1):

    {
      "evaluation": "<id>",
      "status": "COMPLETE",
      "languages": [<display names in canonical order>],
      "aggregation": {"type": "weighted_mean" | "category_mean" | "semantic_harmonic", ...},
      "published": {"ranking": [{"language": <display name>, "rank": int, "score": float}], ...},
      "requirements": [
        {
          "requirement_id": "metric.x" | "condition.x",
          "weight": float,            # only for weighted_mean / semantic_harmonic quality metrics
          "category": "<category>",   # only for category_mean evaluations
          "scores": {<display name>: float (full precision)},
          "ranking": [{"language": <display name>, "rank": int, "score": float (rounded)}],
          "not_applicable": {<display name>: <reason>},
          "measured_by": [...]
        }
      ],
      "categories": [                 # empty unless aggregation.type == "category_mean"
        {"category": "<id>", "weight": float, "metrics": [<requirement ids>],
         "means": {<display name>: float}, "contribution": {...},
         "ranking": [{"language": <display name>, "rank": int, "score": float (rounded)}]}
      ]
    }

Per-requirement and per-category scores are taken from the already-rounded
``ranking[].score`` values (the same precision as rankings.json); the full-precision
``scores`` map is only used as a cross-check.

The methodology summaries are authored text (they cannot be derived mechanically)
and live in METHODOLOGY_SUMMARIES below. Each one was written against the
corresponding benchmark/template/methodology/<evaluation>.md and common.md; keep
them in sync with those documents when the methodology changes.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

GITHUB_REPO = "https://github.com/quidra-lang/quidra"
DEFAULT_REF = "main"

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "src" / "data" / "benchmarks.json"

# Authored text. 1-3 plain sentences per evaluation describing WHAT is measured and
# HOW, at a high level. Every claim is stated in benchmark/template/methodology/*.md
# or benchmark/template/config/primary.json of the evaluated checkout.
METHODOLOGY_SUMMARIES: dict[str, str] = {
    "semantic_compression": (
        "How much program meaning a language states explicitly and determinately per "
        "unit of syntax, relative to the breadth of capabilities it can express. All ten "
        "languages are annotated against one frozen, language-neutral semantic-site "
        "matrix over 44 probes. Five quality metrics (density, determinacy, locality, "
        "hidden semantic cost, capability efficiency) form a quality score, and the "
        "published score is its harmonic mean with capability coverage, so a tiny "
        "language cannot score high by having few rules. Annotation is worker judgment "
        "checked by a mechanical validator and a blinded comparability audit. Higher is "
        "better."
    ),
    "llm_learnability": (
        "Whether a model can learn a language's rules from a reference pack and apply "
        "them when familiarity is controlled: the language is never named, keywords or "
        "vocabulary are transformed by reversible mappings in most conditions, and every "
        "program is mapped back and validated by the real toolchain. Six conditions "
        "(keyword and vocabulary anonymization, surface perturbation, novel-rule "
        "generalization, held-out rule composition, prior-conflict resistance) are "
        "scored with the same task metrics as LLM Proficiency and combined with fixed "
        "weights. It is separate from LLM Proficiency and is not a proof of zero prior "
        "exposure. Higher is better."
    ),
    "language_quality": (
        "The intrinsic quality of the language and its implementation on comparable "
        "workloads written idiomatically in each language, excluding maturity and "
        "network effects, which belong to Ecosystem. Twenty-five metrics in four "
        "weighted categories: performance and resource metrics are mechanical "
        "measurements of the same programs; safety and robustness metrics are computed "
        "from frozen adversarial case sets that record how early a defect is detected; "
        "language and development metrics are worker judgments on frozen rubrics. "
        "Scores are 0-100, higher is better."
    ),
    "ecosystem": (
        "The infrastructure, maturity and real-world evidence around a language: "
        "libraries, package activity, third-party tools, production adoption, community "
        "knowledge, tooling, editor and debugger support, documentation, installation, "
        "release maturity and platform coverage. It is kept separate from Language "
        "Quality so a young language's maturity gap stays visible. Fifteen metrics in "
        "two equally weighted categories; for each, an LLM worker gathers evidence by "
        "web search and assigns rubric levels that the runner converts to a 0-100 score. "
        "Absent evidence scores low rather than N/A. Higher is better."
    ),
    "llm_proficiency": (
        "How useful a language is to a present-day LLM under its real name, syntax, "
        "standard library and toolchain; pretraining familiarity is deliberately "
        "included. One fixed model implements three frozen workloads under two "
        "scenarios with up to three repair turns, and correctness is decided by "
        "hidden-input oracles. Eighteen weighted metrics, including Correct@1, silent-bug "
        "resistance, test pass rate and repair success, combine into a 0-100 score; "
        "sixteen are computed by the runner from trial evidence and two are "
        "worker-judged. Higher is better."
    ),
}

RUN_ID_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-([0-9a-f]{7,40})-(.+)$")


class SyncError(Exception):
    pass


def fail(message: str) -> None:
    raise SyncError(message)


def load_json(path: Path):
    if not path.is_file():
        fail(f"missing required file: {path}")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def find_run_dir(bench: Path) -> Path:
    candidates = sorted(
        d for d in bench.glob("20??-??-??-*") if d.is_dir() and (d / "rankings.json").is_file()
    )
    if not candidates:
        fail(f"no benchmark/20??-??-??-*/rankings.json found under {bench}")
    return candidates[-1]


def github_url(rel_path: str, ref: str, *, is_dir: bool) -> str:
    kind = "tree" if is_dir else "blob"
    return f"{GITHUB_REPO}/{kind}/{ref}/{rel_path}"


def check_checkout_path(core: Path, rel_path: str, *, is_dir: bool) -> None:
    p = core / rel_path
    ok = p.is_dir() if is_dir else p.is_file()
    if not ok:
        fail(f"URL target does not exist in checkout: {rel_path}")


def build(core: Path, ref: str) -> tuple[dict, dict]:
    bench = core / "benchmark"
    run_dir = find_run_dir(bench)
    run_id = run_dir.name
    run_rel = f"benchmark/{run_id}"

    metadata = load_json(bench / "template" / "config" / "benchmark_metadata.json")
    config = load_json(bench / "config.json")
    rankings = load_json(run_dir / "rankings.json")
    summary = load_json(run_dir / "summary.json")
    provenance = load_json(run_dir / "provenance.json")
    versioned = load_json(run_dir / "versioned_scores.json")

    if rankings.get("run_id") != run_id or summary.get("run_id") != run_id:
        fail("run_id mismatch between directory name, rankings.json and summary.json")

    m = RUN_ID_RE.match(run_id)
    if not m:
        fail(f"run_id does not match <date>-<short sha>-<tag>: {run_id}")
    run_date, short_sha, _tag = m.groups()

    commit = summary["evaluated"]["commit_sha"]
    if not commit.startswith(short_sha):
        fail(f"evaluated commit {commit} does not start with run_id short sha {short_sha}")
    compiler_version = summary["evaluated"]["compiler_version"]
    if provenance.get("quidra_project_version") != compiler_version:
        fail("compiler_version differs between summary.json and provenance.json")

    # --- languages -------------------------------------------------------------
    display_names: list[str] = metadata["languages"]
    target_name: str = metadata["evaluated_target_language"]
    if target_name not in display_names:
        fail(f"evaluated target language {target_name!r} is not in the language list")

    name_to_id: dict[str, str] = {}
    for name in display_names:
        entry = config["languages"].get(name)
        if entry is None:
            fail(f"benchmark/config.json has no entry for language {name!r}")
        version = compiler_version if name == target_name else entry["version"]
        name_to_id[name] = f"{entry['id']}_v{version}"

    # Cross-check against the run's own display-name -> generation-id map.
    for ev_id, ev_data in versioned["evaluations"].items():
        gens = ev_data.get("current_generations", {})
        if gens != name_to_id:
            fail(f"versioned_scores.json current_generations for {ev_id} differ from config-derived ids")
    id_to_name = {v: k for k, v in name_to_id.items()}
    quidra_id = name_to_id[target_name]
    if provenance.get("quidra_result_id") != quidra_id:
        fail("quidra_result_id in provenance.json differs from derived id")

    languages_out = [
        {"id": name_to_id[n], "name": n, "version": name_to_id[n].split("_v", 1)[1]}
        for n in display_names
    ]

    # --- ranking basis (must be identical across evaluations) --------------------
    bases = list(rankings["ranking_basis"].values())
    if not bases:
        fail("rankings.json has no ranking_basis")
    for b in bases[1:]:
        if b != bases[0]:
            fail("ranking_basis differs between evaluations; refusing to flatten it")
    basis = bases[0]
    precision = int(basis["precision_decimals"])

    def rounded(x: float) -> float:
        return round(float(x), precision)

    # --- evaluations -----------------------------------------------------------
    eval_meta = metadata["evaluations"]
    eval_ids = [e["id"] for e in eval_meta]
    if set(eval_ids) != set(METHODOLOGY_SUMMARIES):
        fail(
            "METHODOLOGY_SUMMARIES keys must equal the evaluation ids in benchmark_metadata.json: "
            f"{sorted(eval_ids)} vs {sorted(METHODOLOGY_SUMMARIES)}"
        )
    if set(eval_ids) != set(rankings["rankings"]):
        fail("rankings.json evaluations differ from benchmark_metadata.json")

    evaluations_out = []
    for order, e in enumerate(eval_meta, start=1):
        ev_id = e["id"]
        published = rankings["rankings"][ev_id]
        prim = summary["primary_evaluations"][ev_id]
        breakdown = load_json(run_dir / "breakdown" / f"{ev_id}.json")

        if rankings["language_counts"][ev_id] != len(display_names):
            fail(f"{ev_id}: language_counts is not {len(display_names)}")
        if len(published) != len(display_names):
            fail(f"{ev_id}: ranking has {len(published)} entries, expected {len(display_names)}")
        if prim["status"] != "COMPLETE":
            fail(f"{ev_id}: status is {prim['status']}, only COMPLETE evaluations publish a ranking")
        if breakdown.get("evaluation") != ev_id or breakdown.get("status") != "COMPLETE":
            fail(f"{ev_id}: breakdown file does not describe a COMPLETE {ev_id}")
        if breakdown.get("languages") != display_names:
            fail(f"{ev_id}: breakdown language order differs from benchmark_metadata.json")

        ranking_out = []
        for row in published:
            lang_id = row["language"]
            if lang_id not in id_to_name:
                fail(f"{ev_id}: unknown language id {lang_id!r} in rankings.json")
            ranking_out.append(
                {
                    "rank": int(row["rank"]),
                    "language_id": lang_id,
                    "name": id_to_name[lang_id],
                    "score": rounded(row["score"]),
                }
            )
        if {r["language_id"] for r in ranking_out} != set(name_to_id.values()):
            fail(f"{ev_id}: ranking does not cover exactly the ten languages")

        # Display names and numbers must agree with summary.json's display-name ranking
        # (ties may be listed in a different order there, so compare as multisets).
        sci = sorted((r["rank"], r["language"], rounded(r["score"])) for r in prim["scientific_primary_ranking"])
        ours = sorted((r["rank"], r["name"], r["score"]) for r in ranking_out)
        if sci != ours:
            fail(f"{ev_id}: display-name ranking disagrees with summary.json scientific_primary_ranking")
        pub = sorted((r["rank"], r["language"], rounded(r["score"])) for r in breakdown["published"]["ranking"])
        if pub != ours:
            fail(f"{ev_id}: breakdown published ranking disagrees with rankings.json")

        quidra_row = next(r for r in ranking_out if r["language_id"] == quidra_id)

        requirements_out = []
        for req in breakdown["requirements"]:
            scores_by_name = {}
            ranks_by_name = {}
            for row in req["ranking"]:
                name = row["language"]
                if name not in name_to_id:
                    fail(f"{ev_id}/{req['requirement_id']}: unknown language {name!r}")
                if name in scores_by_name:
                    fail(f"{ev_id}/{req['requirement_id']}: language {name!r} ranked twice")
                score = rounded(row["score"])
                full = req["scores"].get(name)
                if full is None or abs(rounded(full) - score) > 10 ** (-precision) * 1.01:
                    fail(f"{ev_id}/{req['requirement_id']}: ranking score disagrees with scores map for {name}")
                scores_by_name[name] = score
                ranks_by_name[name] = int(row["rank"])
            row_out = {
                "id": req["requirement_id"],
                "weight": req.get("weight"),
                "category": req.get("category"),
                "scores": {name_to_id[n]: scores_by_name[n] for n in display_names if n in scores_by_name},
                "ranks": {name_to_id[n]: ranks_by_name[n] for n in display_names if n in ranks_by_name},
            }
            na = req.get("not_applicable") or {}
            if na:
                row_out["not_applicable"] = {name_to_id[n]: na[n] for n in display_names if n in na}
            requirements_out.append(row_out)

        categories_out = []
        for cat in breakdown.get("categories", []):
            scores_by_name = {}
            ranks_by_name = {}
            for row in cat["ranking"]:
                name = row["language"]
                score = rounded(row["score"])
                mean = cat["means"].get(name)
                if mean is None or abs(rounded(mean) - score) > 10 ** (-precision) * 1.01:
                    fail(f"{ev_id}/{cat['category']}: category ranking score disagrees with means for {name}")
                scores_by_name[name] = score
                ranks_by_name[name] = int(row["rank"])
            categories_out.append(
                {
                    "id": cat["category"],
                    "weight": cat["weight"],
                    "metrics": list(cat["metrics"]),
                    "scores": {name_to_id[n]: scores_by_name[n] for n in display_names if n in scores_by_name},
                    "ranks": {name_to_id[n]: ranks_by_name[n] for n in display_names if n in ranks_by_name},
                }
            )

        methodology_rel = f"benchmark/template/methodology/{ev_id}.md"
        breakdown_rel = f"{run_rel}/breakdown/{ev_id}.md"
        check_checkout_path(core, methodology_rel, is_dir=False)
        check_checkout_path(core, breakdown_rel, is_dir=False)

        evaluations_out.append(
            {
                "id": ev_id,
                "name": e["display_name"],
                "order": order,
                "summary": METHODOLOGY_SUMMARIES[ev_id],
                "methodology_url": github_url(methodology_rel, ref, is_dir=False),
                "breakdown_url": github_url(breakdown_rel, ref, is_dir=False),
                "status": prim["status"],
                "aggregation": breakdown["aggregation"]["type"],
                "ranking": ranking_out,
                "quidra": {"rank": quidra_row["rank"], "score": quidra_row["score"]},
                "requirements": requirements_out,
                "categories": categories_out,
            }
        )

    source_paths = {
        "readme": ("benchmark/README.md", False),
        "run": (run_rel, True),
        "rankings": (f"{run_rel}/rankings.json", False),
        "methodology_dir": ("benchmark/template/methodology", True),
    }
    for rel, is_dir in source_paths.values():
        check_checkout_path(core, rel, is_dir=is_dir)

    data = {
        "run_id": run_id,
        "run_date": run_date,
        "evaluated_commit": commit,
        "evaluated_commit_short": short_sha,
        "compiler_version": compiler_version,
        "inference_model": provenance["inference_identity"]["model"],
        "source_urls": {k: github_url(rel, ref, is_dir=is_dir) for k, (rel, is_dir) in source_paths.items()},
        "interpretation": basis["interpretation"],
        "tie_policy": basis["tie_policy"],
        "precision_decimals": precision,
        "languages": languages_out,
        "evaluations": evaluations_out,
    }
    return data, rankings


def verify_output(path: Path, run_dir: Path) -> None:
    """Re-read the generated file and rankings.json from disk and compare every number."""
    with path.open(encoding="utf-8") as fh:
        out = json.load(fh)
    rankings = load_json(run_dir / "rankings.json")
    if out["run_id"] != rankings["run_id"]:
        fail("verify: run_id mismatch")
    seen = set()
    for ev in out["evaluations"]:
        expected = [(int(r["rank"]), r["language"], round(float(r["score"]), out["precision_decimals"]))
                    for r in rankings["rankings"][ev["id"]]]
        actual = [(r["rank"], r["language_id"], r["score"]) for r in ev["ranking"]]
        if expected != actual:
            fail(f"verify: {ev['id']} ranking differs from rankings.json:\n  {expected}\n  {actual}")
        scores = rankings["scores"][ev["id"]]
        for r in ev["ranking"]:
            if round(float(scores[r["language_id"]]), out["precision_decimals"]) != r["score"]:
                fail(f"verify: {ev['id']} score for {r['language_id']} differs from rankings.json scores map")
        q = next(r for r in ev["ranking"] if r["name"] == "Quidra")
        if ev["quidra"] != {"rank": q["rank"], "score": q["score"]}:
            fail(f"verify: {ev['id']} quidra summary differs from its ranking row")
        seen.add(ev["id"])
    if seen != set(rankings["rankings"]):
        fail("verify: evaluation set differs from rankings.json")
    if len(out["languages"]) != 10:
        fail("verify: expected ten languages")


def main(argv: list[str]) -> int:
    unknown = [a for a in argv[1:] if a.startswith("--") and a != "--ref"]
    if unknown:
        raise SystemExit(f"unknown option(s): {' '.join(unknown)}")
    args = [a for a in argv[1:] if not a.startswith("--")]
    ref = DEFAULT_REF
    if "--ref" in argv:
        i = argv.index("--ref")
        if i + 1 >= len(argv):
            print("--ref needs a value", file=sys.stderr)
            return 2
        ref = argv[i + 1]
        args = [a for a in args if a != ref]
    if len(args) != 1:
        print(__doc__.split("\n\n", 1)[0], file=sys.stderr)
        print("usage: python3 scripts/sync-benchmarks.py /path/to/quidra-core-checkout [--ref main]", file=sys.stderr)
        return 2
    core = Path(args[0]).resolve()
    if not (core / "benchmark").is_dir():
        print(f"not a Quidra core checkout (no benchmark/ directory): {core}", file=sys.stderr)
        return 2

    try:
        data, _rankings = build(core, ref)
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        OUTPUT_PATH.write_text(text, encoding="utf-8")
        verify_output(OUTPUT_PATH, core / "benchmark" / data["run_id"])
    except SyncError as exc:
        print(f"sync-benchmarks: {exc}", file=sys.stderr)
        return 1

    n_req = sum(len(e["requirements"]) for e in data["evaluations"])
    print(
        f"wrote {OUTPUT_PATH}: run {data['run_id']}, {len(data['evaluations'])} evaluations, "
        f"{len(data['languages'])} languages, {n_req} requirement rows; verified against rankings.json"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
