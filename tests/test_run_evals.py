"""Check synthetic evidence and immutable release records; no model is invoked."""

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_evals as harness


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8", errors="strict", newline="\n",
    )


def make_cases(root: Path) -> None:
    """Write schema-valid synthetic case files for tests only."""
    groups = {name.removesuffix(".json"): [] for name in harness.CASE_COUNTS}

    def case(category, index):
        return {
            "id": f"{category}-{index:03}", "category": category,
            "context": "합성 테스트 문맥", "instruction": "주어진 문장을 그대로 출력하세요.",
            "input": "합성 테스트 원문입니다.", "must_preserve": ["주어진 의미"],
            "must_include": [], "must_not_add": ["새로운 사실"], "review_points": ["의미 보존"],
            "critical_failures": ["의미 변경"], "applicable_rubric": list(harness.RUBRIC),
        }

    for category, count in harness.CORE_CATEGORIES.items():
        groups["core"].extend(case(category, number) for number in range(1, count + 1))
    groups["approved-copy"] = [case("approved-copy", number) for number in (1, 2)]
    groups["punctuation"] = [case("punctuation", number) for number in range(1, 8)]
    groups["context"] = [{**case("context", number), "id": case_id}
                         for number, case_id in enumerate(harness.CONTEXT_CASE_IDS, 1)]
    groups["pragmatics"] = [{**case("pragmatics", number), "id": case_id}
                            for number, case_id in enumerate(harness.PRAGMATICS_CASE_IDS, 1)]
    required = {
        "meaning": "meaning-close-001", "register": "register-honorific-001",
        "approved-copy": "approved-introduction-001",
    }
    for group in groups.values():
        for item in group:
            category = item["category"]
            if category in required and item["id"] == f"{category}-001":
                item["id"] = required[category]
                item["input"], expected = harness.REQUIRED_CASES[item["id"]]
                if expected is not None:
                    item["expected_exact"] = expected
            elif category == "approved-copy":
                item["expected_exact"] = item["input"]
    for name, group in groups.items():
        write_json(root / "evals" / f"{name}.json", group)


def make_envelope(case_id, role):
    return {
        "id": case_id, "role": role, **harness.SETTINGS,
        "attempt_log": [{
            "attempt": 1, "context_id": harness.new_context_id(),
            "runtime_surface": "codex-desktop", "runtime_version": "synthetic-test-runtime",
            "status": "completed", "retry_reason": None,
        }],
    }


def judgment(case):
    return {
        "id": case["id"], "rubric": dict.fromkeys(case["applicable_rubric"], "pass"),
        "critical_failure": False, "reason": "합성 테스트 판정입니다.",
    }


class EvalHarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / ".eval-work"
        make_cases(self.root)
        runtime = self.root / "skills" / "natural-korean-writing"
        runtime.mkdir(parents=True)
        (runtime / "SKILL.md").write_text("# Synthetic skill\n", encoding="utf-8", errors="strict")
        (runtime / "references").mkdir()
        (runtime / "references" / "context-audience-boundary.md").write_text(
            "# Synthetic context reference\n", encoding="utf-8", errors="strict"
        )
        protocol = Path(__file__).resolve().parents[1] / "evals" / "README.md"
        (self.root / "evals" / "README.md").write_bytes(protocol.read_bytes())
        self.cases = harness.load_cases(self.root)
        harness.prepare(self.root)
        self.envelopes = []
        for case in self.cases:
            case_id = case["id"]
            (self.work / "generator" / f"{case_id}.txt").write_text(
                case.get("expected_exact", case["input"]), encoding="utf-8", errors="strict", newline="\n"
            )
            for role in ("reviewer-a", "reviewer-b"):
                write_json(self.work / role / f"{case_id}.json", judgment(case))
            self.envelopes.extend(make_envelope(case_id, role) for role in
                                  ("generator", "reviewer-a", "reviewer-b"))
        self.write_execution()

    def write_execution(self):
        (self.work / "execution.jsonl").write_text(
            "".join(harness._json(item) + "\n" for item in self.envelopes),
            encoding="utf-8", errors="strict", newline="\n",
        )

    def write_judgment(self, role, value):
        write_json(self.work / role / f"{value['id']}.json", value)

    def add_adjudicator(self, case, value):
        self.write_judgment("adjudicator", value)
        self.envelopes.append(make_envelope(case["id"], "adjudicator"))
        self.write_execution()

    def tracked_path(self):
        return self.root / "evals" / "runs" / f"{harness.VERSION}.jsonl"

    def mutate_tracked(self, change):
        rows = harness._read_jsonl(self.tracked_path())
        change(rows)
        self.tracked_path().write_text(
            "".join(harness._json(row) + "\n" for row in rows),
            encoding="utf-8", errors="strict", newline="\n",
        )

    def test_agreement_roundtrip_and_raw_output(self):
        case = self.cases[1]
        output = "첫 문장입니다.\r\n둘째 문장입니다.\n"
        (self.work / "generator" / f"{case['id']}.txt").write_bytes(output.encode("utf-8"))
        records = harness.aggregate(self.root)
        self.assertEqual(len(records), 50)
        self.assertEqual(records[1]["output"], output)
        self.assertTrue(all(row["case_pass"] for row in records))
        self.assertNotIn("id", records[0]["generator"])
        self.assertNotIn("id", records[0]["reviewers"][0])
        harness.check(self.root)
        harness.verify_tracked(self.root)
        self.assertEqual(self.tracked_path().read_bytes().count(b"\n"), 50)

    def test_disagreement_majority_and_failed_case_preserved(self):
        case = self.cases[1]
        second = judgment(case)
        second["rubric"]["natural_korean"] = "fail"
        self.write_judgment("reviewer-b", second)
        third = judgment(case)
        third["rubric"]["natural_korean"] = "fail"
        self.add_adjudicator(case, third)
        records = harness.aggregate(self.root)
        self.assertFalse(records[1]["case_pass"])
        self.assertEqual(records[1]["final_rubric"]["natural_korean"], "fail")
        self.assertFalse(records[1]["critical_failure"])
        harness.check(self.root)
        harness.verify_tracked(self.root)

    def test_critical_failure_vote_and_reason_only_difference(self):
        case = self.cases[0]
        second = judgment(case)
        second["critical_failure"] = True
        self.write_judgment("reviewer-b", second)
        third = judgment(case)
        third["critical_failure"] = True
        self.add_adjudicator(case, third)
        different_reason = judgment(self.cases[1])
        different_reason["reason"] = "표현만 다른 합성 판정입니다."
        self.write_judgment("reviewer-b", different_reason)
        records = harness.aggregate(self.root)
        self.assertTrue(records[0]["critical_failure"])
        self.assertFalse(records[0]["case_pass"])
        self.assertIsNone(records[1]["adjudicator"])

    def test_missing_reviewer_and_generator_outputs(self):
        for role, extension in (("reviewer-a", ".json"), ("reviewer-b", ".json"), ("generator", ".txt")):
            path = self.work / role / (self.cases[0]["id"] + extension)
            original = path.read_bytes()
            with self.subTest(role=role):
                path.unlink()
                with self.assertRaises(ValueError):
                    harness.aggregate(self.root)
                path.write_bytes(original)
        path = self.work / "generator" / f"{self.cases[0]['id']}.txt"
        path.write_text(" \n", encoding="utf-8", errors="strict")
        with self.assertRaises(ValueError):
            harness.aggregate(self.root)

    def test_reviewer_schema_is_exact(self):
        case = self.cases[0]
        mutations = [
            lambda value: value.update(extra="not allowed"),
            lambda value: value.update(id="another-case"),
            lambda value: value.update(critical_failure=0),
            lambda value: value["rubric"].pop("output_format"),
            lambda value: value["rubric"].update(unknown="pass"),
            lambda value: value["rubric"].update(output_format=True),
        ]
        for index, change in enumerate(mutations):
            with self.subTest(index=index):
                value = judgment(case)
                change(value)
                self.write_judgment("reviewer-a", value)
                with self.assertRaises(ValueError):
                    harness.aggregate(self.root)
        self.write_judgment("reviewer-a", judgment(case))
        path = self.work / "reviewer-a" / f"{case['id']}.json"
        text = harness._json(judgment(case))
        path.write_text(text[:-1] + ',"reason":"duplicate"}', encoding="utf-8", errors="strict")
        with self.assertRaises(ValueError):
            harness.aggregate(self.root)

    def test_missing_or_unused_adjudicator_is_rejected(self):
        case = self.cases[0]
        changed = judgment(case)
        changed["critical_failure"] = True
        self.write_judgment("reviewer-b", changed)
        with self.assertRaises(ValueError):
            harness.aggregate(self.root)
        self.add_adjudicator(case, judgment(case))
        self.write_judgment("reviewer-b", judgment(case))
        with self.assertRaises(ValueError):
            harness.aggregate(self.root)

    def test_one_transport_retry_is_recorded(self):
        completed = self.envelopes[0]["attempt_log"][0]
        failed = {**completed, "context_id": harness.new_context_id(),
                  "status": "transport_error", "retry_reason": "connection_reset"}
        completed["attempt"] = 2
        self.envelopes[0]["attempt_log"] = [failed, completed]
        self.write_execution()
        records = harness.aggregate(self.root)
        self.assertEqual(len(records[0]["generator"]["attempt_log"]), 2)
        harness.verify_tracked(self.root)

    def test_output_free_delivery_and_runtime_errors_allow_one_retry(self):
        for status in ("delivery_error", "runtime_error", "transport_error"):
            with self.subTest(status=status):
                envelope = make_envelope(self.cases[0]["id"], "generator")
                completed = envelope["attempt_log"][0]
                failed = {**completed, "context_id": harness.new_context_id(),
                          "status": status, "retry_reason": "verified output-free failure"}
                completed["attempt"] = 2
                envelope["attempt_log"] = [failed, completed]
                actual = harness._validate_envelope(envelope, self.cases[0]["id"], "generator", set())
                self.assertEqual(actual["attempt_log"][0]["status"], status)
                for forbidden in ("quality_failure", "invalid_json", "completed"):
                    failed["status"] = forbidden
                    with self.assertRaises(ValueError):
                        harness._validate_envelope(envelope, self.cases[0]["id"], "generator", set())

    def test_operations_only_changes_preserve_identity_and_first_failure(self):
        case = self.cases[1]
        failed = judgment(case)
        failed["rubric"]["natural_korean"] = "fail"
        for role in ("reviewer-a", "reviewer-b"):
            self.write_judgment(role, failed)
        harness.aggregate(self.root)
        original_records = self.tracked_path().read_bytes()
        original_metadata = (self.work / "run.json").read_bytes()
        identity = harness.compute_evaluation_identity(self.root)
        raw = harness.compute_digest(self.root)
        protocol = self.root / "evals" / "README.md"
        protocol.write_text(harness._read_text(protocol).replace(
            "## 평가 준비\n", "## 평가 준비\n\n운영 절차의 설명만 보완합니다.\n", 1
        ), encoding="utf-8", errors="strict", newline="\n")
        self.assertNotEqual(harness.compute_digest(self.root), raw)
        self.assertEqual(harness.compute_evaluation_identity(self.root), identity)
        harness.check(self.root)
        harness.verify_tracked(self.root)
        self.assertEqual(self.tracked_path().read_bytes(), original_records)
        self.assertEqual((self.work / "run.json").read_bytes(), original_metadata)
        self.assertFalse(harness._read_jsonl(self.tracked_path())[1]["case_pass"])

    def test_normative_or_unclassified_protocol_changes_reject_reuse(self):
        protocol = self.root / "evals" / "README.md"
        original = harness._read_text(protocol)
        metadata = harness._read_json(self.work / "run.json")
        variants = [original.replace(f"## {heading}\n", f"## {heading}\nChanged rule.\n", 1)
                    for heading in harness.NORMATIVE_SECTIONS]
        variants.extend((original + "\n## Unclassified policy\nUnknown impact.\n",
                         original.replace("## 실행 설정\n", "## Unknown settings\n", 1),
                         original.replace("요청한 결과만 출력하세요.", "설명을 추가하세요.", 1)))
        for index, variant in enumerate(variants):
            with self.subTest(variant=index):
                protocol.write_text(variant, encoding="utf-8", errors="strict", newline="\n")
                with self.assertRaises(ValueError):
                    harness._metadata(self.root, metadata, harness.VERSION)

    def test_prompt_settings_and_release_rule_changes_reject_reuse(self):
        metadata = harness._read_json(self.work / "run.json")
        with patch.dict(harness.SETTINGS, {"model": "another-model"}):
            with self.assertRaises(ValueError):
                harness._metadata(self.root, metadata, harness.VERSION)
        with patch.dict(harness.SETTINGS, {"reasoning_effort": "low"}):
            with self.assertRaises(ValueError):
                harness._metadata(self.root, metadata, harness.VERSION)
        renderer = harness.render_adjudicator_prompt
        with patch.object(harness, "render_adjudicator_prompt",
                          side_effect=lambda *args: renderer(*args) + "Changed criterion."):
            with self.assertRaises(ValueError):
                harness._metadata(self.root, metadata, harness.VERSION)
        source = harness._read_text(Path(harness.__file__))
        release = harness._read_text(Path(harness.__file__).with_name("validate_repo.py"))
        original = harness._semantic_code(source, release)
        self.assertNotEqual(original, harness._semantic_code(source, release.replace('(\"core\", 22)', '(\"core\", 21)')))
        changed = source.replace('else "fail"', 'else "pass"', 1)
        self.assertNotEqual(original, harness._semantic_code(changed, release))
        changed = source.replace('"meaning_preservation", "no_unsupported_addition"', '"meaning_changed", "no_unsupported_addition"', 1)
        self.assertNotEqual(original, harness._semantic_code(changed, release))

    def test_record_identity_output_and_judgment_dependency_tampering_fails(self):
        harness.aggregate(self.root)
        original = self.tracked_path().read_bytes()
        mutations = (
            lambda rows: rows[0].update(evaluation_identity="0" * 64),
            lambda rows: rows[0].update(output=rows[0]["output"] + "changed"),
            lambda rows: rows[0]["reviewers"][0].update(reason="changed justification"),
            lambda rows: rows[0]["dependency_sha256"]["prompts"].update(**{"reviewer-a": "0" * 64}),
        )
        for index, change in enumerate(mutations):
            with self.subTest(mutation=index):
                self.tracked_path().write_bytes(original)
                self.mutate_tracked(change)
                with self.assertRaises(ValueError):
                    harness.verify_tracked(self.root)

    def test_release_dependencies_change_identity_but_operational_helpers_do_not(self):
        source = harness._read_text(Path(harness.__file__))
        release = harness._read_text(Path(harness.__file__).with_name("validate_repo.py"))
        original = harness._semantic_code(source, release)
        for name in ("Report", "read_text", "Path", "json", "run_evals"):
            self.assertIn("validate_repo." + name, original)
        metadata = harness._read_json(self.work / "run.json")
        read_text = harness._read_text
        for old, new in (("if not condition:", "if False:"),
                         ('value = path.read_text(encoding="utf-8", errors="strict")',
                          'value = path.read_text(encoding="utf-8", errors="ignore")')):
            with self.subTest(dependency=old):
                changed = release.replace(old, new, 1)
                self.assertNotEqual(original, harness._semantic_code(source, changed))
                with patch.object(harness, "_read_text", side_effect=lambda path: (
                    changed if path == Path(harness.__file__).with_name("validate_repo.py") else read_text(path)
                )):
                    with self.assertRaisesRegex(ValueError, "evaluation identity changed"):
                        harness._metadata(self.root, metadata, harness.VERSION)
        operational = release.replace('capture_output=True,', 'capture_output=False,', 1)
        self.assertNotEqual(release, operational)
        self.assertEqual(original, harness._semantic_code(source, operational))

    def test_legacy_metadata_without_frozen_evidence_is_not_trusted(self):
        metadata = harness._read_json(self.work / "run.json")
        for key in harness.IDENTITY_FIELDS:
            metadata.pop(key)
        metadata.pop("source_protocol")
        with self.assertRaises((ValueError, OSError)):
            harness._metadata(self.root, metadata, harness.VERSION)

    def test_raw_digest_and_metadata_types_are_verified_against_original_snapshot(self):
        metadata = harness._read_json(self.work / "run.json")
        with self.assertRaisesRegex(ValueError, "tested skill digest mismatch against source snapshot"):
            harness._metadata(self.root, {**metadata, "tested_skill_digest": "0" * 64}, harness.VERSION)
        for field in ("tested_skill_digest", "tested_at", "evaluation_identity", "operations_version", "source_protocol"):
            for value in (None, 3, [], {}):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        harness._metadata(self.root, {**metadata, field: value}, harness.VERSION)
        harness.aggregate(self.root)
        snapshot = self.root / "evals" / "runs" / f"{harness.VERSION}.inputs.json"
        self.assertEqual(harness._read_json(snapshot), metadata)
        changed = {**metadata, "tested_skill_digest": "0" * 64}
        write_json(snapshot, changed)
        with self.assertRaisesRegex(ValueError, "tested skill digest mismatch against source snapshot"):
            harness.verify_tracked(self.root)

    def test_public_legacy_evidence_and_original_failed_result(self):
        repository = Path(__file__).resolve().parents[1]
        release_path = os.environ.get("NKW_RELEASE_ROOT")
        self.assertTrue(release_path, "Set NKW_RELEASE_ROOT to a separate v0.1.0 checkout")
        root = Path(release_path).resolve()
        self.assertNotEqual(root, repository, "Historical verification needs a separate checkout")
        revisions = subprocess.run(
            ["git", "rev-parse", "HEAD", "refs/tags/v0.1.0^{commit}"], cwd=root,
            check=True, capture_output=True, text=True, encoding="utf-8", errors="strict", timeout=15,
        ).stdout.splitlines()
        original_commit = "3b602310bec0a42f0648e00b675eed317240e772"
        self.assertEqual(revisions, [original_commit, original_commit])
        for relative in (harness.LEGACY_EVIDENCE, "evals/runs/v0.1.0.jsonl", "evals/results-v0.1.0.md"):
            self.assertTrue(
                (repository / relative).read_bytes() == (root / relative).read_bytes(),
                f"Archived evaluation file changed: {relative}",
            )
        evidence = harness._read_json(root / harness.LEGACY_EVIDENCE)
        harness._metadata(root, evidence["metadata"], harness.VERSION)
        records = harness._read_jsonl(root / "evals/runs/v0.1.0.jsonl")
        harness._verify_legacy_records(root, evidence["metadata"], harness.load_cases(root), records)
        self.assertEqual(len(records), 50)
        self.assertEqual(sum(record["case_pass"] for record in records), 49)
        self.assertFalse(next(record for record in records if record["id"] == "register-casual-001")["case_pass"])
        changed = copy.deepcopy(records)
        changed[0]["output"] += "changed"
        with self.assertRaisesRegex(ValueError, "original legacy output or judgment changed"):
            harness._verify_legacy_records(root, evidence["metadata"], harness.load_cases(root), changed)
        with (
            patch.object(harness, "LEGACY_EVIDENCE_SHA256", "0" * 64),
            self.assertRaisesRegex(ValueError, "legacy compatibility evidence changed"),
        ):
            harness._metadata(root, evidence["metadata"], harness.VERSION)

    def test_retry_limit_order_and_status_are_strict(self):
        base = copy.deepcopy(self.envelopes[0]["attempt_log"][0])
        invalid = [
            [dict(base), dict(base), dict(base)],
            [{**base, "attempt": 2}],
            [dict(base), {**base, "attempt": 2, "context_id": harness.new_context_id()}],
            [{**base, "status": "transport_error", "retry_reason": "connection_reset"}],
            [{**base, "retry_reason": "not allowed after completion"}],
            [{**base, "attempt": True}],
        ]
        for index, attempts in enumerate(invalid):
            with self.subTest(index=index):
                self.envelopes[0]["attempt_log"] = attempts
                self.write_execution()
                with self.assertRaises(ValueError):
                    harness.aggregate(self.root)

    def test_context_ids_are_globally_unique_uuids(self):
        self.envelopes[-1]["attempt_log"][0]["context_id"] = self.envelopes[0]["attempt_log"][0]["context_id"]
        self.write_execution()
        with self.assertRaises(ValueError):
            harness.aggregate(self.root)
        self.envelopes[-1]["attempt_log"][0]["context_id"] = "not-a-uuid"
        self.write_execution()
        with self.assertRaises(ValueError):
            harness.aggregate(self.root)

    def test_execution_settings_and_runtime_metadata_are_required(self):
        original = copy.deepcopy(self.envelopes[0])
        mutations = [
            lambda value: value.update(model="different-model"),
            lambda value: value.update(reasoning_effort="low"),
            lambda value: value.update(sampling="0.2"),
            lambda value: value.update(agent="different-agent"),
            lambda value: value.update(extra="not allowed"),
            lambda value: value["attempt_log"][0].update(runtime_surface="cli"),
            lambda value: value["attempt_log"][0].pop("runtime_version"),
            lambda value: value["attempt_log"][0].update(runtime_version="unknown"),
            lambda value: value["attempt_log"][0].update(runtime_version=""),
        ]
        for index, change in enumerate(mutations):
            with self.subTest(index=index):
                self.envelopes[0] = copy.deepcopy(original)
                change(self.envelopes[0])
                self.write_execution()
                with self.assertRaises(ValueError):
                    harness.aggregate(self.root)

    def test_extra_files_and_duplicate_envelopes_fail(self):
        extra = self.work / "generator" / "extra.txt"
        extra.write_text("extra", encoding="utf-8", errors="strict")
        with self.assertRaises(ValueError):
            harness.aggregate(self.root)
        extra.unlink()
        self.envelopes.append(copy.deepcopy(self.envelopes[0]))
        self.write_execution()
        with self.assertRaises(ValueError):
            harness.aggregate(self.root)

    def test_prompt_packets_hide_conditions_from_generator(self):
        case = {**self.cases[1], "expected_exact": "SECRET_EXPECTED", "review_points": ["SECRET_RUBRIC"],
                "instruction": "최신 요청의 말투와 형식을 유지하세요."}
        prompt = harness.render_generator_prompt(case)
        self.assertNotIn("SECRET", prompt)
        reviewer = harness.render_reviewer_prompt(case, "실제 출력")
        self.assertIn("SECRET_EXPECTED", reviewer)
        self.assertIn("SECRET_RUBRIC", reviewer)
        self.assertIn("요청: 최신 요청의 말투와 형식을 유지하세요.", reviewer)
        self.assertIn("실제 출력", reviewer)
        adjudicator = harness.render_adjudicator_prompt(case, "실제 출력", judgment(case), judgment(case))
        self.assertIn("요청: 최신 요청의 말투와 형식을 유지하세요.", adjudicator)
        template = self.work / "prompts" / "reviewer-a" / f"{self.cases[1]['id']}.txt"
        self.assertIn("{output}", harness._read_text(template))
        generator = self.work / "prompts" / "generator" / f"{self.cases[1]['id']}.txt"
        generator.write_text("changed request", encoding="utf-8", errors="strict")
        with self.assertRaises(ValueError):
            harness.aggregate(self.root)

    def test_prepare_refuses_existing_work_and_creates_no_results(self):
        original = (self.work / "run.json").read_bytes()
        with self.assertRaises(ValueError):
            harness.prepare(self.root)
        self.assertEqual((self.work / "run.json").read_bytes(), original)
        self.assertFalse(self.tracked_path().exists())
        self.assertFalse((self.root / "evals" / f"results-{harness.VERSION}.md").exists())

    def test_reviewers_receive_semantic_and_exact_preservation_boundaries(self):
        boundaries = (
            "조건을 설명한 문장을 출력의 고정 문구로 취급하지 마세요.",
            "보호 대상 밖에서 의미가 같은 표현이나 조사, 어순이 달라진 것만으로 이 항목을 fail로 판정하지 마세요.",
            "null이어도 보호할 개별 원문은 정확히 유지해야 합니다.",
        )
        for case in self.cases:
            reviewer = harness.render_reviewer_prompt(case, "합성 출력")
            adjudicator = harness.render_adjudicator_prompt(
                case, "합성 출력", judgment(case), judgment(case)
            )
            generator = harness.render_generator_prompt(case)
            for boundary in boundaries:
                with self.subTest(case_id=case["id"], boundary=boundary):
                    self.assertTrue(boundary in reviewer, "reviewer is missing a preservation boundary")
                    self.assertTrue(boundary in adjudicator, "adjudicator is missing a preservation boundary")
                    self.assertFalse(boundary in generator, "reviewer policy leaked into generator prompt")

    def test_documented_reviewer_template_matches_execution(self):
        source = Path(__file__).resolve().parents[1] / "evals" / "README.md"
        text = source.read_text(encoding="utf-8", errors="strict")
        documented = text.split("### 평가용 프롬프트\n\n```text\n", 1)[1].split("\n```", 1)[0]
        expected = harness.REVIEWER_TEMPLATE.replace("{{", "{").replace("}}", "}").strip()
        self.assertEqual(documented, expected)

    def test_preservation_clarification_does_not_override_literal_failures(self):
        case = next(case for case in self.cases if case["category"] == "literal")
        failed = judgment(case)
        failed["rubric"]["literal_preservation"] = "fail"
        failed["critical_failure"] = True
        for role in ("reviewer-a", "reviewer-b"):
            self.write_judgment(role, failed)
        records = harness.aggregate(self.root)
        actual = next(row for row in records if row["id"] == case["id"])
        self.assertFalse(actual["case_pass"])
        self.assertTrue(actual["critical_failure"])
        self.assertEqual(actual["final_rubric"]["literal_preservation"], "fail")
        harness.verify_tracked(self.root)

    def test_wrong_prompt_hash_and_nested_extra_id_fail(self):
        harness.aggregate(self.root)
        original = self.tracked_path().read_bytes()
        self.mutate_tracked(lambda rows: rows[0].update(prompt_sha256="0" * 64))
        with self.assertRaises(ValueError):
            harness.verify_tracked(self.root)
        self.tracked_path().write_bytes(original)
        self.mutate_tracked(lambda rows: rows[0]["reviewers"][0].update(id=rows[0]["id"]))
        with self.assertRaises(ValueError):
            harness.verify_tracked(self.root)

    def test_tracked_summary_and_recomputed_bytes_must_match(self):
        harness.aggregate(self.root)
        summary = self.root / "evals" / f"results-{harness.VERSION}.md"
        original = summary.read_bytes()
        summary.write_bytes(original + b"\n")
        with self.assertRaises(ValueError):
            harness.check(self.root)
        with self.assertRaises(ValueError):
            harness.verify_tracked(self.root)
        with self.assertRaises(ValueError):
            harness.aggregate(self.root)
        self.assertEqual(summary.read_bytes(), original + b"\n")

    def test_mixed_metadata_and_changed_source_digest_fail(self):
        harness.aggregate(self.root)
        original = self.tracked_path().read_bytes()
        self.mutate_tracked(lambda rows: rows[1].update(tested_at="2020-01-01T00:00:00Z"))
        with self.assertRaises(ValueError):
            harness.verify_tracked(self.root)
        self.tracked_path().write_bytes(original)
        (self.root / "evals" / "README.md").write_text("changed", encoding="utf-8", errors="strict")
        with self.assertRaises(ValueError):
            harness.check(self.root)
        with self.assertRaises(ValueError):
            harness.verify_tracked(self.root)

    def test_verify_tracked_needs_no_temporary_inputs(self):
        harness.aggregate(self.root)
        self.assertTrue(self.work.resolve().is_relative_to(self.root.resolve()))
        self.work.rename(self.root / "archived-synthetic-inputs")
        harness.verify_tracked(self.root)

    def test_exact_output_release_gate_does_not_rewrite_votes(self):
        index = next(index for index, case in enumerate(self.cases) if case["category"] == "approved-copy")
        case = self.cases[index]
        (self.work / "generator" / f"{case['id']}.txt").write_text(
            "완전 일치하지 않는 합성 출력입니다.", encoding="utf-8", errors="strict"
        )
        records = harness.aggregate(self.root)
        self.assertTrue(records[index]["case_pass"])
        self.assertNotEqual(records[index]["output"], case["expected_exact"])
        harness.verify_tracked(self.root)

    def test_free_rewriting_uses_votes_and_preserves_failed_judgments(self):
        variants = {
            "meaning-close-001": "기획서 전체를 검토해 서로 맞지 않는 내용도 함께 수정한다.",
            "register-honorific-001": "제안해 주신 문장이 더 자연스러워요.",
        }
        for case_id, output in variants.items():
            case = next(case for case in self.cases if case["id"] == case_id)
            self.assertNotIn("expected_exact", case)
            self.assertIn("완전 일치 기준: null", harness.render_reviewer_prompt(case, output))
            (self.work / "generator" / f"{case_id}.txt").write_text(
                output, encoding="utf-8", errors="strict"
            )
        _, records, _ = harness._collect(self.root, harness.VERSION, Path(".eval-work"))
        selected = [row for row in records if row["id"] in variants]
        self.assertTrue(all(row["case_pass"] for row in selected))
        self.assertEqual({row["id"]: row["output"] for row in selected}, variants)
        for case_id in variants:
            case = next(case for case in self.cases if case["id"] == case_id)
            failed = judgment(case)
            failed["rubric"]["meaning_preservation"] = "fail"
            for role in ("reviewer-a", "reviewer-b"):
                self.write_judgment(role, failed)
        records = harness.aggregate(self.root)
        self.assertTrue(all(not row["case_pass"] for row in records if row["id"] in variants))
        harness.verify_tracked(self.root)

    def test_required_regressions_preserve_source_and_matching_policy(self):
        for filename in ("core.json", "approved-copy.json"):
            path = self.root / "evals" / filename
            original = harness._read_json(path)
            for index, case in enumerate(original):
                if case["id"] in harness.REQUIRED_CASES:
                    for field, value in (("id", "replacement-case"), ("input", "changed source")):
                        with self.subTest(case_id=case["id"], field=field):
                            changed = copy.deepcopy(original)
                            changed[index][field] = value
                            write_json(path, changed)
                            with self.assertRaises(ValueError):
                                harness.load_cases(self.root)
                if case["category"] == "approved-copy" or case["id"] in harness.REQUIRED_CASES:
                    with self.subTest(case_id=case["id"], field="expected_exact"):
                        changed = copy.deepcopy(original)
                        if case["category"] == "approved-copy":
                            changed[index].pop("expected_exact")
                        else:
                            changed[index]["expected_exact"] = "unapproved exact answer"
                        write_json(path, changed)
                        with self.assertRaises(ValueError):
                            harness.load_cases(self.root)
                write_json(path, original)

    def test_case_schema_counts_duplicates_and_required_text(self):
        path = self.root / "evals" / "core.json"
        original = harness._read_json(path)
        variants = [
            original[:-1],
            [{**original[0], "extra": True}, *original[1:]],
            [original[0], {**original[1], "id": original[0]["id"]}, *original[2:]],
            [{**original[0], "expected_exact": "changed"}, *original[1:]],
            [{**original[0], "applicable_rubric": ["meaning_preservation"] * 2}, *original[1:]],
        ]
        for index, variant in enumerate(variants):
            with self.subTest(index=index):
                write_json(path, variant)
                with self.assertRaises(ValueError):
                    harness.load_cases(self.root)
        path.write_bytes(b"\xff")
        with self.assertRaises(ValueError):
            harness.load_cases(self.root)

    def test_context_file_count_category_ids_and_utf8_are_required(self):
        path = self.root / "evals" / "context.json"
        original_bytes = path.read_bytes()
        original = harness._read_json(path)
        self.assertEqual(len(original), 10)
        self.assertEqual({case["id"] for case in original}, set(harness.CONTEXT_CASE_IDS))
        path.unlink()
        with self.assertRaisesRegex(ValueError, "cannot read UTF-8 file"):
            harness.load_cases(self.root)
        variants = [
            original[:-1],
            [*original, original[0]],
            [{**original[0], "category": "artifact"}, *original[1:]],
            [original[0], {**original[1], "id": original[0]["id"]}, *original[2:]],
            [{**original[0], "id": self.cases[0]["id"]}, *original[1:]],
            [{**original[0], "id": "Invalid_ID"}, *original[1:]],
            [{key: value for key, value in original[0].items() if key != "instruction"}, *original[1:]],
        ]
        for index, variant in enumerate(variants):
            with self.subTest(variant=index):
                write_json(path, variant)
                with self.assertRaises(ValueError):
                    harness.load_cases(self.root)
        for index in range(len(original)):
            with self.subTest(required_id=original[index]["id"]):
                changed = copy.deepcopy(original)
                changed[index]["id"] = "replacement-context-001"
                write_json(path, changed)
                with self.assertRaisesRegex(ValueError, "required context regression"):
                    harness.load_cases(self.root)
        for data in (b"\xff", b"\xef\xbb\xbf" + original_bytes):
            with self.subTest(invalid_encoding=data[:3]):
                path.write_bytes(data)
                with self.assertRaisesRegex(ValueError, "UTF-8"):
                    harness.load_cases(self.root)

    def test_context_results_are_separate_from_core(self):
        case = next(case for case in self.cases if case["category"] == "context")
        failed = judgment(case)
        failed["rubric"]["audience_fit"] = "fail"
        for role in ("reviewer-a", "reviewer-b"):
            self.write_judgment(role, failed)
        records = harness.aggregate(self.root)
        summary = harness._read_text(self.root / "evals" / f"results-{harness.VERSION}.md")
        self.assertIn("| core | 24 | 24 | 0 |", summary)
        self.assertIn("| approved-copy | 2 | 2 | 0 |", summary)
        self.assertIn("| punctuation | 7 | 7 | 0 |", summary)
        self.assertIn("| context | 10 | 9 | 1 |", summary)
        self.assertIn("| pragmatics | 7 | 7 | 0 |", summary)
        self.assertIn("| 전체 | 50 | 49 | 1 |", summary)
        self.assertFalse(next(row for row in records if row["id"] == case["id"])["case_pass"])
        harness.check(self.root)
        harness.verify_tracked(self.root)

    def test_pragmatics_file_count_category_ids_and_utf8_are_required(self):
        path = self.root / "evals" / "pragmatics.json"
        original_bytes = path.read_bytes()
        original = harness._read_json(path)
        self.assertEqual(len(original), 7)
        self.assertEqual({case["id"] for case in original}, set(harness.PRAGMATICS_CASE_IDS))
        path.unlink()
        with self.assertRaisesRegex(ValueError, "cannot read UTF-8 file"):
            harness.load_cases(self.root)
        variants = [
            original[:-1],
            [*original, original[0]],
            [{**original[0], "category": "context"}, *original[1:]],
            [original[0], {**original[1], "id": original[0]["id"]}, *original[2:]],
            [{**original[0], "id": self.cases[0]["id"]}, *original[1:]],
            [{**original[0], "id": "Invalid_ID"}, *original[1:]],
            [{key: value for key, value in original[0].items() if key != "instruction"}, *original[1:]],
        ]
        for index, variant in enumerate(variants):
            with self.subTest(variant=index):
                write_json(path, variant)
                with self.assertRaises(ValueError):
                    harness.load_cases(self.root)
        for index in range(len(original)):
            with self.subTest(required_id=original[index]["id"]):
                changed = copy.deepcopy(original)
                changed[index]["id"] = "replacement-pragmatics-001"
                write_json(path, changed)
                with self.assertRaisesRegex(ValueError, "required pragmatics regression"):
                    harness.load_cases(self.root)
        for data in (b"\xff", b"\xef\xbb\xbf" + original_bytes):
            with self.subTest(invalid_encoding=data[:3]):
                path.write_bytes(data)
                with self.assertRaisesRegex(ValueError, "UTF-8"):
                    harness.load_cases(self.root)

    def test_pragmatics_results_are_separate_and_cannot_be_omitted(self):
        case = next(case for case in self.cases if case["category"] == "pragmatics")
        failed = judgment(case)
        failed["rubric"]["audience_fit"] = "fail"
        for role in ("reviewer-a", "reviewer-b"):
            self.write_judgment(role, failed)
        records = harness.aggregate(self.root)
        summary = harness._read_text(self.root / "evals" / f"results-{harness.VERSION}.md")
        self.assertIn("| core | 24 | 24 | 0 |", summary)
        self.assertIn("| context | 10 | 10 | 0 |", summary)
        self.assertIn("| pragmatics | 7 | 6 | 1 |", summary)
        self.assertIn("| 전체 | 50 | 49 | 1 |", summary)
        self.assertFalse(next(row for row in records if row["id"] == case["id"])["case_pass"])
        harness.check(self.root)
        harness.verify_tracked(self.root)
        self.mutate_tracked(lambda rows: rows.pop())
        with self.assertRaisesRegex(ValueError, "tracked case count mismatch"):
            harness.verify_tracked(self.root)

    def test_context_sources_and_helper_changes_invalidate_existing_results(self):
        harness.aggregate(self.root)
        before = harness.compute_digest(self.root)
        for relative in (
            "evals/context.json", "evals/pragmatics.json",
            "skills/natural-korean-writing/SKILL.md",
            "skills/natural-korean-writing/references/context-audience-boundary.md",
        ):
            with self.subTest(path=relative):
                path = self.root / relative
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                self.assertEqual(len(harness.load_cases(self.root)), 50)
                self.assertNotEqual(harness.compute_digest(self.root), before)
                with self.assertRaisesRegex(ValueError, "tested skill digest mismatch"):
                    harness.check(self.root)
                with self.assertRaisesRegex(ValueError, "tested skill digest mismatch"):
                    harness.verify_tracked(self.root)
                path.write_bytes(original)

    def test_digest_order_scope_and_raw_bytes(self):
        runtime = self.root / "skills" / "natural-korean-writing"
        for name, body in (("B.txt", b"B\r\n"), ("a.txt", b"a\x00\xff"), ("한글.txt", b"korean")):
            (runtime / name).write_bytes(body)
        paths = [
            self.root / "evals" / name
            for name in ("README.md", "core.json", "approved-copy.json", "punctuation.json", "context.json", "pragmatics.json")
        ] + [path for path in runtime.rglob("*") if path.is_file()]
        state = hashlib.sha256()
        for relative, path in sorted(
            ((path.relative_to(self.root).as_posix().encode("utf-8"), path) for path in paths),
            key=lambda item: item[0],
        ):
            body = path.read_bytes()
            state.update(relative + b"\0" + str(len(body)).encode("ascii") + b"\0" + body + b"\0")
        self.assertEqual(harness.compute_digest(self.root), state.hexdigest().upper())
        before = harness.compute_digest(self.root)
        write_json(self.root / "evals" / "runs" / "ignored.jsonl", {"synthetic": True})
        (self.root / "evals" / f"results-{harness.VERSION}.md").write_text(
            "ignored result", encoding="utf-8", errors="strict"
        )
        self.assertEqual(harness.compute_digest(self.root), before)


