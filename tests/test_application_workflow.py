"""분리한 지원서 지침의 원본 보존과 참조 연결을 검사합니다."""

import hashlib
from pathlib import Path
import re
import subprocess
import sys
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import measure_read_paths as paths
import validate_repo as validator


STAGE_HEADINGS = {
    "planning": (
        "Select experiences against the complete prompt",
        "Verify duty evidence in the actual answer",
        "Ground application recommendations in role evidence",
    ),
    "writing": (
        "Review selection reasons, not only correctness",
        "Make the actor, object, and reason readable",
        "Explain service operation through tone revisions",
    ),
    "review": (
        "Read the whole company's answer set",
        "Review and freeze the actual version",
    ),
    "form": ("Coordinate writing and authorized form work",),
    "delivery": ("Deliver requested originals and report download state",),
}

# 원본의 위치 표현 3개와 명시적으로 바꾼 역할 계약 2개를 대조합니다.
# 원본 본문이나 승인된 변경을 모델 출력에 맞춰 느슨하게 비교하지 않습니다.
APPROVED_REPLACEMENTS = {
    "writing": (
        (
            "deadline reserve and version-freeze rules below",
            "[deadline reserve and version-freeze rules]"
            "(application-review.md#review-and-freeze-the-actual-version)",
        ),
        (
            "duty-evidence passage check above",
            "[duty-evidence passage check]"
            "(application-planning.md#verify-duty-evidence-in-the-actual-answer)",
        ),
        (
            "The delivering assistant owns the final decision: reviewer PASS labels are inputs, "
            "not completion evidence. Independently read the exact assembled final answers "
            "against the questions, source facts, and latest constraints after integrating changes.",
            "The designated reviewer must read the exact assembled final answers against the "
            "questions, source facts, and latest constraints after changes are integrated. The "
            "coordinator verifies the final version or fingerprint against the substantive returned "
            "findings, confirms the disposition of material issues, and checks that every required "
            "review role and completion condition is satisfied; reviewer PASS labels alone are "
            "not completion evidence. If the coordinator makes substantive changes or judges the "
            "content itself, it must read the complete references required for that writing or "
            "review role before doing so. Any changed version must repeat the relevant checks "
            "and required independent review.",
        ),
    ),
    "review": (
        (
            "duty-evidence record above",
            "[duty-evidence record]"
            "(application-planning.md#verify-duty-evidence-in-the-actual-answer)",
        ),
        (
            "Inspect the assembled answers, including unchanged passages.",
            "The designated reviewer inspects the assembled answers, including unchanged passages, "
            "against the exact questions, source facts, and latest constraints. Before delivery, "
            "the coordinator verifies the exact final version or fingerprint, substantive returned "
            "findings, disposition of material issues, and completion conditions. If the coordinator "
            "makes substantive changes or judges the content itself, it must first read the full "
            "references required for that role.",
        ),
    ),
}

# 이번 문단 검수 보완의 삽입 2개만 정확한 위치와 바이트 해시로 확인합니다.
# 이를 제거한 나머지는 기존 치환을 제외하면 고정 원본과 같아야 합니다.
APPROVED_INSERTIONS = {
    "writing": (
        b"These are semantic roles, not mandatory headings or a conclusion-last order.\n\n",
        b"For each paragraph, state privately",
        "04250b45d7b9d6ccadcdbc0819f1bc355f133e47265699efaeed259979907c12",
    ),
    "review": (
        b"This application review is separate from the repository's benchmark protocol, "
        b"whose reviewers receive only their prescribed evaluation inputs.\n\n",
        b"Keep factual support, paragraph relevance,",
        "6c347c80efdee49cd90269531f6877e8e1173e6e7db1a3f3d145f1f95256ad0c",
    ),
}


class ApplicationWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = subprocess.check_output(
            ["git", "show", paths.BEFORE_AGENT_WORKFLOW + ":" + paths.SKILL + paths.WORKFLOW],
            cwd=ROOT, timeout=30,
        )
        cls.original_intro, cls.original_sections = paths.profile_parts(cls.original)

    def test_stage_bodies_restore_the_pinned_source_after_only_approved_changes(self):
        self.assertEqual(tuple(STAGE_HEADINGS), tuple(paths.APPLICATION_STAGES))
        original_order = tuple(heading for headings in STAGE_HEADINGS.values() for heading in headings)
        self.assertEqual(original_order, tuple(self.original_sections))
        restored = [self.original_intro]
        for stage, headings in STAGE_HEADINGS.items():
            relative = paths.APPLICATION_STAGES[stage]
            with self.subTest(path=relative):
                data = (ROOT / paths.SKILL / relative).read_bytes()
                _, sections = paths.profile_parts(data)
                self.assertEqual(tuple(sections), headings)
                actual = b"".join(sections.values())
                if stage in APPROVED_INSERTIONS:
                    anchor, prefix, digest = APPROVED_INSERTIONS[stage]
                    self.assertEqual(actual.count(anchor), 1)
                    start = actual.index(anchor) + len(anchor)
                    end = actual.index(b"\n\n", start) + 2
                    inserted = actual[start:end]
                    self.assertTrue(inserted.startswith(prefix))
                    self.assertEqual(hashlib.sha256(inserted).hexdigest(), digest)
                    actual = actual[:start] + actual[end:]
                original = b"".join(self.original_sections[heading] for heading in headings)
                expected = original
                for old, new in APPROVED_REPLACEMENTS.get(stage, ()):
                    old_bytes, new_bytes = old.encode("utf-8"), new.encode("utf-8")
                    self.assertEqual(original.count(old_bytes), 1)
                    self.assertEqual(actual.count(new_bytes), 1)
                    expected = expected.replace(old_bytes, new_bytes)
                self.assertEqual(actual, expected)
                for old, new in reversed(APPROVED_REPLACEMENTS.get(stage, ())):
                    actual = actual.replace(new.encode("utf-8"), old.encode("utf-8"))
                restored.append(actual)
        self.assertEqual(b"".join(restored), self.original)

    def test_stage_introductions_keep_context_privacy_and_fictional_example_limits(self):
        shared = b"Keep working records " + self.original_intro.split(
            b"Keep working records ", 1)[1].strip()
        for stage, relative in paths.APPLICATION_STAGES.items():
            with self.subTest(path=relative):
                intro, _ = paths.profile_parts((ROOT / paths.SKILL / relative).read_bytes())
                self.assertIn(shared, intro)
                self.assertIn(b"entrypoint's required context and punctuation guidance", intro)
                if stage in {"form", "delivery"}:
                    self.assertIn(
                        b"If this stage also drafts or substantively reviews an answer, read the full "
                        b"application prose profile and all three drafting stages selected by the index.",
                        intro,
                    )
                else:
                    self.assertIn(b"and the application prose profile.", intro)
                self.assertIn("application-answer-workflow.md", validator.relative_targets(
                    intro.decode("utf-8", errors="strict")))

    def test_old_headings_remain_in_the_index_and_link_to_their_full_stage(self):
        index = (ROOT / paths.SKILL / paths.WORKFLOW).read_text(encoding="utf-8", errors="strict")
        old_headings = re.findall(r"^#{2,3} .+$", self.original.decode("utf-8"), re.MULTILINE)
        for heading in old_headings:
            with self.subTest(heading=heading):
                self.assertEqual(index.splitlines().count(heading), 1)
        linked = set(validator.relative_targets(index))
        self.assertTrue({Path(path).name for path in paths.APPLICATION_STAGES.values()} <= linked)

        markdown = validator.prose_markdown(index)
        targets = re.findall(r"\[[^\]\n]*\]\(([^\s)]+)\)", markdown)
        stage_paths = {Path(path).name for path in paths.APPLICATION_STAGES.values()}
        for target in targets:
            parsed = urlsplit(target)
            if parsed.path in stage_paths and parsed.fragment:
                with self.subTest(target=target):
                    body = (ROOT / paths.SKILL / "references" / parsed.path).read_text(
                        encoding="utf-8", errors="strict")
                    headings = re.findall(r"^#{1,6} (.+)$", body, re.MULTILINE)
                    anchors = {
                        re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
                        for heading in headings
                    }
                    self.assertIn(unquote(parsed.fragment), anchors)

    def test_every_role_and_stage_file_is_registered_for_current_validation(self):
        expected = {paths.AGENT_WORKFLOW, paths.WORKFLOW, *paths.APPLICATION_STAGES.values()}
        self.assertEqual({paths.SKILL + path for path in expected}, set(validator.WORKFLOW_REFERENCES))
        self.assertTrue(set(validator.WORKFLOW_REFERENCES).isdisjoint(
            validator.ORIGINAL_RELEASE_MANIFEST))


if __name__ == "__main__":
    unittest.main()
