"""Build evidence-backed explanations for the historical non-LLM evaluations.

The published breakdown owns every displayed score.  Retained worker evidence,
the run-selected mechanical cache, and immutable generation inputs explain those
scores.  Source-snapshot methodology is never substituted for missing observations.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
from statistics import mean


REPO = "https://github.com/quidra-lang/quidra"
PROBE_ID = re.compile(r"^F\d\d\.P\d$")
WORKLOADS = {
    "mb01": "Fibonacci", "mb02": "Factorial", "mb03": "Integer arithmetic",
    "mb04": "Floating-point arithmetic", "mb05": "Vector inner product",
    "mb06": "Matrix multiplication", "mb07": "Sorting", "mb08": "Strings",
    "mb09": "Statistics", "mb10": "File I/O", "mb11": "Collections",
}

SC_META = {
    "semantic_density": (
        "Semantic density",
        "How many locally explicit semantic facts the measured syntax communicates per lexical token.",
    ),
    "semantic_determinacy": (
        "Semantic determinacy",
        "How many materially different interpretations remain possible from a probe's local syntax.",
    ),
    "semantic_locality": (
        "Semantic locality",
        "How much external context the submitted annotations say a reader must inspect to resolve a probe's meaning.",
    ),
    "hidden_semantic_cost": (
        "Hidden semantic cost",
        "How many material behaviors from the prescribed checklist occur without a local syntactic signal.",
    ),
    "capability_efficiency": (
        "Capability efficiency",
        "The recorded number of semantic complexity units per supported capability point.",
    ),
    "capability_coverage": (
        "Capability coverage",
        "How much of the complete language-neutral capability universe each language was credited with supporting.",
    ),
}

MICRO_META = {
    "native_execution_performance": (
        "Native execution performance", "cold_seconds", "s",
        "Cold execution wall time for the eleven prescribed microbenchmark workloads.",
    ),
    "long_running_performance": (
        "Long-running performance", "steady_seconds", "s",
        "Steady execution time for the same eleven microbenchmark workloads.",
    ),
    "compile_build_performance": (
        "Compile / build performance", "compile_effective_seconds", "effective s",
        "Build cost, using the archived effective compile-time values that include the runner's calibration shift.",
    ),
    "startup_latency": (
        "Startup latency", "startup_seconds", "s",
        "Process-start-to-exit wall time for MB-00, the ordinary program that prints HELLO.",
    ),
    "memory_efficiency": (
        "Memory efficiency", "rss_bytes", "bytes",
        "Peak resident memory under the eleven microbenchmark workloads.",
    ),
    "source_code_size": (
        "Source code size", "source_bytes", "bytes",
        "Source bytes for the eleven equivalent benchmark programs; each workload is normalized separately.",
    ),
    "binary_artifact_size": (
        "Binary / artifact size", "artifact_effective_bytes", "effective bytes",
        "The archived build-artifact values, including the runner's artifact-size shift.",
    ),
    "runtime_overhead": (
        "Runtime overhead", "startup_rss_bytes", "bytes",
        "Baseline resident memory for MB-00, separate from memory consumed by substantive workloads.",
    ),
}

DESIGN_META = {
    "code_efficiency_conciseness": ("Code efficiency / conciseness", "The mandatory ceremony needed to express ordinary programs, judged separately from measured source bytes."),
    "readability": ("Readability", "The clarity of idiomatic source, judged through a fixed rubric rather than a human readability study."),
    "functionality_expressiveness": ("Functionality / expressiveness", "The intrinsic ability to model data, compose abstractions and control execution."),
    "diagnostics": ("Diagnostics", "The language implementation's ability to identify and explain errors with useful, stable diagnostic information."),
    "dependency_simplicity": ("Dependency simplicity", "The explicitness and predictability of module and dependency semantics."),
    "portability_design_platform_neutrality": ("Portability design / platform neutrality", "Whether the language's design supports portable source and explicit platform boundaries."),
    "ffi_interoperability_design": ("FFI / interoperability design", "How the language declares, controls and checks foreign-interface boundaries."),
    "concurrency": ("Concurrency", "The language and core runtime's parallelism, task structure, coordination and error propagation."),
}

ECOSYSTEM_META = {
    "third_party_library_availability_domain_coverage": ("Third-party library availability / domain coverage", "Evidence of usable independently maintained libraries across five prescribed domain groups."),
    "package_ecosystem_activity_maintenance": ("Package ecosystem activity / maintenance", "Evidence of package discovery, maintenance, metadata, distribution and supply-chain support."),
    "third_party_tool_availability": ("Third-party tool availability", "Evidence of independently maintained editor, analysis, build, debugging and developer-operations tools."),
    "production_adoption_deployment_evidence": ("Production adoption / deployment evidence", "Publicly checkable deployments, their scale, diversity, continuity and depth."),
    "community_public_knowledge_availability": ("Community / public knowledge availability", "Searchable discussion, independent learning material, active groups and the breadth of public knowledge."),
    "core_tooling_availability_quality": ("Core tooling availability / quality", "The build, formatting, testing, documentation and diagnostic tools available in the core workflow."),
    "package_dependency_management_quality": ("Package / dependency management quality", "The quality of dependency resolution, manifests, workspaces, security and publishing workflows."),
    "ide_editor_support_quality": ("IDE / editor support quality", "Implemented navigation, completion, refactoring, debugging and editor support."),
    "debugger_profiler_support": ("Debugger / profiler support", "Usable debugging and profiling facilities around the implementation."),
    "build_test_integration": ("Build / test integration", "Evidence of repeatable builds, test execution, automation and integration."),
    "documentation_quality": ("Documentation quality", "The coverage, usability and maintenance of language and toolchain documentation."),
    "installation_distribution_experience": ("Installation / distribution experience", "How well users can obtain, install, update and verify supported distributions."),
    "toolchain_stability_release_maturity": ("Toolchain stability / release maturity", "Observable release, compatibility and maintenance commitments; language age itself earns no points."),
    "implemented_platform_coverage": ("Implemented platform coverage", "The operating systems, architectures and deployment targets actually supported at the evidence snapshot."),
    "external_integration_coverage": ("External integration coverage", "Working bindings and integrations with external languages, native systems, data systems and services."),
}

# These analyst caveats concern specific retained records, not later language releases.
RUBRIC_RECORD_CAVEATS = {
    ("2026-09-27-38b7137-gh31", "metric.implemented_platform_coverage", "Quidra"): (
        "The architecture component was recertified at 4/4, contributing 20 points, but its preserved finding describes only generic Linux CI and says an ARM64 Linux target was not evidenced. The row's limitation also says ARM64 targets were not evidenced. This inherited text does not independently justify full coverage across the rubric's major CPU architectures; the displayed points reproduce the recorded level.",
        "The WebAssembly finding describes running the compiler frontend in a browser. By itself, that does not demonstrate WebAssembly as a deployment target for generated Quidra programs. The recertified web/WASM/other component is 0/4; the inherited frontend finding does not directly establish or refute support under that deployment-target criterion. The embedded component's attached finding describes macOS and Apple Silicon runtime details, which do not independently evaluate embedded or bare-metal deployment support for its recorded 0/4 level.",
    ),
    ("2026-09-27-38b7137-gh31", "metric.third_party_library_availability_domain_coverage", "TypeScript"): (
        "The inherited finding describes coverage as near-complete but 'not scored 100', whereas the later recertification assigns 4/4 to all five components and the runner publishes 100. The preserved 97/100 assessment and the recertified 100/100 belong to different assessment stages. The inherited prose does not independently justify all five maximum levels.",
        "Some preserved findings are not specific to their assigned domain: the data/numerical paragraph discusses frontend state-management libraries, and the ML / AI paragraph gives npm registry totals. Those observations alone do not establish the rubric's numerical/scientific and machine-learning library coverage. The official component levels remain the arithmetic source for this comparison.",
    ),
}

SAFETY_META = {
    "type_safety": (
        "Type safety", "Interception of six type hazards, with additional credit for guarantees established before execution.",
        "Score = 0.5 × TS_stage + 0.5 × TS_static. TS_stage averages detection-stage credit across six equally weighted hazards; TS_static is 100 times the hazard-weighted fraction prevented by construction, rejected at compile time, or checked before execution. The prescribed set has eight case-variant rows.",
    ),
    "memory_safety": (
        "Memory safety", "The integrity-preservation rate on nine prescribed storage hazards.",
        "Score = 100 × mean(integrity-preserved indicator), first averaging variants within each hazard, then giving the nine hazards equal weight. Prevention, compile-time detection, pre-execution checking and safe runtime detection receive 1; other outcomes receive 0. The prescribed set has eleven case-variant rows.",
    ),
    "runtime_safety": (
        "Runtime safety", "The fraction of scored row-weight reaching execution that was prevented by construction or safely diagnosed at runtime.",
        "Score = 100 × safe runtime/prevented row-weight ÷ row-weight that reaches execution. Compile-time and pre-execution rejections leave the denominator; sub-programs share their row's weight. The source scorer assigns 100 when applicable rows exist but none reaches execution.",
    ),
    "boundary_value_safety": (
        "Boundary value safety", "Detection-stage credit on eleven numeric and index-boundary hazards.",
        "Score = the mean detection-stage credit across ADV-01 through ADV-10 and ADV-24. Variants and sub-programs are averaged within a case before the eleven cases receive equal weight.",
    ),
    "adversarial_input_robustness": (
        "Adversarial input robustness", "Detection-stage credit on seven hazards supplied through external input or unbounded resource demand.",
        "Score = the mean detection-stage credit across ADV-11, ADV-19, ADV-20, ADV-21, ADV-22, ADV-23 and ADV-25, giving each of these seven cases equal weight after within-case averaging.",
    ),
    "early_error_detection": (
        "Early error detection", "How early the implementation prevented or exposed defects across the complete adversarial case set.",
        "Score = the arithmetic mean of detection-stage credits across 26 equally weighted hazards. The source scorer averages variants and sub-programs within each hazard first, so a hazard with more variants receives no extra case weight.",
    ),
    "debuggability": (
        "Debuggability", "A mechanical proxy for useful fault-report evidence in this published run.",
        "The implemented diagnostic-evidence proxy gives 100 × (A1 + A2 + A3) ÷ 3 per report: A1 is 1 for a case-specific hazard match, 0.5 for a general hazard match, otherwise 0; A2 is 1 for a source position; A3 is 1 for a stable fault key. Prevention by construction receives 100. Scores are averaged within variants and then across cases.",
    ),
    "silent_bug_resistance": (
        "Silent bug resistance", "Resistance to apparently plausible wrong results under the adversarial decision procedure.",
        "Score = 100 × (1 − silent-or-undefined row-weight ÷ applicable row-weight). Sub-programs share one row's weight. Undefined behavior is included because the relevant classifier outcomes are silent wrong results; uncontrolled termination is classified separately.",
    ),
    "implementation_robustness": (
        "Implementation robustness", "Resistance to failures of the toolchain itself while handling the prescribed programs.",
        "Score = 100 × (1 − flagged toolchain-failure row-weight ÷ applicable row-weight). The flags cover toolchain crashes, pre-execution toolchain crashes, successful builds producing no runnable artifact, and build timeouts. This is separate from a compiled program's runtime safety.",
    ),
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _n(value: float, digits: int = 6) -> str:
    return f"{value:,.{digits}f}".rstrip("0").rstrip(".")


def _label(value: str) -> str:
    special = {"ml_ai": "ML / AI", "c_native": "C / native", "qa_discussion": "Q&A discussion", "docs_package": "Documentation / package tooling"}
    if value in special:
        return special[value]
    acronyms = {"abi": "ABI", "api": "API", "ci": "CI", "cpu": "CPU", "ffi": "FFI", "ide": "IDE", "os": "OS", "qa": "Q&A", "sdk": "SDK", "vm": "VM", "wasm": "WASM"}
    words = value.split("_")
    return " ".join(acronyms.get(word, word.capitalize() if i == 0 else word) for i, word in enumerate(words))


def _plain(value: str) -> str:
    value = re.sub(r"\*\*|`", "", str(value))
    value = value.replace("Current Quidra", "Quidra v0.3.0 in this benchmark")
    # The surrounding paragraph already attributes findings to the archived date.
    value = re.sub(r"\bcurrently-maintained\b", "maintained", value, flags=re.I)
    value = re.sub(r"\bcurrently\b", "at the recorded snapshot", value, flags=re.I)
    value = re.sub(r"(?<!then-)\bcurrent\b", "then-current", value, flags=re.I)
    value = re.sub(r"\btoday\b", "at the recorded snapshot", value, flags=re.I)
    return re.sub(r"\s+", " ", value).strip()


def _finding(value: str) -> str:
    """Extract the finding from repeated recertification boilerplate, not its score."""
    value = str(value)
    if "Evidence basis: " in value:
        value = value.split("Evidence basis: ", 1)[1].split("Preserved paid evidence additionally records:", 1)[0]
    value = re.sub(r"^Preserved paid evidence \([^)]*\):\s*", "", value)
    value = _plain(value)
    # A legacy normalized number is not the runner's rubric total.
    value = re.sub(r"^[^.]*\b(?:is|was) scored (?:low|high) \(\d+(?:\.\d+)?/100\)\.\s*", "", value)
    value = re.sub(r"\([^)]*\b\d+(?:\.\d+)?/100\)", "", value)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", value)
    selected = sentences[0]
    if len(sentences) > 1 and len(selected) + len(sentences[1]) < 850:
        selected += " " + sentences[1]
    if len(selected) > 1100:
        selected = selected[:1050].rsplit(" ", 1)[0] + "…"
    return selected.strip()


def _check_score(actual: float, expected: float, context: str) -> None:
    if round(float(actual), 2) != float(expected):
        raise ValueError(f"{context}: reconstructed {actual} differs from published {expected}")


def _probe_rows(node) -> dict[str, list]:
    rows: dict[str, list] = {}

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if PROBE_ID.match(str(key)):
                    rows.setdefault(str(key), []).append(item)
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                probe = str(item.get("probe_id") or item.get("probe") or "") if isinstance(item, dict) else ""
                if PROBE_ID.match(probe):
                    rows.setdefault(probe, []).append({k: v for k, v in item.items() if k not in ("probe_id", "probe")})
                else:
                    walk(item)

    walk(node)
    return rows


def _row_number(value, names: list[str]) -> float | None:
    # Match the source runner's sc_row_number precedence across worker schemas.
    names = [n.lower() for n in names]
    if isinstance(value, bool):
        return None
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, list):
        return float(len(value))
    if not isinstance(value, dict):
        return None
    numeric = {str(k).lower(): float(v) for k, v in value.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
    for key in numeric:
        if key in names:
            return numeric[key]
    for key in numeric:
        if any(name in key for name in names):
            return numeric[key]
    for key, item in value.items():
        if isinstance(item, dict) and any(name in str(key).lower() for name in names):
            found = _row_number(item, names + ["total"])
            if found is not None:
                return found
    for key in ("total", "count", "value", "units", "sum", "n"):
        if key in numeric:
            return numeric[key]
    if len(numeric) == 1:
        return next(iter(numeric.values()))
    for key, item in value.items():
        if isinstance(item, list) and any(h in str(key).lower() for h in ("triggered", "categories", "hops", "lookups")):
            return float(len(item))
    return None


def _per_probe(evidence: dict, names: list[str]) -> dict[str, float]:
    values = {}
    for probe, entries in _probe_rows(evidence).items():
        for entry in entries:
            number = _row_number(entry, names)
            if number is not None:
                values[probe] = number
                break
    return values


def _probe_comment(evidence: dict, probe: str) -> str:
    for entry in _probe_rows(evidence).get(probe, []):
        if isinstance(entry, dict):
            for key in ("note", "notes", "rationale", "basis", "citation"):
                if isinstance(entry.get(key), str) and entry[key]:
                    return _plain(entry[key])
    return ""


class _Builder:
    def __init__(self, core: Path, data: dict, ref: str):
        self.core = core
        self.data = data
        self.ref = ref
        self.run_rel = f"benchmark/{data['run_id']}"
        self.run = core / self.run_rel
        self.languages = data["languages"]
        self.by_name = {l["name"]: l for l in self.languages}
        self.by_id = {l["id"]: l for l in self.languages}
        self.evaluations = {e["id"]: e for e in data["evaluations"]}
        self.provenance = _load(self.run / "provenance.json")
        self.cache_records = {r["work_unit_id"]: r for r in self.provenance["cache_promotion"]["records"]}
        self.evidence = {}
        for evaluation in ("semantic_compression", "language_quality", "ecosystem"):
            for path in sorted((self.run / "evidence" / evaluation).glob("*.json")):
                record = _load(path)
                for rid in record["requirement_ids"]:
                    for language in record["assigned_languages"]:
                        self.evidence[evaluation, rid, language] = (path, record)

    def source(self, path: str | Path, label: str) -> dict:
        if isinstance(path, Path):
            path = path.relative_to(self.core).as_posix()
        if not (self.core / path).exists():
            raise ValueError(f"Missing evidence source: {path}")
        kind = "tree" if (self.core / path).is_dir() else "blob"
        return {"label": label, "url": f"{REPO}/{kind}/{self.ref}/{path}"}

    def selected(self, requirement: dict) -> list[dict]:
        scores = requirement["scores"]
        top = max(v for k, v in scores.items() if self.by_id[k]["name"] != "Quidra")
        return [l for l in self.languages if l["name"] == "Quidra" or scores.get(l["id"]) == top]

    def language(self, requirement: dict, language: dict) -> dict:
        return {
            "id": language["id"], "name": language["name"],
            "score": requirement["scores"][language["id"]],
            "explanation": [], "facts": [], "sources": [], "caveats": [],
        }

    def requirement(self, requirement: dict, meta: tuple[str, str], method: str) -> dict:
        return {"id": requirement["id"], "title": meta[0], "description": meta[1], "method": method, "comparison_notes": [], "languages": []}

    def cache(self, work_unit: str) -> tuple[Path, dict]:
        selected = self.cache_records[work_unit]
        path = self.core / "benchmark/cache" / selected["path"]
        record = _load(path)
        if record["fingerprint"] != selected["fingerprint"]:
            raise ValueError(f"Cache identity differs for {work_unit}")
        return path, record

    def metric_record(self, evaluation: str, rid: str, name: str) -> tuple[Path, dict, dict]:
        path, record = self.evidence[evaluation, rid, name]
        block = record["evidence"].get(rid, record["evidence"])
        return path, record, block

    def rubric(self, evaluation: str) -> dict:
        relative = "ecosystem/rubrics.json" if evaluation == "ecosystem" else "language_quality/design_rubrics.json"
        return _load(self.core / "benchmark/template/methodology-assets" / relative)

    def rubric_requirement(self, evaluation: str, requirement: dict) -> dict:
        rid = requirement["id"]
        slug = rid.split(".", 1)[1]
        ecosystem = evaluation == "ecosystem"
        metadata = ECOSYSTEM_META if ecosystem else DESIGN_META
        asset = self.rubric(evaluation)
        rubric = asset["metrics"][rid]
        asset_rel = "benchmark/template/methodology-assets/" + ("ecosystem/rubrics.json" if ecosystem else "language_quality/design_rubrics.json")
        file_hash = hashlib.sha256((self.core / asset_rel).read_bytes()).hexdigest()
        components = rubric["components"]
        result = self.requirement(requirement, metadata[slug], "Five equally weighted components are each assigned a judgment level from 0 to 4. The trusted runner converts each level to 0, 5, 10, 15 or 20 points and sums the five contributions. " + _plain(rubric["selection_rule"]))
        result["comparison_notes"].append("The difference is the sum of the recorded component-level differences, multiplied by five. A tie means equal published rubric totals; the underlying findings can differ.")
        if ecosystem:
            result["comparison_notes"].append("Evidence snapshot: " + asset["evidence_policy"]["snapshot_date"] + ". These are archived evidence judgments under a fixed retrieval budget; an absence finding is scoped to that search and date.")
        else:
            result["comparison_notes"].append("These are rubric judgments about the historical implementations. They are distinct from timed workloads, safety-case execution and ecosystem maturity.")

        for language in self.selected(requirement):
            name = language["name"]
            row = self.language(requirement, language)
            path, record, block = self.metric_record(evaluation, rid, name)
            cache_path, cached = self.cache(record["work_unit_id"])
            expected_hash = cached["fingerprint_payload"]["readable_input_content_hashes"].get(asset_rel.removeprefix("benchmark/"))
            if expected_hash != file_hash:
                raise ValueError(f"{evaluation}/{rid}/{name}: rubric asset is not the run-fingerprinted version")
            if block["rubric_id"] != rubric["rubric_id"]:
                raise ValueError(f"Rubric identity differs: {rid}/{name}")
            levels = block["component_levels"]
            if set(levels) != {c["id"] for c in components}:
                raise ValueError(f"Rubric component set differs: {rid}/{name}")
            if any(type(v) is not int or v not in (0, 1, 2, 3, 4) for v in levels.values()):
                raise ValueError(f"Invalid rubric levels: {rid}/{name}")
            points = sum(asset["scoring"]["level_points"][str(v)] for v in levels.values())
            _check_score(points, row["score"], f"{rid}/{name} rubric")
            _check_score(block["runner_score_0_100"], row["score"], f"{rid}/{name} runner")
            ordered_levels = [levels[c["id"]] for c in components]
            row["explanation"].append(f"The recorded levels are {' + '.join(str(v) for v in ordered_levels)} = {sum(ordered_levels)} out of 20 level units. The runner's conversion gives {sum(ordered_levels)} × 5 = {points:.2f}/100.")
            grouped_findings: dict[str, list[str]] = {}
            for component in components:
                cid = component["id"]
                row["facts"].append({"label": _label(cid), "value": f"Level {levels[cid]}/4 → {levels[cid] * 5}/20 points"})
                finding = _finding(block["component_findings"][cid])
                if finding:
                    grouped_findings.setdefault(finding, []).append(_label(cid))
            for finding, labels in grouped_findings.items():
                row["explanation"].append(f"Recorded judgment for {', '.join(labels)}: {finding}")
            row["sources"] = [
                self.source(path, "Recorded component levels and findings"),
                self.source(asset_rel, "Rubric verified against the run's input hash"),
                self.source(cache_path, "Run-selected evidence fingerprint"),
            ]
            if block.get("limitations"):
                row["caveats"].append(_plain(block["limitations"]))
            row["caveats"].extend(RUBRIC_RECORD_CAVEATS.get((self.data["run_id"], rid, name), ()))
            if ecosystem:
                row["facts"].append({"label": "Evidence snapshot", "value": block["snapshot_date"]})
                if "legacy_score_0_100" in block and block["legacy_score_0_100"] != points:
                    row["caveats"].append(f"The archive also preserves an earlier {block['legacy_score_0_100']}/100 judgment. The published {points:.2f} is the later runner-owned rubric total; the earlier number is not used in the calculation.")
            else:
                recertifier = record["evidence"].get("language_quality_snapshot_recertification", {}).get("recertifier", {})
                if recertifier:
                    row["caveats"].append("The retained design judgment was recertified with " + recertifier.get("engine", "the recorded adjudicator") + "; the record explicitly claims no new Anthropic/Sonnet call for that reconstruction.")
            result["languages"].append(row)
        return result

    def micro_requirements(self) -> dict[str, dict]:
        rows, caches = {}, {}
        for language in self.languages:
            name = language["name"]
            selected = next(r for r in self.provenance["cache_promotion"]["records"] if r["assigned_languages"] == [name] and r["work_unit_id"].startswith("lq-micro-raw--"))
            path, record = self.cache(selected["work_unit_id"])
            rows[name] = record["result"]["normalization_raw"][name]
            caches[name] = (path, record)
        results = {}
        for requirement in self.evaluations["language_quality"]["requirements"]:
            slug = requirement["id"].split(".", 1)[1]
            if slug not in MICRO_META:
                continue
            title, field, unit, description = MICRO_META[slug]
            single = field.startswith("startup_")
            method = "Lower values score higher: each score is 100 × the smallest archived value among the ten languages ÷ that language's archived value."
            method += " MB-00 supplies the single scored value." if single else " Normalize each of MB-01 through MB-11 separately, then take the unweighted arithmetic mean of the eleven scores."
            if field == "artifact_effective_bytes":
                method += " Effective artifact bytes already include the source runner's 4,096-byte shift."
            if field == "compile_effective_seconds":
                method += " Effective compile seconds already include a spawn-calibration shift, allowing a finite comparison when a language has no separate compilation step."
            result = self.requirement(requirement, (title, description), method)
            result["comparison_notes"] = ["The published run reused certified baseline measurements. The archived effective raw values below reproduce its published scores; score ratios are not universal speed or size ratios between languages."]
            if not single:
                result["comparison_notes"].append("Different languages can be best on different workloads. Each workload has equal score weight, so a very long workload does not dominate the average merely because it takes more seconds.")
            cells = ["mb00"] if single else list(WORKLOADS)
            values = {
                cell: {name: float(raw[field] if single else raw["workloads"][cell][field]) for name, raw in rows.items()}
                for cell in cells
            }
            best = {cell: min(v.values()) for cell, v in values.items()}
            scores = {name: {cell: 100 * best[cell] / values[cell][name] for cell in cells} for name in rows}
            for name in rows:
                _check_score(mean(scores[name].values()), requirement["scores"][self.by_name[name]["id"]], f"{requirement['id']}/{name} raw")
            for language in self.selected(requirement):
                name = language["name"]
                row = self.language(requirement, language)
                path, cached = caches[name]
                if single:
                    raw = values["mb00"][name]
                    row["explanation"].append(f"The archived MB-00 value is {_n(raw, 9)} {unit}. The cohort minimum is {_n(best['mb00'], 9)} {unit}, so 100 × {_n(best['mb00'], 9)} ÷ {_n(raw, 9)} = {row['score']:.2f}.")
                    row["facts"] = [{"label": "MB-00 archived value", "value": f"{_n(raw, 9)} {unit}"}, {"label": "Cohort minimum", "value": f"{_n(best['mb00'], 9)} {unit}"}]
                else:
                    cell_scores = scores[name]
                    row["explanation"].append(f"The eleven workload scores sum to {_n(sum(cell_scores.values()), 4)}. Their unweighted mean is {row['score']:.2f}/100. Every value and corresponding score contribution is shown below.")
                    strongest = max(cells, key=cell_scores.get)
                    weakest = min(cells, key=cell_scores.get)
                    row["explanation"].append(f"Its highest contribution is {strongest.upper()} ({WORKLOADS[strongest]}), {cell_scores[strongest]:.2f}; its lowest is {weakest.upper()} ({WORKLOADS[weakest]}), {cell_scores[weakest]:.2f}. These measured differences, after workload-by-workload normalization, determine the total.")
                    for cell in cells:
                        row["facts"].append({"label": f"{cell.upper()} · {WORKLOADS[cell]}", "value": f"{_n(values[cell][name], 9)} {unit} → {cell_scores[cell]:.2f}/100"})
                origin = cached["result"].get("evidence", {}).get("source_run_id", cached.get("provenance", {}).get("run_id", "the recorded baseline"))
                row["caveats"].append(f"These raw inputs originated in {origin} and were reused by the published run. The retained values describe that benchmark configuration and are not a fresh measurement of a later release.")
                if field.startswith("compile_"):
                    row["caveats"].append("The retained normalization input is effective compile time. The separate unshifted time and calibration samples are not included in this compact cache record.")
                row["sources"] = [self.source(path, "Archived mechanical measurements selected by this run"), self.source(f"{self.run_rel}/provenance.json", "Run-to-cache provenance"), self.source("benchmark/template/scripts/micro_measure.py", "Normalization implementation at the source snapshot")]
                result["languages"].append(row)
            results[requirement["id"]] = result
        return results

    def safety_requirement(self, requirement: dict) -> dict:
        slug = requirement["id"].split(".", 1)[1]
        title, description, method = SAFETY_META[slug]
        result = self.requirement(requirement, (title, description), method)
        result["comparison_notes"] = [
            "The committed run records preserve aggregate mechanical scores and identify the raw workspace artifact, but do not include the per-case verdicts, applicability counts or diagnostic text. The calculation can be described; a claim that a named failing case caused the gap cannot be verified from these retained records.",
            "The source-snapshot detection ladder assigns 100 to compile-time detection or prevention by construction, 90 to static checking before execution, 75 to safe runtime detection, 55 to test failure, 40 to output verification, 20 to a crash, 5 to undefined behavior and 0 to a silent bug. Several safety metrics reuse this evidence with different formulas.",
        ]
        if slug == "debuggability":
            result["comparison_notes"].insert(0, "The scorer explicitly states that the separate frozen 80-session diagnostic-agent protocol was not executed. These published numbers are the diagnostic-evidence proxy above, not a measured human debugging outcome.")
        if slug == "runtime_safety":
            result["comparison_notes"].insert(0, "The denominator depends on how much was rejected before execution. The compact run record omits that denominator and its low-sample flag, which limits direct comparison of these percentages.")
        for language in self.selected(requirement):
            name = language["name"]
            row = self.language(requirement, language)
            path, record, evidence = self.metric_record("language_quality", requirement["id"], name)
            _check_score(record["requirements"][requirement["id"]][name], row["score"], f"{requirement['id']}/{name} retained score")
            row["facts"] = [{"label": "Published mechanical score", "value": f"{row['score']:.2f}/100"}, {"label": "Programs identified by the evidence record", "value": str(evidence["programs_per_language"])}]
            if slug == "silent_bug_resistance":
                complement = round(100 - row["score"], 2)
                row["explanation"].append(f"The recorded {row['score']:.2f} corresponds to approximately {complement:.2f}% of applicable row-weight classified as a silent bug or undefined behavior, using the complement formula. This is a weighted aggregate, not a count of independently observed production bugs.")
                row["facts"].append({"label": "Silent / undefined row-weight implied by the score", "value": f"Approximately {complement:.2f}%"})
            elif slug == "implementation_robustness":
                complement = round(100 - row["score"], 2)
                row["explanation"].append(f"The published {row['score']:.2f} corresponds to approximately {complement:.2f}% flagged toolchain-failure row-weight. A full score here reports that narrow aggregate; runtime crashes or incorrect outputs are assessed by other requirements.")
                row["facts"].append({"label": "Toolchain-failure row-weight implied by the score", "value": f"Approximately {complement:.2f}%"})
            elif slug == "type_safety":
                row["explanation"].append(f"The retained runner result assigns {row['score']:.2f} under the equal blend of type-hazard stage credit and static-guarantee coverage. It does not preserve the separate TS_stage and TS_static values, so the share of this score attributable to each component cannot be recovered from the committed summary.")
                row["facts"].append({"label": "Prescribed type-hazard set", "value": "6 hazards · 8 case-variant rows · 50% stage / 50% static"})
            elif slug == "memory_safety":
                row["explanation"].append(f"The published integrity-preservation rate is {row['score']:.2f}%. The formula rewards the implementation's intervention on storage hazards, including safe runtime diagnosis; an uncontrolled crash receives no integrity-preservation credit. The compact evidence does not identify which hazards received credit.")
                row["facts"].append({"label": "Prescribed storage-hazard set", "value": "9 equally weighted hazards · 11 case-variant rows"})
            elif slug == "runtime_safety":
                row["explanation"].append(f"The runner reports {row['score']:.2f}% safe-or-prevented row-weight among the applicable weight reaching execution. The retained result omits the numerator and denominator, so this percentage cannot establish how many cases reached runtime or which checks account for it.")
            elif slug == "debuggability":
                row["explanation"].append(f"The retained mechanical result is {row['score']:.2f} for the diagnostic-evidence proxy. The source implementation rewards hazard identification, source locations and stable fault keys, but the compact record omits their individual A1/A2/A3 means and the diagnostic reports needed to attribute the exact difference.")
                row["facts"].append({"label": "Scored diagnostic components", "value": "Hazard match · source position · stable fault key"})
            else:
                count = {"early_error_detection": 26, "boundary_value_safety": 11, "adversarial_input_robustness": 7}[slug]
                row["explanation"].append(f"The recorded {row['score']:.2f} is detection-stage credit averaged over the applicable cases in the prescribed {count}-hazard set. More prevention or earlier diagnosis earns more credit, while crashes and plausible wrong results earn less. The per-case stages needed to identify this language's particular contributing failures were not retained in the repository summary.")
                row["facts"].append({"label": "Prescribed equally weighted hazard set", "value": str(count)})
            row["caveats"] = ["Per-case raw observations are referenced by artifact path and hash, but are not embedded in the committed evidence. Case-level causal claims and exact applicable denominators are therefore unavailable here."]
            row["sources"] = [self.source(path, "Published mechanical result and raw-evidence reference"), self.source("benchmark/template/scripts/adversarial_measure.py", "Scorer implementation at the source snapshot"), self.source("benchmark/template/methodology-assets/language_quality/adversarial_cases.json", "Case definitions and detection credits at the source snapshot")]
            if slug in ("type_safety", "memory_safety", "debuggability"):
                row["sources"].append(self.source(f"benchmark/template/methodology-assets/language_quality/{slug}.json", "Metric definition at the source snapshot"))
            result["languages"].append(row)
        return result

    def semantic_compression(self) -> dict:
        evaluation = self.evaluations["semantic_compression"]
        config = _load(self.core / "benchmark/template/config/aggregation.json")["evaluations"]["semantic_compression"]
        rules = config["recompute_from_evidence"]["metrics"]
        coverage_path = self.run / "evidence/semantic_compression/system-sc-capability-coverage.json"
        coverage = _load(coverage_path)["evidence"]["languages"]
        universe = _load(self.core / "benchmark/template/methodology-assets/semantic_compression/capability_universe.json")
        probes = {p["probe_id"]: p for p in universe["probes"]}
        generations = {l["name"]: _load(self.core / f"benchmark/cache/v1/semantic-compression/{l['id']}/generation.json") for l in self.languages}
        output = []
        for requirement in evaluation["requirements"]:
            rid = requirement["id"]
            slug = rid.split(".", 1)[1]
            if slug == "capability_coverage":
                result = self.requirement(requirement, SC_META[slug], "Score = 100 × awarded capability points ÷ 88 fixed points. Each of the 44 probes is worth two points: FULL support receives two, PARTIAL one and NONE zero. Every probe remains in the coverage denominator.")
                result["comparison_notes"] = ["Coverage follows the run's final support ledger. A NONE or PARTIAL label describes the exact prescribed probe, rather than a claim that every related programming task is impossible in that language."]
                for language in self.selected(requirement):
                    name = language["name"]
                    row = self.language(requirement, language)
                    evidence = coverage[name]
                    levels = evidence["levels"]
                    counts = Counter(levels.values())
                    awarded = evidence["awarded_capability_points"]
                    total = evidence["total_capability_points"]
                    _check_score(100 * awarded / total, row["score"], f"{rid}/{name} coverage")
                    if 2 * counts["FULL"] + counts["PARTIAL"] != awarded:
                        raise ValueError(f"Coverage point ledger differs: {name}")
                    row["explanation"].append(f"The final ledger records {counts['FULL']} FULL, {counts['PARTIAL']} PARTIAL and {counts['NONE']} NONE probes. That awards {_n(awarded)} of {_n(total)} capability points: 100 × {_n(awarded)} ÷ {_n(total)} = {row['score']:.2f}.")
                    for level in ("NONE", "PARTIAL"):
                        entries = [f"{p}: {probes[p]['title']}" for p, value in levels.items() if value == level]
                        if entries:
                            row["explanation"].append(f"Recorded {level} probes: " + "; ".join(entries) + ".")
                    row["facts"] = [{"label": "Awarded / fixed capability points", "value": f"{_n(awarded)} / {_n(total)}"}, {"label": "FULL / PARTIAL / NONE probes", "value": f"{counts['FULL']} / {counts['PARTIAL']} / {counts['NONE']}"}]
                    row["sources"] = [self.source(coverage_path, "Run's final per-probe support ledger"), self.source(f"{self.run_rel}/audit/semantic_compression.json", "Recorded support adjudications"), self.source("benchmark/template/methodology-assets/semantic_compression/capability_universe.json", "Probe definitions at the source snapshot")]
                    output_prose = [*row["explanation"]]
                    row["explanation"] = [_plain(p) for p in output_prose]
                    result["languages"].append(row)
                output.append(result)
                continue

            rule = rules[rid]
            blocks = {name: self.metric_record("semantic_compression", rid, name)[2] for name in self.by_name}
            raw = {name: float(generations[name]["normalization_raw"][rid]) for name in self.by_name}
            common, numerator, denominator, per_probe = [], {}, {}, {}
            if rule["reduce"] == "ratio":
                numerators = {name: _per_probe(block, rule["numerator"]) for name, block in blocks.items()}
                denominators = {name: _per_probe(block, rule["denominator"]) for name, block in blocks.items()}
                common = sorted(set.intersection(*(set(numerators[n]) & set(denominators[n]) for n in blocks)))
                for name in blocks:
                    numerator[name] = sum(numerators[name][p] for p in common)
                    denominator[name] = sum(denominators[name][p] for p in common)
                    if not math.isclose(numerator[name] / denominator[name], raw[name], abs_tol=1e-9):
                        raise ValueError(f"Semantic density raw reconstruction differs: {name}")
            elif rule["reduce"] != "language_ratio":
                per_probe = {name: _per_probe(block, rule["fields"]) for name, block in blocks.items()}
                common = sorted(set.intersection(*(set(v) for v in per_probe.values())))
                for name, values in per_probe.items():
                    numbers = [values[p] for p in common]
                    if rule["reduce"] == "mean_log2":
                        numbers = [math.log2(max(v, 1)) for v in numbers]
                    if not math.isclose(mean(numbers), raw[name], abs_tol=1e-9):
                        raise ValueError(f"{rid}/{name}: common-basis raw differs from generation")
            low, high = min(raw.values()), max(raw.values())
            high_good = rule["direction"] == "higher_is_better"
            formula = "100 × (raw − cohort minimum) ÷ (cohort maximum − cohort minimum)" if high_good else "100 × (cohort maximum − raw) ÷ (cohort maximum − cohort minimum)"
            method = "The published reconstruction uses min–max normalization: " + formula + "."
            if common:
                method += f" The raw calculation uses the {len(common)} probes with a retained per-probe value in every language, from the full 44-probe universe."
            else:
                method += " Raw capability efficiency divides the submitted complexity-unit numerator by the final reconciled supported-capability points."
            result = self.requirement(requirement, SC_META[slug], method)
            result["comparison_notes"] = ["These scores are relative to the ten-language cohort. A 100 marks the best recorded raw value in that cohort; it does not mean the language has no complexity, ambiguity, lookups or hidden behavior.", "The published runner and aggregation configuration use min–max scaling. The source snapshot's scoring/constants.json describes different ratio families; those constants do not reproduce these published Semantic Compression scores."]
            if slug == "semantic_locality":
                result["comparison_notes"].insert(0, "Comparability limit: Quidra's worker submitted estimated whole-number summaries per probe, while Zig's worker submitted fractional averages per semantic site. The runner averaged the submitted numbers on the common probes. The numerical gap therefore includes differing annotation granularity, and cannot by itself establish that Zig requires this proportion fewer actual lookups.")
            for name in raw:
                computed = 100 if high == low else 100 * ((raw[name] - low) if high_good else (high - raw[name])) / (high - low)
                _check_score(computed, requirement["scores"][self.by_name[name]["id"]], f"{rid}/{name} min-max")
            for language in self.selected(requirement):
                name = language["name"]
                row = self.language(requirement, language)
                path, record, block = self.metric_record("semantic_compression", rid, name)
                row["facts"] = [{"label": "Raw value used for publication", "value": _n(raw[name], 9)}, {"label": "Cohort minimum / maximum raw", "value": f"{_n(low, 9)} / {_n(high, 9)}"}]
                if slug == "semantic_density":
                    row["explanation"].append(f"The common-basis annotations contain {_n(numerator[name])} locally explicit facts across {_n(denominator[name])} lexical tokens. Their ratio is {_n(raw[name], 9)} facts per token; min–max scaling produces {row['score']:.2f}.")
                    row["facts"].append({"label": "Common-basis facts / tokens", "value": f"{_n(numerator[name])} / {_n(denominator[name])} across {len(common)} probes"})
                    if "F10.P1" in common:
                        example = next(e for e in _probe_rows(block)["F10.P1"] if isinstance(e, dict) and "fragment" in e)
                        facts = _row_number(example, rule["numerator"])
                        tokens = _row_number(example, rule["denominator"])
                        row["explanation"].append(f"For the integer-narrowing probe F10.P1, the worker counted {_n(facts)} locally explicit facts in {_n(tokens)} tokens. Its recorded fragment is: {_plain(example['fragment'])}. This concrete declaration/conversion form contributes to the fact-per-token ratio; the overall number also includes the other common probes.")
                elif slug == "semantic_determinacy":
                    branching = [(p, per_probe[name][p]) for p in common if per_probe[name][p] > 1]
                    row["explanation"].append(f"The mean of log2(B) is {_n(raw[name], 9)} bits across {len(common)} common probes, where B is the worker's count of compatible interpretations. Min–max inversion produces {row['score']:.2f}.")
                    row["explanation"].append("The recorded branching probes are " + "; ".join(f"{p} ({probes[p]['title']}): B = {_n(b)}" for p, b in branching) + "." if branching else "Every common-basis probe was annotated B = 1, so the mean log2 branching is zero.")
                    row["facts"].append({"label": "Common probes with B greater than 1", "value": f"{len(branching)} / {len(common)}"})
                    for probe in ([p for p, _ in branching] or ["F05.P1"]):
                        comment = _probe_comment(block, probe)
                        if comment:
                            row["explanation"].append(f"Worker reasoning for {probe}: {comment}")
                elif slug in ("semantic_locality", "hidden_semantic_cost"):
                    total = sum(per_probe[name][p] for p in common)
                    label = "submitted lookup values" if slug == "semantic_locality" else "hidden-behavior counts"
                    row["explanation"].append(f"The {label} sum to {_n(total)} across {len(common)} common probes. Dividing by {len(common)} gives {_n(raw[name], 9)}; min–max inversion produces {row['score']:.2f}.")
                    row["facts"].append({"label": "Sum of submitted probe values / common probes", "value": f"{_n(total)} / {len(common)}"})
                    nonzero = [(p, per_probe[name][p]) for p in common if per_probe[name][p] > 0]
                    row["explanation"].append("Examples of nonzero recorded contributions: " + "; ".join(f"{p} ({probes[p]['title']}): {_n(v)}" for p, v in nonzero[:4]) + ".")
                    if slug == "semantic_locality":
                        row["caveats"].append("The submitted value's granularity is part of this comparison: whole per-probe counts and per-site averages coexist in the retained worker evidence. The final score does not correct that difference.")
                        if name == "Quidra":
                            categories = block["lookup_category_used_per_flagged_probe"]
                            for probe in ("F01.P1", "F17.P1"):
                                row["explanation"].append(f"The worker assigns {probe} one lookup for: {_plain(categories[probe])}.")
                            row["caveats"].append("The Quidra worker explicitly describes its lookup values as estimates of the dominant nonlocal category, rather than fully itemized counts for each semantic site.")
                        if name == "Zig":
                            examples = block["illustrative_site_reasoning_examples"]
                            for probe in ("F03.P1", "F05.P1"):
                                row["explanation"].append(f"Worker reasoning for {probe}: {_plain(examples[probe])}")
                    else:
                        for probe in ("F10.P1", "F06.P1"):
                            comment = _probe_comment(block, probe)
                            if probe in common and comment:
                                row["explanation"].append(f"Worker reasoning for {probe}, recorded count {_n(per_probe[name][probe])}: {comment}")
                else:
                    points = coverage[name]["awarded_capability_points"]
                    units = raw[name] * points
                    found_units = []
                    pattern = re.compile(rule["numerator_pattern"], re.I)
                    def collect(node):
                        if isinstance(node, dict):
                            for key, value in node.items():
                                if pattern.search(key) and isinstance(value, (float, int)):
                                    found_units.append(float(value))
                                collect(value)
                        elif isinstance(node, list):
                            for value in node:
                                collect(value)
                    collect(block)
                    if not found_units or not math.isclose(found_units[0], units, abs_tol=1e-8):
                        raise ValueError(f"{name}: complexity numerator is not supported by the worker evidence")
                    row["explanation"].append(f"The worker recorded {_n(units)} semantic complexity units. The final support ledger awards {_n(points)} capability points, so the raw value is {_n(units)} ÷ {_n(points)} = {_n(raw[name], 9)} units per point. Min–max inversion produces {row['score']:.2f}.")
                    row["facts"].append({"label": "Complexity units / final supported points", "value": f"{_n(units)} / {_n(points)}"})
                    for probe in ("F17.P1", "F19.P1"):
                        example = next(e for e in _probe_rows(block)[probe] if isinstance(e, dict) and "complexity" in e)
                        vector = example["complexity"]
                        forms = vector.get("distinct_syntax_forms", vector.get("forms", 0))
                        context = vector.get("context_dependent_rules", vector.get("context", 0))
                        implicit = vector.get("implicit_rules", vector.get("implicit", 0))
                        exceptions = vector.get("documented_semantic_exceptions", vector.get("exceptions", 0))
                        if forms + context + implicit + exceptions != vector["total"]:
                            raise ValueError(f"{name}/{probe}: complexity example does not sum")
                        recorded_basis = example.get("citation") or example.get("fragment_form")
                        row["explanation"].append(f"For {probe} ({probes[probe]['title']}), the worker counted {forms} syntax forms + {context} contextual rules + {implicit} implicit rules + {exceptions} semantic exceptions = {vector['total']} complexity units. Its cited basis/fragment is: {_plain(recorded_basis)}.")
                    if name == "Quidra":
                        row["caveats"].append("The worker's provisional formula used 73 support points. The final support ledger awards 72, which is the denominator used by the published reconstruction.")
                    if name == "Swift":
                        row["caveats"].append("The Swift evidence says the complexity counts came from the assessor's structured recollection of documented semantics, without live access to the official reference during annotation. This limits how strongly the apparent efficiency advantage can be interpreted.")
                row["sources"] = [self.source(path, "Retained semantic annotation and provisional worker reasoning"), self.source(f"benchmark/cache/v1/semantic-compression/{language['id']}/generation.json", "Immutable raw inputs and published metric cross-check"), self.source("benchmark/template/config/aggregation.json", "Published reconstruction rules at the source snapshot")]
                if slug == "capability_efficiency":
                    row["sources"].append(self.source(coverage_path, "Final supported-point denominator"))
                row["caveats"].append("These are retained worker annotations reused by the historical run. Worker-local normalized scores and support claims can differ from the reconciled publication; the displayed score always comes from the published breakdown.")
                row["explanation"] = [_plain(p) for p in row["explanation"]]
                result["languages"].append(row)
            output.append(result)
        return {
            "id": "semantic_compression",
            "introduction": "This historical evaluation compares how explicitly and locally the benchmark's programs communicate meaning, while retaining a separate penalty for unsupported capabilities. Four quality metrics are reconstructed from the 31 probes common to all ten retained worker records; coverage keeps all 44 probes and 88 possible points. The annotations and their comparability limits are part of the evidence, so the explanations below distinguish the published arithmetic from broader claims about language design.",
            "aggregation": "Quality Q = 20% density + 25% determinacy + 20% locality + 20% hidden-cost score + 15% capability efficiency. The evaluation score is the harmonic mean 2 × Q × C ÷ (Q + C), where C is capability coverage. Both the quality component and coverage must remain strong to obtain a high overall score.",
            "requirements": output,
        }


def build(core: Path, site_data: dict, source_ref: str) -> list[dict]:
    """Return all 46 requirement analyses for the three assigned evaluations."""
    builder = _Builder(core, site_data, source_ref)
    semantic = builder.semantic_compression()
    micro = builder.micro_requirements()
    quality_requirements = []
    for requirement in builder.evaluations["language_quality"]["requirements"]:
        if requirement["id"] in micro:
            quality_requirements.append(micro[requirement["id"]])
        elif requirement["category"] == "language_development":
            quality_requirements.append(builder.rubric_requirement("language_quality", requirement))
        else:
            quality_requirements.append(builder.safety_requirement(requirement))
    quality = {
        "id": "language_quality",
        "introduction": "The published Language Quality evaluation combines three different kinds of evidence: archived mechanical measurements, judgments under an input-hash-verified design rubric, and aggregate adversarial-case results. The mechanical cache permits exact reconstruction of the performance and resource scores. The committed safety summaries omit individual case verdicts, so those sections explain the scoring rule and the limit on causal attribution. Every Quidra result here describes the historical v0.3.0 benchmark, including certified baseline measurements reused by that run.",
        "aggregation": "The overall score is 25% Performance + 18.75% Resource / Distribution + 25% Language / Development + 31.25% Safety / Robustness. Within each category, the applicable metric scores have equal weight. This preserves the distinction between intrinsic language/implementation quality and ecosystem maturity.",
        "requirements": quality_requirements,
    }
    ecosystem = {
        "id": "ecosystem",
        "introduction": "These results describe the evidence snapshot of 23 September 2026, not the ecosystem today. Workers' preserved findings were recertified into five fixed components per requirement, and the runner converted levels into points. The rubric file linked below matches the input hash recorded for each selected worker. Low absence scores refer to evidence obtained under the benchmark's fixed retrieval policy; they are not a new survey of present-day packages, tools or adoption.",
        "aggregation": "External Ecosystem / Adoption and Toolchain / Developer Ecosystem Maturity each contribute 50%. The five external requirements have equal weight within their category, as do the ten tooling requirements within theirs. Each individual requirement totals five component judgments worth at most 20 points each.",
        "requirements": [builder.rubric_requirement("ecosystem", r) for r in builder.evaluations["ecosystem"]["requirements"]],
    }
    return [semantic, quality, ecosystem]
