"""Regression cases for selecting and explaining the published comparison rows."""
import copy
import unittest

try:
    from benchmark_analysis.validation import comparison_ids, validate_analysis
except ImportError:
    comparison_ids = validate_analysis = None


def fixture():
    languages = [
        {"id": "quidra_v1", "name": "Quidra"},
        {"id": "alpha_v1", "name": "Alpha"},
        {"id": "beta_v1", "name": "Beta"},
        {"id": "gamma_v1", "name": "Gamma"},
    ]
    requirement = {"id": "metric.correctness", "scores": {
        "quidra_v1": 100.0, "alpha_v1": 95.0, "beta_v1": 95.0, "gamma_v1": 70.0,
    }}
    site = {"run_id": "frozen-run", "evaluated_commit": "a" * 40,
            "languages": languages, "evaluations": [{"id": "sample", "requirements": [requirement]}]}
    participants = []
    for language in languages[:3]:
        participants.append({**language, "score": requirement["scores"][language["id"]],
            "explanation": ["Nine of ten trials passed the recorded correctness gate."],
            "facts": [{"label": "Passing trials", "value": "9 / 10"}],
            "sources": [{"label": "Recorded evidence", "url":
                "https://github.com/quidra-lang/quidra/blob/" + "b" * 40 + "/benchmark/evidence.json"}],
            "caveats": []})
    analysis = {"schema_version": 1, "run_id": site["run_id"], "evaluated_commit": site["evaluated_commit"],
        "source_commit": "b" * 40, "evaluations": [{"id": "sample", "introduction": "Recorded trial results.",
            "aggregation": "Weighted mean of the requirement scores.", "requirements": [{
                "id": requirement["id"], "title": "Correctness", "description": "Passing the hidden tests.",
                "method": "100 times the passing-trial fraction.", "comparison_notes": [],
                "languages": participants}]}]}
    return site, analysis


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(comparison_ids), "benchmark comparison selection is not implemented")

    def test_uses_each_requirement_leader_and_excludes_quidra_from_rivals(self):
        site, _ = fixture()
        req = site["evaluations"][0]["requirements"][0]
        self.assertEqual(comparison_ids(req, site["languages"]), ["quidra_v1", "alpha_v1", "beta_v1"])
        req["scores"]["gamma_v1"] = 99.0
        self.assertEqual(comparison_ids(req, site["languages"]), ["quidra_v1", "gamma_v1"])

    def test_keeps_all_published_ties_in_canonical_language_order(self):
        site, _ = fixture()
        req = site["evaluations"][0]["requirements"][0]
        req["scores"]["quidra_v1"] = 0
        req["scores"]["gamma_v1"] = 95.0
        self.assertEqual(comparison_ids(req, site["languages"]), [l["id"] for l in site["languages"]])

    def test_zero_is_a_real_score_not_missing_data(self):
        site, _ = fixture()
        req = site["evaluations"][0]["requirements"][0]
        req["scores"] = {l["id"]: 0 for l in site["languages"]}
        self.assertEqual(len(comparison_ids(req, site["languages"])), 4)

    def test_missing_score_is_rejected_instead_of_silently_selecting_a_rival(self):
        site, _ = fixture()
        req = site["evaluations"][0]["requirements"][0]
        del req["scores"]["alpha_v1"]
        with self.assertRaises(ValueError):
            comparison_ids(req, site["languages"])


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(validate_analysis), "benchmark analysis validation is not implemented")
        self.site, self.analysis = fixture()

    def test_accepts_complete_evidence_matching_the_published_scores(self):
        validate_analysis(self.site, self.analysis)

    def test_rejects_analysis_from_another_run_or_compiler(self):
        for key in ("run_id", "evaluated_commit"):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.analysis)
                changed[key] = "stale"
                with self.assertRaises(ValueError):
                    validate_analysis(self.site, changed)

    def test_rejects_a_missing_requirement(self):
        self.analysis["evaluations"][0]["requirements"] = []
        with self.assertRaises(ValueError):
            validate_analysis(self.site, self.analysis)

    def test_rejects_omitted_tied_winner(self):
        self.analysis["evaluations"][0]["requirements"][0]["languages"].pop()
        with self.assertRaises(ValueError):
            validate_analysis(self.site, self.analysis)

    def test_rejects_a_provisional_score_in_place_of_the_published_score(self):
        self.analysis["evaluations"][0]["requirements"][0]["languages"][0]["score"] = 17
        with self.assertRaises(ValueError):
            validate_analysis(self.site, self.analysis)

    def test_rejects_an_uncited_or_empty_explanation(self):
        for field in ("sources", "explanation"):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.analysis)
                changed["evaluations"][0]["requirements"][0]["languages"][0][field] = []
                with self.assertRaises(ValueError):
                    validate_analysis(self.site, changed)

    def test_rejects_mutable_source_branch_links(self):
        participant = self.analysis["evaluations"][0]["requirements"][0]["languages"][0]
        participant["sources"][0]["url"] = "https://github.com/quidra-lang/quidra/blob/main/benchmark/evidence.json"
        with self.assertRaises(ValueError):
            validate_analysis(self.site, self.analysis)

    def test_rejects_non_finite_scores(self):
        self.site["evaluations"][0]["requirements"][0]["scores"]["alpha_v1"] = float("nan")
        with self.assertRaises(ValueError):
            validate_analysis(self.site, self.analysis)


if __name__ == "__main__":
    unittest.main()
