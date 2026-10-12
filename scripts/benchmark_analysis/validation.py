"""Checks that the narrative explains exactly the scores the overview publishes."""
from __future__ import annotations

import math
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

CORE_URL = "https://github.com/quidra-lang/quidra/"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def score(value, label: str) -> float:
    require(isinstance(value, (float, int)) and not isinstance(value, bool)
            and math.isfinite(value) and 0 <= value <= 100, f"{label}: invalid 0–100 score")
    return float(value)


def comparison_ids(requirement: dict, languages: list[dict]) -> list[str]:
    """Compare with the best *published row*, preserving all ties and real zeros."""
    targets = [language["id"] for language in languages if language["name"] == "Quidra"]
    require(len(targets) == 1, "expected exactly one Quidra language")
    quidra = targets[0]
    require(len(languages) >= 2, "a comparison needs another language")
    values = requirement.get("scores", {})
    for language in languages:
        require(language["id"] in values, f"{requirement['id']}: missing score for {language['id']}")
        score(values[language["id"]], f"{requirement['id']} / {language['id']}")
    peers = [language["id"] for language in languages if language["id"] != quidra]
    highest = max(values[peer] for peer in peers)
    return [quidra] + [peer for peer in peers if values[peer] == highest]


def nonempty(value, label: str) -> None:
    require(isinstance(value, str) and bool(value.strip()), f"{label}: expected nonempty text")


def text_list(value, label: str, *, minimum: int = 0) -> None:
    require(isinstance(value, list) and len(value) >= minimum, f"{label}: missing text list")
    for text in value:
        nonempty(text, label)


def validate_analysis(site: dict, analysis: dict, core: Path | None = None) -> None:
    require(analysis.get("schema_version") == 1, "unsupported analysis schema")
    for key in ("run_id", "evaluated_commit"):
        require(analysis.get(key) == site[key], f"analysis {key} differs from published scores; regenerate both files")
    source_commit = analysis.get("source_commit", "")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", source_commit)), "analysis must pin its source commit")
    expected_evaluations = site["evaluations"]
    evaluations = analysis.get("evaluations", [])
    require([e["id"] for e in evaluations] == [e["id"] for e in expected_evaluations],
            "analysis evaluation set/order differs from published scores")
    language_names = {language["id"]: language["name"] for language in site["languages"]}
    for evaluation, published in zip(evaluations, expected_evaluations):
        label = evaluation["id"]
        nonempty(evaluation.get("introduction"), label + " introduction")
        nonempty(evaluation.get("aggregation"), label + " aggregation")
        requirements = evaluation.get("requirements", [])
        require([r["id"] for r in requirements] == [r["id"] for r in published["requirements"]],
                f"{label}: analysis must cover every published requirement in order")
        for requirement, row in zip(requirements, published["requirements"]):
            row_label = f"{label} / {row['id']}"
            for key in ("title", "description", "method"):
                nonempty(requirement.get(key), f"{row_label} {key}")
            text_list(requirement.get("comparison_notes"), row_label + " comparison notes")
            participants = requirement.get("languages", [])
            require([p["id"] for p in participants] == comparison_ids(row, site["languages"]),
                    f"{row_label}: explain Quidra and every tied highest-scoring other language")
            for participant in participants:
                identity = participant["id"]
                participant_label = f"{row_label} / {identity}"
                require(participant.get("name") == language_names[identity], participant_label + ": wrong language name")
                require(score(participant.get("score"), participant_label) == row["scores"][identity],
                        participant_label + ": narrative score differs from published score")
                text_list(participant.get("explanation"), participant_label + " explanation", minimum=1)
                text_list(participant.get("caveats"), participant_label + " caveats")
                require(isinstance(participant.get("facts"), list), participant_label + ": missing facts list")
                for fact in participant["facts"]:
                    nonempty(fact.get("label"), participant_label + " fact label")
                    nonempty(fact.get("value"), participant_label + " fact value")
                sources = participant.get("sources", [])
                require(isinstance(sources, list) and bool(sources), participant_label + ": explanation needs sources")
                pinned = False
                for source in sources:
                    nonempty(source.get("label"), participant_label + " source label")
                    url = source.get("url", "")
                    require(url.startswith("https://"), participant_label + ": source must use HTTPS")
                    if url.startswith(CORE_URL):
                        path = unquote(urlsplit(url).path).split("/", 5)
                        require(len(path) == 6 and path[3] in ("blob", "tree") and path[4] == source_commit,
                                participant_label + ": Core sources must use the pinned source commit")
                        pinned = True
                        if core is not None:
                            relative = Path(path[5])
                            require(not relative.is_absolute() and ".." not in relative.parts,
                                    participant_label + ": invalid source path")
                            require((core / relative).exists(), participant_label + f": missing source {relative}")
                require(pinned, participant_label + ": include a pinned benchmark evidence source")


def validate_source_scores(site: dict, core: Path) -> None:
    """Compare every displayed score with the selected run, not worker proposals."""
    import json
    by_name = {language["name"]: language["id"] for language in site["languages"]}
    for evaluation in site["evaluations"]:
        path = core / "benchmark" / site["run_id"] / "breakdown" / (evaluation["id"] + ".json")
        source = json.loads(path.read_text(encoding="utf-8"))
        rows = source["requirements"]
        require([row["requirement_id"] for row in rows] == [row["id"] for row in evaluation["requirements"]],
                f"{evaluation['id']}: source requirement set/order changed")
        for row, published in zip(rows, evaluation["requirements"]):
            expected = {by_name[entry["language"]]: entry["score"] for entry in row["ranking"]}
            require(expected == published["scores"], f"{published['id']}: overview differs from source breakdown")
