"""Check fixture identity and isolation only; do not run or judge model outputs."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_evals as harness


# Source: fc2d3ffdff3388771d30de08254bdb4a6e4478e1, not the moving branch name.
IMPORTED_SHA256 = {
    "evals/supplemental/local-edit-boundary.json": "5bfd868a474190d9e18c9e39b966bc1fd696c8137c496704aec690288b609fab",
    "evals/supplemental/reader-information-order.json": "899648b9e4e4cb62282f7a1b5a9d927c57a358d4c931c3fef5c8d8a4137d1615",
}
IMPORTED_CASE_IDS = {
    "local-edit-boundary.json": (
        "local-edit-whole-review-001",
        "local-edit-outside-finding-001",
        "local-edit-expanded-scope-001",
        "local-edit-ending-modality-001",
    ),
    "reader-information-order.json": (
        "reader-order-late-context-001",
        "reader-order-shared-visible-context-001",
        "reader-order-deliberate-reveal-001",
        "reader-order-missing-evidence-001",
        "reader-order-expert-shared-knowledge-001",
        "reader-order-moved-version-001",
    ),
}

# Baseline and published evidence at 2419612d3deebf1913ca596af400955cb5d53846.
# These byte-level checks must not be updated to accommodate a model's output.
BASELINE_SHA256 = {
    "evals/core.json": "cb8d90c736fea63e96594f858688bc961a62fc1e0faaf1e0391fbb8daa063e50",
    "evals/approved-copy.json": "19fa0ad6b1fa49cc37544c600ecb38df2b3e84287b6e1f87b4f5c48799019bc1",
    "evals/punctuation.json": "a022b97030f8f25a1e6a827d3d8573a966e257f9f8e283a15a7e02ab58916250",
    "evals/context.json": "5c5e0155ffa6b9d3b721ffbb8ba321633754d1707abcaca2373871a9f8fafa9d",
    "evals/pragmatics.json": "29ba8eb9514b5b06cf45702ec99ecce46ffa7d1741d22d65203505ecbf629c77",
}
ARCHIVED_EVIDENCE_SHA256 = {
    "evals/runs/v0.1.0.jsonl": "37f4843faf9071a1e2840dfbff6c2129ecb875277fe1e87f424ca948c45e5512",
    "evals/results-v0.1.0.md": "8c3c13f41ba13e9095b9c967234b4fd14a4d976b11f5c3d395e8d67ff18a63ff",
    "evals/compatibility-v0.1.0.json": "2420cafa38d421fa1d81488c6186997dfc2199a25cfef7e7b3373739b63babe4",
}


class ScopeRegressionTests(unittest.TestCase):
    def assert_preserved_bytes(self, expected_hashes):
        for relative, expected in expected_hashes.items():
            with self.subTest(path=relative):
                body = (ROOT / relative).read_bytes()
                self.assertFalse(body.startswith(b"\xef\xbb\xbf"))
                body.decode("utf-8", errors="strict")
                self.assertEqual(hashlib.sha256(body).hexdigest(), expected)

    def test_imported_cases_match_pinned_branch_bytes(self):
        self.assert_preserved_bytes(IMPORTED_SHA256)

    def test_imported_case_ids_and_schema(self):
        for filename, expected_ids in IMPORTED_CASE_IDS.items():
            path = ROOT / "evals" / "supplemental" / filename
            cases = json.loads(path.read_text(encoding="utf-8", errors="strict"))
            self.assertIsInstance(cases, list)
            self.assertEqual(tuple(case["id"] for case in cases), expected_ids)
            self.assertNotIn(path.relative_to(ROOT / "evals").as_posix(), harness.CASE_COUNTS)
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

    def test_ids_are_unique_across_baseline_and_all_supplemental_cases(self):
        baseline_ids = [case["id"] for case in harness.load_cases(ROOT)]
        supplemental_ids = []
        for path in sorted((ROOT / "evals" / "supplemental").glob("*.json")):
            cases = json.loads(path.read_text(encoding="utf-8", errors="strict"))
            self.assertIsInstance(cases, list)
            supplemental_ids.extend(case["id"] for case in cases)
        duplicates = sorted(
            case_id for case_id, count in Counter(baseline_ids + supplemental_ids).items()
            if count > 1
        )
        self.assertEqual(duplicates, [])
        self.assertTrue(set(baseline_ids).isdisjoint(supplemental_ids))
        self.assertTrue(
            {case_id for ids in IMPORTED_CASE_IDS.values() for case_id in ids}
            <= set(supplemental_ids)
        )

    def test_baseline_stays_at_fifty_unchanged_cases(self):
        self.assertEqual(harness.CASE_COUNTS, {
            "core.json": 24, "approved-copy.json": 2, "punctuation.json": 7,
            "context.json": 10, "pragmatics.json": 7,
        })
        self.assertEqual(len(harness.load_cases(ROOT)), 50)
        self.assert_preserved_bytes(BASELINE_SHA256)

    def test_archived_evidence_bytes_remain_unchanged(self):
        self.assert_preserved_bytes(ARCHIVED_EVIDENCE_SHA256)


if __name__ == "__main__":
    unittest.main()
