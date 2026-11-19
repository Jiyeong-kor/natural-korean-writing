"""Check reviewed predecessor fixtures, not generated Korean quality."""

import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_evals as harness


# The first two files come from PR #4 at e701d69c9de69c1ac52312608d5ea101d91be4a1.
# evidence-selection.json comes from PR #3 at af3368fcc2b94f4bd30c63c4c1ebc68f0a203cc4.
IMPORTED_SHA256 = {
    "application-causal-action.json": "2044019218dac9366b17cc11c0c8d6393775378fe38a727bb1a3ea853c47bd6d",
    "application-trait-initiative.json": "8e8b914033aed1e9c08d6eea745173675097c7a05b4685b3a07d11beeea5a74a",
    "evidence-selection.json": "20e2dbcb3ee0085bdea0c150437bcda33b4c0fb7ee98a5621f3ed4130d79a812",
}
CASE_IDS = {
    "application-causal-action.json": (
        "application-causal-action-reason-001",
        "application-causal-action-summary-001",
        "application-causal-action-onboarding-001",
        "application-causal-action-learning-001",
        "application-causal-action-valid-boundaries-001",
    ),
    "application-trait-initiative.json": (
        "application-trait-evidence-label-001",
        "application-trait-initiative-proposal-001",
        "application-trait-initiative-unknown-001",
    ),
    "evidence-selection.json": (
        "application-evidence-selection-001",
        "context-redundant-tail-001",
    ),
    "predecessor-boundaries.json": (
        "artifact-copy-only-progress-001",
        "proposal-research-state-unknown-001",
    ),
    "agent-workflow.json": (
        "agent-workflow-coordinator-resume-001",
        "agent-workflow-delegated-writer-001",
        "agent-workflow-delegated-reviewer-001",
        "agent-workflow-latest-correction-001",
        "agent-workflow-review-version-001",
        "agent-workflow-unread-source-001",
        "agent-workflow-independent-review-unavailable-001",
        "agent-workflow-short-edit-001",
    ),
}


class PredecessorFeedbackTests(unittest.TestCase):
    def load_cases(self, filename):
        return json.loads((ROOT / "evals" / "supplemental" / filename).read_text(
            encoding="utf-8", errors="strict"))

    def test_imported_cases_match_reviewed_commits_byte_for_byte(self):
        for filename, expected in IMPORTED_SHA256.items():
            with self.subTest(file=filename):
                body = (ROOT / "evals" / "supplemental" / filename).read_bytes()
                self.assertFalse(body.startswith(b"\xef\xbb\xbf"))
                body.decode("utf-8", errors="strict")
                self.assertEqual(hashlib.sha256(body).hexdigest(), expected)

    def test_added_cases_keep_supplemental_schema_and_separate_ids(self):
        baseline_ids = {case["id"] for case in harness.load_cases(ROOT)}
        for filename, expected_ids in CASE_IDS.items():
            cases = self.load_cases(filename)
            self.assertEqual(tuple(case["id"] for case in cases), expected_ids)
            self.assertTrue(baseline_ids.isdisjoint(expected_ids))
            self.assertNotIn(f"supplemental/{filename}", harness.CASE_COUNTS)
            for case in cases:
                with self.subTest(file=filename, case=case["id"]):
                    self.assertEqual(set(case), harness.CASE_FIELDS)
                    self.assertEqual(case["category"], "context")
                    for field in ("id", "category", "context", "instruction", "input"):
                        self.assertIsInstance(case[field], str)
                        self.assertTrue(case[field])
                    self.assertRegex(case["id"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
                    for field in (
                        "must_preserve", "must_include", "must_not_add",
                        "review_points", "critical_failures", "applicable_rubric",
                    ):
                        self.assertIsInstance(case[field], list)
                        self.assertTrue(all(isinstance(item, str) and item for item in case[field]))
                    self.assertTrue(case["must_preserve"])
                    self.assertTrue(case["critical_failures"])
                    applicable = case["applicable_rubric"]
                    self.assertTrue(applicable)
                    self.assertEqual(len(applicable), len(set(applicable)))
                    self.assertLessEqual(set(applicable), set(harness.RUBRIC))

    def test_revision_review_retains_the_three_reviewed_additions(self):
        # Selectively adding the three review points reproduces this PR #3 file.
        # Existing examples and conditions were not replaced with another baseline.
        body = (ROOT / "evals" / "supplemental" / "revision-review.json").read_bytes()
        self.assertEqual(hashlib.sha256(body).hexdigest(),
                         "68ec52e78ed356c110512d9a8eee84e4a09a3ea1516f7c1d9ee1a78e6a3ffec2")
        self.assertEqual(len(self.load_cases("revision-review.json")), 5)

    def test_turn_boundary_case_does_not_equate_final_only_with_full_trace(self):
        case = self.load_cases("predecessor-boundaries.json")[0]
        points = "\n".join(case["review_points"])
        self.assertIn("최종 본문만 수집한 경우", points)
        self.assertIn("확인하지 못한 범위", points)
        self.assertIn("상위 지침이 요구한 진행 안내", points)


if __name__ == "__main__":
    unittest.main()
