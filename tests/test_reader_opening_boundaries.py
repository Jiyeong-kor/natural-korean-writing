"""보충 사례 형식과 이전 입력 보존을 검사하며 생성 문장 품질은 판정하지 않습니다."""

import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_evals as harness


CASE_PATH = ROOT / "evals" / "supplemental" / "reader-opening-boundaries.json"
CASE_IDS = (
    "application-whole-answer-logic-baseline-001",
    "application-opening-scene-preservation-001",
    "reader-continuity-preservation-001",
)

# 28937df4101e79e2c1ccfe769f22ff354efe1720의
# evals/supplemental/application-whole-answer-logic.json에 있는 원본 사례입니다.
# ID만 제외한 객체를 키 정렬, UTF-8, 공백 없는 JSON으로 직렬화해 계산했습니다.
ORIGINAL_CASE_SHA256 = "0774a66055b48722c4a3b9ceaad660ad4fe3863a63b15fcebb6e85213f73dfa8"


class ReaderOpeningBoundaryTests(unittest.TestCase):
    def load_cases(self):
        body = CASE_PATH.read_bytes()
        self.assertFalse(body.startswith(b"\xef\xbb\xbf"))
        return json.loads(body.decode("utf-8", errors="strict"))

    def test_supplemental_schema_and_ids_stay_separate_from_core_cases(self):
        cases = self.load_cases()
        self.assertIsInstance(cases, list)
        self.assertEqual(tuple(case["id"] for case in cases), CASE_IDS)
        baseline = harness.load_cases(ROOT)
        self.assertEqual(len(baseline), 50)
        other_ids = {case["id"] for case in baseline}
        for path in CASE_PATH.parent.glob("*.json"):
            if path != CASE_PATH:
                other_ids.update(case["id"] for case in json.loads(
                    path.read_text(encoding="utf-8", errors="strict")))
        self.assertTrue(other_ids.isdisjoint(CASE_IDS))
        self.assertNotIn("supplemental/reader-opening-boundaries.json", harness.CASE_COUNTS)
        for case in cases:
            with self.subTest(case=case["id"]):
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
                    self.assertTrue(case[field])
                    self.assertTrue(all(isinstance(item, str) and item for item in case[field]))
                applicable = case["applicable_rubric"]
                self.assertEqual(len(applicable), len(set(applicable)))
                self.assertLessEqual(set(applicable), set(harness.RUBRIC))

    def test_original_case_is_preserved_except_for_new_id(self):
        original = self.load_cases()[0]
        self.assertEqual(original["id"], CASE_IDS[0])
        body = json.dumps(
            {key: value for key, value in original.items() if key != "id"},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(hashlib.sha256(body).hexdigest(), ORIGINAL_CASE_SHA256)


if __name__ == "__main__":
    unittest.main()
