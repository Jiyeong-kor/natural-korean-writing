"""Check byte accounting and section boundaries, not model routing behavior."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import measure_read_paths as paths
import run_evals as harness


class ReadPathTests(unittest.TestCase):
    def setUp(self):
        self.intro = "# Profiles\n\n공통 서문입니다.\n\n".encode("utf-8")
        self.sections = {
            heading: ("## " + heading + "\n\n본문입니다.\n\n### Child\n\n"
                      "하위 절을 끝까지 읽습니다.\n\n").encode("utf-8")
            for heading in paths.ROUTES.values()
        }
        self.profiles = self.intro + b"".join(self.sections.values())
        self.files = {paths.SKILL + name: (name + "\n원문\n").encode("utf-8")
                      for name in (*paths.CORE, paths.WORKFLOW)}
        self.files[paths.SKILL + paths.PROFILES] = self.profiles

    def test_selected_profile_keeps_intro_and_all_children(self):
        for heading, section in self.sections.items():
            with self.subTest(heading=heading):
                self.assertEqual(paths.selected_profile(self.profiles, heading),
                                 self.intro + section)

    def test_sections_reconstruct_original_without_normalization(self):
        for original in (self.profiles, self.profiles.replace(b"\n", b"\r\n")):
            intro, sections = paths.profile_parts(original)
            self.assertEqual(intro + b"".join(sections.values()), original)

    def test_fenced_headings_remain_inside_the_selected_section(self):
        for fence in (b"```", b"~~~~"):
            section = (self.sections[paths.ROUTES["email"]] + fence + b"markdown\n"
                       b"## Not a profile\n" + fence + b"\n\n")
            data = self.intro + section + self.sections[paths.ROUTES["ui"]]
            self.assertEqual(paths.selected_profile(data, paths.ROUTES["email"]),
                             self.intro + section)

    def test_missing_or_duplicate_headings_fail(self):
        with self.assertRaisesRegex(ValueError, "Missing profile"):
            paths.selected_profile(self.profiles, "Absent")
        with self.assertRaisesRegex(ValueError, "Duplicate profile"):
            paths.profile_parts(self.profiles + self.sections[paths.ROUTES["email"]])
        with self.assertRaisesRegex(ValueError, "No profile"):
            paths.profile_parts(self.intro)

    def test_utf8_and_bom_failures_are_not_hidden(self):
        with self.assertRaises(UnicodeDecodeError):
            paths.profile_parts(b"\xff\xfe")
        with self.assertRaisesRegex(ValueError, "BOM"):
            paths.profile_parts(b"\xef\xbb\xbf" + self.profiles)

    def test_core_and_application_workflow_are_whole_files(self):
        measured = paths.measure(self.files.__getitem__)
        core = sum(len(self.files[paths.SKILL + name]) for name in paths.CORE)
        self.assertEqual(measured["core"], core)
        self.assertEqual(measured["application"], core + len(self.intro)
                         + len(self.sections[paths.ROUTES["application"]])
                         + len(self.files[paths.SKILL + paths.WORKFLOW]))

    def test_unrelated_profile_does_not_inflate_email_or_ui(self):
        before = paths.measure(self.files.__getitem__)
        self.files[paths.SKILL + paths.PROFILES] += b"## Unrelated\n\n" + b"x" * 10000
        after = paths.measure(self.files.__getitem__)
        self.assertEqual(before["email"], after["email"])
        self.assertEqual(before["ui"], after["ui"])
        whole = paths.measure(self.files.__getitem__, whole_profiles=True)
        self.assertGreater(whole["email"], after["email"])
        self.assertGreater(whole["ui"], after["ui"])

    def test_current_paths_exist_and_profile_sections_are_distinct(self):
        read = lambda path: (ROOT / path).read_bytes()
        values = paths.measure(read)
        data = read(paths.SKILL + paths.PROFILES)
        intro, sections = paths.profile_parts(data)
        self.assertEqual(intro + b"".join(sections.values()), data)
        for route, heading in paths.ROUTES.items():
            with self.subTest(route=route):
                self.assertIn(heading, sections)
                selected = paths.selected_profile(data, heading)
                if route == "application":
                    self.assertIn(b"### Application essays", selected)
                for other in paths.ROUTES.values():
                    if other != heading:
                        self.assertNotIn(("## " + other + "\n").encode("utf-8"), selected)
                self.assertGreater(values[route], values["core"])
        entrypoint = read(paths.SKILL + "SKILL.md")
        for reference in (*paths.CORE[1:], paths.PROFILES, paths.WORKFLOW):
            self.assertIn(reference.encode("utf-8"), entrypoint)

    def test_short_artifact_cases_keep_supplemental_schema(self):
        fixture = ROOT / "evals/supplemental/artifact-profile-routing.json"
        cases = json.loads(fixture.read_text(encoding="utf-8", errors="strict"))
        self.assertEqual([case["id"] for case in cases], [
            "artifact-profile-short-email-001", "artifact-profile-ui-dismiss-001",
        ])
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(set(case), harness.CASE_FIELDS)
                self.assertEqual(case["category"], "context")
                for field in ("id", "category", "context", "instruction", "input"):
                    self.assertIsInstance(case[field], str)
                    self.assertTrue(case[field])
                for field in ("must_preserve", "must_include", "must_not_add",
                              "review_points", "critical_failures", "applicable_rubric"):
                    self.assertIsInstance(case[field], list)
                    self.assertTrue(all(isinstance(item, str) and item for item in case[field]))
                self.assertTrue(case["critical_failures"])
                self.assertEqual(len(case["applicable_rubric"]), len(set(case["applicable_rubric"])))
                self.assertLessEqual(set(case["applicable_rubric"]), set(harness.RUBRIC))


if __name__ == "__main__":
    unittest.main()