class SupplementalRegressionTests(unittest.TestCase):
    def test_supplemental_schema_and_baseline_isolation(self):
        root = Path(__file__).resolve().parents[1]
        baseline = harness.load_cases(root)
        self.assertEqual(len(baseline), 50)
        baseline_ids = {case["id"] for case in baseline}
        supplemental_ids = []
        for path in sorted((root / "evals/supplemental").glob("*.json")):
            cases = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsInstance(cases, list)
            self.assertNotIn(path.relative_to(root / "evals").as_posix(), harness.CASE_COUNTS)
            if path.name == "application-workflow.json":
                self.assertEqual(len(cases), 13)
            elif path.name == "application-tone-approval.json":
                self.assertEqual(len(cases), 3)
            elif path.name == "resume-information-selection.json":
                self.assertEqual(len(cases), 4)
            elif path.name == "resume-technology-outline.json":
                self.assertEqual(len(cases), 3)
            elif path.name == "scoped-korean-wording.json":
                self.assertEqual(len(cases), 2)
            elif path.name == "ai-contribution-closing.json":
                self.assertEqual(len(cases), 2)
            elif path.name == "name-quotation-scope.json":
                self.assertEqual(len(cases), 2)
            elif path.name == "contextual-writing-decisions.json":
                self.assertEqual(len(cases), 9)
            elif path.name == "execution-learning-authority.json":
                self.assertEqual(len(cases), 3)
            elif path.name == "required-coverage-limitations.json":
                self.assertEqual(len(cases), 2)
            elif path.name in {"korean-document-layout.json", "application-duty-evidence.json"}:
                self.assertEqual(len(cases), 2)
            elif path.name in {"resume-project-status.json", "application-contribution-tone.json"}:
                self.assertEqual(len(cases), 1)
            for case in cases:
                with self.subTest(file=path.name, case=case.get("id")):
                    self.assertEqual(set(case) - {"expected_exact"}, harness.CASE_FIELDS)
                    for field in ("id", "category", "context", "instruction", "input"):
                        self.assertIsInstance(case[field], str)
                        if field != "input":
                            self.assertTrue(case[field])
                    self.assertRegex(case["id"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
                    for field in ("must_preserve", "must_include", "must_not_add", "review_points",
                                  "critical_failures", "applicable_rubric"):
                        self.assertIsInstance(case[field], list)
                        self.assertTrue(all(isinstance(item, str) and item for item in case[field]))
                    if "expected_exact" in case:
                        self.assertIsInstance(case["expected_exact"], str)
                        self.assertTrue(case["expected_exact"])
                    applicable = case["applicable_rubric"]
                    self.assertTrue(applicable)
                    self.assertEqual(len(applicable), len(set(applicable)))
                    self.assertLessEqual(set(applicable), set(harness.RUBRIC))
                    supplemental_ids.append(case["id"])
        self.assertTrue((root / "evals/supplemental/application-workflow.json").is_file())
        self.assertTrue((root / "evals/supplemental/application-tone-approval.json").is_file())
        self.assertTrue((root / "evals/supplemental/resume-information-selection.json").is_file())
        self.assertTrue((root / "evals/supplemental/resume-technology-outline.json").is_file())
        self.assertTrue((root / "evals/supplemental/scoped-korean-wording.json").is_file())
        self.assertTrue((root / "evals/supplemental/ai-contribution-closing.json").is_file())
        self.assertTrue((root / "evals/supplemental/name-quotation-scope.json").is_file())
        self.assertTrue((root / "evals/supplemental/contextual-writing-decisions.json").is_file())
        self.assertTrue((root / "evals/supplemental/execution-learning-authority.json").is_file())
        self.assertTrue((root / "evals/supplemental/required-coverage-limitations.json").is_file())
        self.assertTrue((root / "evals/supplemental/korean-document-layout.json").is_file())
        self.assertTrue((root / "evals/supplemental/application-duty-evidence.json").is_file())
        self.assertTrue((root / "evals/supplemental/resume-project-status.json").is_file())
        self.assertTrue((root / "evals/supplemental/application-contribution-tone.json").is_file())
        self.assertEqual(len(supplemental_ids), len(set(supplemental_ids)))
        self.assertTrue(baseline_ids.isdisjoint(supplemental_ids))

    def test_application_action_does_not_replace_pr_summary(self):
        root = Path(__file__).resolve().parents[1]
        core = json.loads((root / "evals/core.json").read_text(encoding="utf-8"))
        original = next(case for case in core if case["id"] == "artifact-pr-summary-001")
        self.assertEqual(original["input"], "문서 내 오타에 대한 수정 작업을 수행했습니다.")
        self.assertIn("테스트는 실행하지 않았다", original["context"])
        extra = json.loads((root / "evals/supplemental/application-action.json").read_text(encoding="utf-8"))
        self.assertEqual(len(extra), 2)
        self.assertEqual(extra[1]["id"], "artifact-concrete-check-001")
        self.assertEqual(set(extra[1]), set(original))
        case = extra[0]
        self.assertEqual(case["id"], "artifact-application-action-001")
        self.assertEqual(set(case), set(original))
        self.assertNotIn(case["id"], {item["id"] for item in core})
        self.assertEqual(case["input"], "수정한 기능만 확인한 뒤 일이 끝났다고 판단하지 않습니다.")
        for key, value in case.items():
            self.assertIsInstance(value, type(original[key]))
            if isinstance(value, list):
                self.assertTrue(all(isinstance(item, str) and item for item in value))


class RevisionCasesTests(unittest.TestCase):
    def test_supplemental_cases_preserve_baseline_and_schema(self):
        baseline = []
        for name, count in (("core", 24), ("approved-copy", 2), ("punctuation", 7), ("context", 10), ("pragmatics", 7)):
            items = json.loads((Path(__file__).resolve().parents[1] / "evals" / f"{name}.json").read_text(encoding="utf-8"))
            self.assertEqual(len(items), count)
            baseline.extend(items)
        extra = json.loads((Path(__file__).resolve().parents[1] / "evals/supplemental/revision-review.json").read_text(encoding="utf-8"))
        self.assertEqual(len(extra), 5)
        ids = [item["id"] for item in baseline + extra]
        self.assertEqual(len(ids), len(set(ids)))
        schema = baseline[0]
        for item in extra:
            self.assertEqual(set(item), set(schema))
            for key, value in item.items():
                self.assertIsInstance(value, type(schema[key]))
                if isinstance(value, list):
                    self.assertTrue(all(isinstance(part, str) and part for part in value))
            self.assertTrue(item["must_preserve"])
            self.assertTrue(item["critical_failures"])


if __name__ == "__main__":
    unittest.main()
