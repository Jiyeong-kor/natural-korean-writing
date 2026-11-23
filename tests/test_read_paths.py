"""Check byte accounting and section boundaries, not model routing behavior."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPLIT_COMMIT = "405475fbe3a298bc6aaf8d34ef4649cb3946e85a"
sys.path.insert(0, str(ROOT / "scripts"))
import measure_read_paths as paths
import run_evals as harness


class ReadPathTests(unittest.TestCase):
    def setUp(self):
        self.intro = "# Profiles\n\n공통 서문입니다.\n\n".encode("utf-8")
        self.sections = {
            heading: ("## " + heading + "\n\n본문입니다.\n\n### Child\n\n"
                      "하위 절을 끝까지 읽습니다.\n\n").encode("utf-8")
            for heading in paths.SPLIT_FILES
        }
        self.profiles = self.intro + b"".join(self.sections.values())
        self.files = {paths.SKILL + name: (name + "\n원문\n").encode("utf-8")
                      for name in (*paths.CORE, paths.WORKFLOW)}
        self.files[paths.SKILL + paths.PROFILES] = self.profiles
        self.split_files = dict(self.files)
        self.split_files[paths.SKILL + paths.PROFILES] = self.intro + (
            "선택 안내 전체도 읽기 분량에 포함합니다.\n\n"
            + "".join(f"## {heading}\n\n[{heading}]({Path(path).name})\n\n"
                      for heading, path in paths.SPLIT_FILES.items())
        ).encode("utf-8")
        for heading, path in paths.SPLIT_FILES.items():
            self.split_files[paths.SKILL + path] = self.sections[heading]
        for path in (paths.AGENT_WORKFLOW, paths.EDITING, paths.LANGUAGE,
                     *paths.APPLICATION_STAGES.values()):
            self.split_files[paths.SKILL + path] = (path + "\n전체 지침입니다.\n").encode("utf-8")

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
        values = paths.measure(read, split_profiles=True)
        data = read(paths.SKILL + paths.PROFILES)
        intro, sections = paths.profile_parts(data)
        self.assertEqual(intro + b"".join(sections.values()), data)
        for route, heading in paths.ROUTES.items():
            with self.subTest(route=route):
                self.assertIn(heading, sections)
                selected = read(paths.SKILL + paths.SPLIT_FILES[heading])
                if route == "application":
                    self.assertIn(b"### Application essays", selected)
                for other in paths.ROUTES.values():
                    if other != heading:
                        self.assertNotIn(("## " + other + "\n").encode("utf-8"), selected)
                self.assertGreater(values[route], values["core"])
        entrypoint = read(paths.SKILL + "SKILL.md")
        for reference in (*paths.CORE[1:], paths.PROFILES, paths.WORKFLOW):
            self.assertIn(reference.encode("utf-8"), entrypoint)
        for reference in paths.SPLIT_FILES.values():
            self.assertIn(Path(reference).name.encode("utf-8"), data)

    def test_split_paths_count_the_entire_index_and_selected_files(self):
        measured = paths.measure(self.split_files.__getitem__, split_profiles=True)
        core = sum(len(self.split_files[paths.SKILL + name]) for name in paths.CORE)
        for route, heading in paths.ROUTES.items():
            with self.subTest(route=route):
                expected = (core + len(self.split_files[paths.SKILL + paths.PROFILES])
                            + len(self.split_files[paths.SKILL + paths.SPLIT_FILES[heading]]))
                if route == "application":
                    expected += len(self.split_files[paths.SKILL + paths.WORKFLOW])
                self.assertEqual(measured[route], expected)
        self.assertEqual(measured, paths.measure(self.split_files.__getitem__,
                                                whole_profiles=True, split_profiles=True))

    def test_split_routes_do_not_read_unrelated_profile_or_document_files(self):
        seen = []

        def read(path):
            seen.append(path)
            return self.split_files[path]

        paths.measure_path(read, ("email",), split_profiles=True)
        expected = {paths.SKILL + name for name in (
            *paths.CORE, paths.PROFILES, paths.SPLIT_FILES[paths.ROUTES["email"]],
        )}
        self.assertEqual(set(seen), expected)
        self.assertEqual(len(seen), len(expected))

    def test_missing_or_empty_split_file_never_falls_back_to_the_collection(self):
        relative = paths.SKILL + paths.SPLIT_FILES[paths.ROUTES["email"]]
        self.split_files[paths.SKILL + paths.PROFILES] = self.profiles
        del self.split_files[relative]
        with self.assertRaises(KeyError):
            paths.measure_path(self.split_files.__getitem__, ("email",), split_profiles=True)
        for content in (b"", b" \n"):
            self.split_files[relative] = content
            with self.subTest(content=content), self.assertRaisesRegex(ValueError, "Empty reading"):
                paths.measure_path(self.split_files.__getitem__, ("email",), split_profiles=True)

    def test_mixed_document_and_layout_paths_count_each_shared_file_once(self):
        seen = []

        def read(path):
            seen.append(path)
            return self.split_files[path]

        value = paths.measure_path(read, ("email", "application", "email", "application"),
                                   document=True, layout=True, split_profiles=True)
        expected = {paths.SKILL + name for name in (
            *paths.CORE, paths.PROFILES, paths.WORKFLOW,
            paths.SPLIT_FILES[paths.ROUTES["email"]],
            paths.SPLIT_FILES[paths.ROUTES["application"]],
            paths.SPLIT_FILES[paths.DOCUMENT], paths.SPLIT_FILES[paths.LAYOUT],
        )}
        self.assertEqual(set(seen), expected)
        self.assertEqual(len(seen), len(expected))
        self.assertEqual(value, sum(len(self.split_files[path]) for path in expected))

    def test_document_evidence_and_layout_conditions_are_independent(self):
        read = self.split_files.__getitem__
        core_index = sum(len(read(paths.SKILL + name)) for name in (*paths.CORE, paths.PROFILES))
        document = len(read(paths.SKILL + paths.SPLIT_FILES[paths.DOCUMENT]))
        layout = len(read(paths.SKILL + paths.SPLIT_FILES[paths.LAYOUT]))
        self.assertEqual(paths.measure_path(read, (), document=True, split_profiles=True),
                         core_index + document)
        self.assertEqual(paths.measure_path(read, (), layout=True, split_profiles=True),
                         core_index + layout)
        self.assertEqual(paths.measure_path(read, (), document=True, layout=True,
                                            split_profiles=True), core_index + document + layout)

    def test_legacy_mixed_units_preserve_intro_children_and_unique_workflow(self):
        read = self.files.__getitem__
        value = paths.measure_path(read, ("application", "email", "application"),
                                   document=True, layout=True)
        headings = (paths.ROUTES["application"], paths.ROUTES["email"],
                    paths.DOCUMENT, paths.LAYOUT)
        expected = (sum(len(read(paths.SKILL + name)) for name in (*paths.CORE, paths.WORKFLOW))
                    + len(self.intro) + sum(len(self.sections[heading]) for heading in headings))
        self.assertEqual(value, expected)
        self.assertEqual(paths.measure_path(read, ("application", "email", "application"),
                                            document=True, layout=True, whole_profiles=True),
                         sum(len(read(paths.SKILL + name))
                             for name in (*paths.CORE, paths.WORKFLOW, paths.PROFILES)))

    def test_unknown_routes_do_not_silently_skip_required_context(self):
        with self.assertRaisesRegex(ValueError, "Unknown artifact route"):
            paths.measure_path(self.split_files.__getitem__, ("absent",), split_profiles=True)

    def test_split_application_drafting_counts_planning_writing_and_review(self):
        read = self.split_files.__getitem__
        previous = paths.measure_path(read, ("application",), split_profiles=True)
        expected = previous + sum(len(read(paths.SKILL + paths.APPLICATION_STAGES[stage]))
                                  for stage in ("planning", "writing", "review"))
        self.assertEqual(paths.measure_path(read, ("application",), split_profiles=True,
                                            split_application=True), expected)
        self.assertEqual(paths.measure(read, split_profiles=True,
                                       split_application=True)["application"], expected)

    def test_plain_application_conditions_add_only_split_stage_files(self):
        read = self.split_files.__getitem__
        base = paths.measure_path(read, ("application",), split_profiles=True,
                                  split_application=True)
        for conditions, stages in (({"form": True}, ("form",)),
                                   ({"delivery": True}, ("delivery",)),
                                   ({"form": True, "delivery": True}, ("form", "delivery"))):
            with self.subTest(conditions=conditions):
                expected = base + sum(len(read(paths.SKILL + paths.APPLICATION_STAGES[stage]))
                                      for stage in stages)
                self.assertEqual(paths.measure_path(read, ("application",), split_profiles=True,
                                                    split_application=True, **conditions), expected)
                legacy = paths.measure_path(self.files.__getitem__, ("application",))
                self.assertEqual(paths.measure_path(self.files.__getitem__, ("application",),
                                                    **conditions), legacy)
                with self.assertRaisesRegex(ValueError, "application route"):
                    paths.measure_path(read, ("email",), split_profiles=True, **conditions)

    def test_application_template_scenario_includes_document_layout_and_form_work(self):
        files = {
            *paths.CORE, paths.PROFILES, paths.WORKFLOW,
            paths.SPLIT_FILES[paths.ROUTES["application"]],
            paths.SPLIT_FILES[paths.DOCUMENT], paths.SPLIT_FILES[paths.LAYOUT],
            *(paths.APPLICATION_STAGES[stage] for stage in ("planning", "writing", "review", "form")),
        }
        actual = paths.measure_scenarios(self.split_files.__getitem__, split_profiles=True,
                                        split_application=True)["application_template"]
        self.assertEqual(actual, sum(len(self.split_files[paths.SKILL + path]) for path in files))

    def test_application_coordinator_reads_core_contract_and_index_only(self):
        seen = []

        def read(path):
            seen.append(path)
            return self.split_files[path]

        value = paths.measure_agent_path(read, "coordinator", ("application",))
        expected = {paths.SKILL + path for path in (*paths.CORE, paths.AGENT_WORKFLOW,
                                                    paths.WORKFLOW)}
        self.assertEqual(set(seen), expected)
        self.assertEqual(len(seen), len(expected))
        self.assertEqual(value, sum(len(self.split_files[path]) for path in expected))
        for path in (paths.PROFILES, *paths.SPLIT_FILES.values(),
                     *paths.APPLICATION_STAGES.values(), paths.EDITING, paths.LANGUAGE):
            del self.split_files[paths.SKILL + path]
        self.assertEqual(paths.measure_agent_path(read, "coordinator", ("application",)), value)

    def test_application_writer_and_reviewer_keep_all_three_drafting_stages(self):
        common = {
            *paths.CORE, paths.AGENT_WORKFLOW, paths.PROFILES, paths.WORKFLOW,
            paths.SPLIT_FILES[paths.ROUTES["application"]],
            *(paths.APPLICATION_STAGES[stage] for stage in ("planning", "writing", "review")),
        }
        for role in ("writer", "reviewer"):
            with self.subTest(role=role):
                seen = []

                def read(path):
                    seen.append(path)
                    return self.split_files[path]

                value = paths.measure_agent_path(read, role, ("application", "application"))
                expected = common | ({paths.EDITING} if role == "reviewer" else set())
                self.assertEqual(set(seen), {paths.SKILL + path for path in expected})
                self.assertEqual(len(seen), len(expected))
                self.assertEqual(value, sum(len(self.split_files[paths.SKILL + path])
                                            for path in expected))

    def test_form_and_delivery_are_independent_explicit_conditions_for_each_role(self):
        read = self.split_files.__getitem__
        form = len(read(paths.SKILL + paths.APPLICATION_STAGES["form"]))
        delivery = len(read(paths.SKILL + paths.APPLICATION_STAGES["delivery"]))
        for role in ("coordinator", "writer", "reviewer"):
            with self.subTest(role=role):
                base = paths.measure_agent_path(read, role, ("application",))
                for conditions, expected in (
                    ({"form": True}, base + form),
                    ({"delivery": True}, base + delivery),
                    ({"form": True, "delivery": True}, base + form + delivery),
                ):
                    self.assertEqual(paths.measure_agent_path(read, role, ("application",),
                                                               **conditions), expected)
        base = paths.measure_agent_path(read, "writer", ("application",))
        del self.split_files[paths.SKILL + paths.APPLICATION_STAGES["form"]]
        del self.split_files[paths.SKILL + paths.APPLICATION_STAGES["delivery"]]
        self.assertEqual(paths.measure_agent_path(read, "writer", ("application",)), base)
        for conditions in ({"form": True}, {"delivery": True}):
            with self.assertRaises(KeyError):
                paths.measure_agent_path(read, "writer", ("application",), **conditions)

    def test_revision_language_and_document_checks_are_added_only_when_requested(self):
        read = self.split_files.__getitem__
        writer = paths.measure_agent_path(read, "writer", ("application",))
        editing = len(read(paths.SKILL + paths.EDITING))
        language = len(read(paths.SKILL + paths.LANGUAGE))
        self.assertEqual(paths.measure_agent_path(read, "writer", ("application",), revision=True),
                         writer + editing)
        self.assertEqual(paths.measure_agent_path(read, "reviewer", ("application",), revision=True),
                         writer + editing)
        self.assertEqual(paths.measure_agent_path(read, "reviewer", ("application",), language=True),
                         writer + editing + language)
        document = len(read(paths.SKILL + paths.SPLIT_FILES[paths.DOCUMENT]))
        layout = len(read(paths.SKILL + paths.SPLIT_FILES[paths.LAYOUT]))
        self.assertEqual(paths.measure_agent_path(read, "writer", ("application",),
                                                  document=True, layout=True),
                         writer + document + layout)

    def test_short_artifact_and_ordinary_paths_exclude_application_and_agent_overhead(self):
        expected = {*paths.CORE, paths.AGENT_WORKFLOW, paths.PROFILES,
                    paths.SPLIT_FILES[paths.ROUTES["email"]]}
        self.assertEqual(set(paths.agent_reading_files("writer", ("email",))), expected)
        self.assertEqual(set(paths.agent_reading_files("coordinator", ("email",))),
                         {*paths.CORE, paths.AGENT_WORKFLOW})
        seen = []

        def read(path):
            seen.append(path)
            return self.split_files[path]

        paths.measure_path(read, ("email",), split_profiles=True, split_application=True)
        self.assertEqual(set(seen), {paths.SKILL + path for path in expected - {paths.AGENT_WORKFLOW}})

    def test_agent_paths_reject_unknown_roles_routes_and_inconsistent_work(self):
        with self.assertRaisesRegex(ValueError, "Unknown agent role"):
            paths.agent_reading_files("unknown", ("application",))
        with self.assertRaisesRegex(ValueError, "Unknown artifact route"):
            paths.agent_reading_files("coordinator", ("unknown",))
        for condition in ("form", "delivery"):
            with self.subTest(condition=condition), self.assertRaisesRegex(ValueError, "application route"):
                paths.agent_reading_files("writer", ("email",), **{condition: True})
        for condition in ("revision", "language", "document", "layout"):
            with self.subTest(condition=condition), self.assertRaisesRegex(ValueError, "writer or reviewer"):
                paths.agent_reading_files("coordinator", ("application",), **{condition: True})

    def test_agent_paths_reject_missing_empty_and_invalid_selected_files(self):
        for path in (paths.AGENT_WORKFLOW, paths.WORKFLOW, paths.EDITING, paths.LANGUAGE,
                     *paths.APPLICATION_STAGES.values()):
            relative = paths.SKILL + path
            original = self.split_files[relative]
            del self.split_files[relative]
            with self.subTest(path=path, content="missing"), self.assertRaises(KeyError):
                paths.measure_agent_path(self.split_files.__getitem__, "reviewer", ("application",),
                                         language=True, form=True, delivery=True)
            for content, error in ((b"", ValueError), (b" \n", ValueError),
                                   (b"\xff", UnicodeDecodeError), (b"\xef\xbb\xbftext", ValueError)):
                self.split_files[relative] = content
                with self.subTest(path=path, content=content), self.assertRaises(error):
                    paths.measure_agent_path(self.split_files.__getitem__, "reviewer", ("application",),
                                             language=True, form=True, delivery=True)
            self.split_files[relative] = original

    def read_split_commit_file(self, ref, path):
        return subprocess.check_output(
            ["git", "show", ref + ":" + paths.SKILL + path],
            cwd=ROOT, timeout=30)

    def test_split_bodies_reconstruct_the_pinned_before_split_collection(self):
        original = self.read_split_commit_file(paths.BEFORE_SPLIT, paths.PROFILES)
        intro, sections = paths.profile_parts(original)
        self.assertEqual(list(paths.SPLIT_FILES), list(sections))
        index = self.read_split_commit_file(SPLIT_COMMIT, paths.PROFILES)
        self.assertTrue(index.startswith(intro))
        restored = [intro]
        for heading, path in paths.SPLIT_FILES.items():
            with self.subTest(path=path):
                body = self.read_split_commit_file(SPLIT_COMMIT, path)
                self.assertEqual(body, sections[heading])
                restored.append(body)
        self.assertEqual(b"".join(restored), original)

    def assert_current_split_content_preserved(self, read, original_intro, original_bodies):
        # Keep the historical reconstruction separate. Permit an intentional live
        # profile change only in its own branch below, rather than disabling the
        # preservation check for all profiles.
        index_path = paths.SKILL + paths.PROFILES
        self.assertTrue(read(index_path).startswith(original_intro),
                        "Current profile index lost its original introduction")
        ui_path = paths.SPLIT_FILES[paths.ROUTES["ui"]]
        for path, original in original_bodies.items():
            current = read(paths.SKILL + path)
            if path == ui_path:
                self.assertTrue(current.startswith(original),
                                f"Current profile lost or changed its original body: {path}")
                extension = current[len(original):].decode("utf-8", errors="strict")
                section, separator, body = extension.strip().partition("\n")
                self.assertEqual(section, "### Check code-backed copy in context")
                self.assertTrue(separator and body.strip(),
                                "Current UI profile lost the code-backed copy guidance")
            else:
                self.assertEqual(current, original,
                                 f"Current profile differs from its preserved body: {path}")

    def read_live_preservation_reference(self):
        original = self.read_split_commit_file(paths.BEFORE_SPLIT, paths.PROFILES)
        intro, sections = paths.profile_parts(original)
        return intro, {path: sections[heading] for heading, path in paths.SPLIT_FILES.items()}

    def test_current_split_files_preserve_original_bodies_and_introduction(self):
        intro, bodies = self.read_live_preservation_reference()
        self.assert_current_split_content_preserved(
            lambda path: (ROOT / path).read_bytes(), intro, bodies)

    def test_current_preservation_detects_truncated_profiles_and_index(self):
        intro, bodies = self.read_live_preservation_reference()
        read = lambda path: (ROOT / path).read_bytes()
        ui = paths.SKILL + paths.SPLIT_FILES[paths.ROUTES["ui"]]
        technical = next(paths.SKILL + path for heading, path in paths.SPLIT_FILES.items()
                         if heading.startswith("2. "))
        index = paths.SKILL + paths.PROFILES
        for target, mutated, failure in (
            (ui, read(ui).splitlines(keepends=True)[0], "original body"),
            (technical, read(technical).splitlines(keepends=True)[0], "preserved body"),
            (index, read(index)[read(index).index(b"## "):], "original introduction"),
            (ui, read(ui).split(b"\n### Check code-backed", 1)[0] + b"\n",
             "Check code-backed copy"),
        ):
            with self.subTest(target=target, failure=failure):
                with self.assertRaisesRegex(AssertionError, failure):
                    self.assert_current_split_content_preserved(
                        lambda path: mutated if path == target else read(path), intro, bodies)

    def test_routed_cases_keep_supplemental_schema(self):
        fixtures = {
            "artifact-profile-routing.json": [
                "artifact-profile-short-email-001", "artifact-profile-ui-dismiss-001",
            ],
            "artifact-ui-runtime-context.json": [
                "artifact-ui-shared-formatted-value-001",
                "artifact-ui-raw-value-retry-001",
                "artifact-ui-mixed-contract-001",
                "artifact-ui-retry-current-state-001",
            ],
            "prose-reasoning-preservation.json": [
                "prose-reasoning-native-draft-001",
                "prose-reasoning-native-revision-001",
                "prose-reasoning-translation-scope-001",
                "prose-reasoning-two-stage-decision-001",
            ],
        }
        cases = []
        for filename, expected_ids in fixtures.items():
            with self.subTest(fixture=filename):
                fixture = ROOT / "evals" / "supplemental" / filename
                items = json.loads(fixture.read_text(encoding="utf-8", errors="strict"))
                self.assertEqual([case["id"] for case in items], expected_ids)
                self.assertNotIn(f"supplemental/{filename}", harness.CASE_COUNTS)
                cases.extend(items)
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
