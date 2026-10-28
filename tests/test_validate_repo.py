"""Exercise repository validation against isolated, deliberately invalid fixtures."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_repo as validator
from test_run_evals import make_cases

REAL_COMMAND = validator.command


class RepositoryValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        environment = patch.dict(os.environ, {"GITHUB_ACTIONS": "false", "GITHUB_REPOSITORY": ""})
        environment.start()
        self.addCleanup(environment.stop)
        self.temporary = tempfile.TemporaryDirectory(prefix="korean-validator-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for relative in validator.MANIFEST:
            self.write(relative, "fixture\n")
        self.skill = f"{validator.SKILL_DIR}/SKILL.md"
        self.yaml = f"{validator.SKILL_DIR}/agents/openai.yaml"
        self.context_link = "[Context](references/context-audience-boundary.md)\n"
        self.write(self.skill, "---\nname: natural-korean-writing\ndescription: Rewrite Korean for its reader.\nlicense: MIT\n---\n# Korean\n" + self.context_link)
        self.write(self.yaml, 'interface:\n  display_name: "Korean writing"\n  short_description: "Natural Korean writing and revision"\n  default_prompt: "Use $natural-korean-writing."\n')
        self.write("README.md", validator.INTRODUCTION + "\n[English](README.en.md)\n")
        self.write("README.en.md", "gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing\n")
        self.write("LICENSE", "MIT License\nCopyright (c) 2026 Jiyoung Jung\n")
        self.write(".gitattributes", "* text=auto eol=lf\n*.png binary\n*.jpg binary\n*.jpeg binary\n*.gif binary\n")
        self.write(".gitignore", ".eval-work/\n")
        self.write("scripts/validate_repo.py", "# Validation fixture\n")
        self.write("tests/test_validate_repo.py", "# Test fixture\n")
        make_cases(self.root)
        self.gh_path = self.root / "gh-fixture.exe"
        self.gh_path.write_bytes(b"fixture")

    def write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", errors="strict", newline="\n")

    @staticmethod
    def gh_command(args: list[str], root: Path, **kwargs: object) -> str:
        if args[0] == "git":
            return REAL_COMMAND(args, root, **kwargs)
        if args[1:] == ["--version"]:
            return "gh version 2.97.0 (2026-07-31)\n"
        if args[1:] == ["api", "user", "--jq", ".login"]:
            return "Jiyeong-kor\n"
        if args[1:] == ["api", f"repos/{validator.PUBLIC_REPOSITORY}", "--jq", ".full_name"]:
            return validator.PUBLIC_REPOSITORY + "\n"
        if args[1:] == ["skill", "--help"]:
            return "Manage skills\n"
        raise AssertionError(f"unexpected command arguments: {args}")

    def validate(self, phase: str = "build") -> validator.Report:
        with patch.object(validator, "command", side_effect=self.gh_command):
            return validator.validate_repo(self.root, phase, self.gh_path)

    def assert_fails(self, item: str, phase: str = "build") -> None:
        report = self.validate(phase)
        self.assertTrue(any(item in error for error in report.errors), report.errors)

    def test_valid_build_and_pre_eval(self) -> None:
        self.assertEqual([], self.validate().errors)
        with patch.object(validator.run_evals, "verify_tracked") as verified:
            self.assertEqual([], self.validate("pre-eval").errors)
            verified.assert_not_called()

    def test_invalid_skill_name(self) -> None:
        self.write(self.skill, "---\nname: Invalid--Name\ndescription: Rewrite Korean.\nlicense: MIT\n---\n")
        self.assert_fails("name syntax")

    def test_existing_line_ending_attributes_are_required(self) -> None:
        (self.root / ".gitattributes").unlink()
        self.assert_fails(".gitattributes", "pre-eval")

    def test_frontmatter_requires_only_name_description_and_mit_license(self) -> None:
        for fields, expected in (("", "frontmatter fields"), ("license: Apache-2.0\n", "license"), ("license: MIT\nmetadata: extra\n", "frontmatter fields")):
            with self.subTest(fields=fields):
                self.write(self.skill, f"---\nname: natural-korean-writing\ndescription: Rewrite Korean.\n{fields}---\n")
                self.assert_fails(expected)

    def test_description_must_be_a_yaml_string(self) -> None:
        for value in ("true", "NULL", "123", "3.5", "2026-08-31", "[words]"):
            with self.subTest(value=value):
                self.write(self.skill, f"---\nname: natural-korean-writing\ndescription: {value}\nlicense: MIT\n---\n")
                self.assert_fails("frontmatter")
        for value in ('"true"', "3D", "1.2.3"):
            self.write(self.skill, f"---\nname: natural-korean-writing\ndescription: {value}\nlicense: MIT\n---\n" + self.context_link)
            self.assertEqual([], self.validate().errors)

    def test_changed_and_repeated_introduction(self) -> None:
        for text in ("바꾼 소개 문장", validator.INTRODUCTION * 2):
            with self.subTest(text=text):
                self.write("README.md", text)
                self.assert_fails("introduction", "pre-eval")

    def test_duplicate_case_id(self) -> None:
        path = self.root / "evals/core.json"
        cases = json.loads(path.read_text(encoding="utf-8", errors="strict"))
        cases[1]["id"] = cases[0]["id"]
        self.write("evals/core.json", json.dumps(cases, ensure_ascii=False))
        self.assert_fails("case schema")

    def test_context_file_is_required_in_all_phases_and_manifest(self) -> None:
        self.assertIn("evals/context.json", validator.MANIFEST)
        (self.root / "evals/context.json").unlink()
        self.assert_fails("case schema")
        self.assert_fails("required file", "pre-eval")
        with patch.object(validator.run_evals, "verify_tracked", side_effect=ValueError("missing real results")):
            self.assert_fails("required file", "final")

    def test_pragmatics_file_is_required_in_all_phases_and_manifest(self) -> None:
        self.assertIn("evals/pragmatics.json", validator.MANIFEST)
        self.assertEqual(len(validator.MANIFEST), len(set(validator.MANIFEST)))
        repository = Path(__file__).resolve().parents[1]
        supplemental = {
            path.relative_to(repository).as_posix()
            for path in (repository / "evals/supplemental").glob("*.json")
        }
        self.assertLessEqual(supplemental, set(validator.MANIFEST))
        runtime_paths = {
            path.relative_to(repository).as_posix()
            for path in (repository / validator.SKILL_DIR).rglob("*") if path.is_file()
        }
        self.assertEqual(runtime_paths, {path for path in validator.MANIFEST
                                       if path.startswith(validator.SKILL_DIR + "/")})
        (self.root / "evals/pragmatics.json").unlink()
        self.assert_fails("case schema")
        self.assert_fails("required file", "pre-eval")
        with patch.object(validator.run_evals, "verify_tracked", side_effect=ValueError("missing real results")):
            self.assert_fails("required file", "final")

    def test_context_reference_must_exist_and_have_content(self) -> None:
        relative = f"{validator.SKILL_DIR}/references/context-audience-boundary.md"
        self.assertIn(relative, validator.MANIFEST)
        (self.root / relative).unlink()
        self.assert_fails("context reference")
        self.assert_fails("relative link")
        self.assert_fails("required file", "pre-eval")
        for content in ("", " \n"):
            with self.subTest(content=content):
                self.write(relative, content)
                self.assert_fails("context reference")

    def test_context_reference_link_cannot_be_removed_broken_or_only_an_example(self) -> None:
        original = (self.root / self.skill).read_text(encoding="utf-8", errors="strict")
        variants = (
            "",
            "[Context](references/missing-context.md)\n",
            "```text\n" + self.context_link + "```\n",
            "`[Context](references/context-audience-boundary.md)`\n",
        )
        for link in variants:
            with self.subTest(link=link):
                self.write(self.skill, original.replace(self.context_link, link))
                self.assert_fails("context reference")

    def test_broken_relative_link(self) -> None:
        self.write("README.en.md", "[Missing](missing.md)\n")
        self.assert_fails("relative link")

    def test_image_reference_and_encoded_relative_links(self) -> None:
        self.write("examples/한글 파일.md", "내용\n")
        self.write("README.en.md", "![Preview](assets/social-preview.png)\n[Note](examples/%ED%95%9C%EA%B8%80%20%ED%8C%8C%EC%9D%BC.md)\n[Guide][guide]\n[guide]: README.md#usage\n")
        self.assertEqual([], self.validate().errors)
        (self.root / "assets/social-preview.png").unlink()
        self.assert_fails("relative link")

    def test_unresolved_owner_placeholder(self) -> None:
        self.write("README.en.md", "gh skill install OWNER/natural-korean-writing\n")
        self.assert_fails("public content", "pre-eval")

    def test_short_description_out_of_range(self) -> None:
        self.write(self.yaml, 'interface:\n  display_name: "Korean"\n  short_description: "Short"\n  default_prompt: "Use $natural-korean-writing."\n')
        self.assert_fails("short_description")

    def test_unquoted_yaml_string(self) -> None:
        self.write(self.yaml, 'interface:\n  display_name: Korean\n  short_description: "Natural Korean writing and revision"\n  default_prompt: "Use $natural-korean-writing."\n')
        self.assert_fails("quoted strings")

    def test_invalid_utf8_and_bom(self) -> None:
        for data in (b"\xff", b"\xef\xbb\xbfKorean\n"):
            with self.subTest(data=data):
                (self.root / "README.en.md").write_bytes(data)
                self.assert_fails("UTF-8")

    def test_build_does_not_require_public_docs_or_results(self) -> None:
        for relative in ("README.md", "README.en.md", "LICENSE", *validator.RESULT_FILES):
            (self.root / relative).unlink()
        with patch.object(validator.run_evals, "verify_tracked") as verified:
            report = validator.validate_repo(self.root, "build")
            self.assertEqual([], report.errors)
            verified.assert_not_called()
        self.assert_fails("required file", "pre-eval")

    def test_final_requires_actual_results(self) -> None:
        with patch.object(validator.run_evals, "verify_tracked", side_effect=ValueError("missing real results")) as verified:
            self.assert_fails("recorded results", "final")
            verified.assert_called_once_with(self.root.resolve(), version="v0.1.0")

    def test_new_release_selects_its_records_without_replacing_history(self) -> None:
        cases = validator.run_evals.load_cases(self.root)
        rows = [{"id": case["id"], "output": case.get("expected_exact", "결과"),
                 "case_pass": True, "critical_failure": False} for case in cases]
        self.write("evals/runs/v0.1.1.jsonl", "".join(json.dumps(row) + "\n" for row in rows))
        self.write("evals/results-v0.1.1.md", "Evaluation fixture\n")
        self.write("evals/runs/v0.1.1.inputs.json", "{}\n")
        original = (self.root / "evals/runs/v0.1.0.jsonl").read_bytes()
        with patch.object(validator, "command", side_effect=self.gh_command), \
                patch.object(validator.run_evals, "verify_tracked") as verified:
            report = validator.validate_repo(self.root, "final", self.gh_path, version="v0.1.1")
        self.assertEqual([], report.errors)
        verified.assert_called_once_with(self.root.resolve(), version="v0.1.1")
        self.assertEqual(original, (self.root / "evals/runs/v0.1.0.jsonl").read_bytes())
        rows[-1]["case_pass"] = False
        self.write("evals/runs/v0.1.1.jsonl", "".join(json.dumps(row) + "\n" for row in rows))
        report = validator.Report()
        validator.check_release(self.root, cases, report, version="v0.1.1")
        self.assertTrue(any("release pragmatics" in error for error in report.errors))

    def test_new_release_missing_records_and_invalid_versions_fail(self) -> None:
        with patch.object(validator, "command", side_effect=self.gh_command), \
                patch.object(validator.run_evals, "verify_tracked", side_effect=ValueError("missing results")):
            pre_eval = validator.validate_repo(self.root, "pre-eval", self.gh_path, version="v0.1.1")
            final = validator.validate_repo(self.root, "final", self.gh_path, version="v0.1.1")
        self.assertEqual([], pre_eval.errors)
        for relative in validator.release_files("v0.1.1"):
            self.assertTrue(any(relative in error for error in final.errors), final.errors)
        self.assertTrue(any("recorded results" in error for error in final.errors))
        for version in ("../v0.1.1", "main", "", "v0.1.1/extra"):
            with self.subTest(version=version):
                report = validator.validate_repo(self.root, version=version)
                self.assertTrue(any("[version]" in error for error in report.errors))

    def test_exact_output_is_release_gate_even_when_reviewers_pass(self) -> None:
        cases = validator.run_evals.load_cases(self.root)
        rows = [{"id": case["id"], "output": case.get("expected_exact", "결과"), "case_pass": True, "critical_failure": False} for case in cases]
        for changed in (row for case, row in zip(cases, rows, strict=True) if case["category"] == "approved-copy"):
            with self.subTest(case_id=changed["id"]):
                original = changed["output"]
                changed["output"] += " "
                self.write("evals/runs/v0.1.0.jsonl", "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
                report = validator.Report()
                validator.check_release(self.root, cases, report)
                self.assertTrue(any("release exact output" in error for error in report.errors), report.errors)
                changed["output"] = original

    def test_free_rewriting_variants_pass_release_without_exact_matching(self) -> None:
        cases = validator.run_evals.load_cases(self.root)
        variants = {
            "meaning-close-001": "기획서 전체를 검토해 서로 맞지 않는 내용도 함께 수정한다.",
            "register-honorific-001": "제안해 주신 문장이 더 자연스러워요.",
        }
        rows = [{"id": case["id"], "output": variants.get(case["id"], case.get("expected_exact", "결과")),
                 "case_pass": True, "critical_failure": False} for case in cases]
        self.write("evals/runs/v0.1.0.jsonl", "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
        report = validator.Report()
        validator.check_release(self.root, cases, report)
        self.assertEqual([], report.errors)

    def test_release_thresholds_critical_and_mandatory_cases(self) -> None:
        cases = validator.run_evals.load_cases(self.root)
        base = [{"id": case["id"], "output": case.get("expected_exact", "결과"), "case_pass": True, "critical_failure": False} for case in cases]
        core = [case["id"] for case in cases if case["category"] in validator.run_evals.CORE_CATEGORIES
                and case["id"] not in {"register-honorific-001", "meaning-close-001"}]
        approved = [case["id"] for case in cases if case["category"] == "approved-copy"]
        punctuation = [case["id"] for case in cases if case["category"] == "punctuation"]
        context = [case["id"] for case in cases if case["category"] == "context"]
        pragmatics = [case["id"] for case in cases if case["category"] == "pragmatics"]
        scenarios = (
            ([], False, None), (core[:2], False, None), (core[:3], False, "release core"),
            (approved[:1], False, "release approved-copy"), (punctuation[:1], False, "release punctuation"),
            (core[:1], True, "release critical failures"),
            *[([case_id], False, "release mandatory case") for case_id in validator.run_evals.REQUIRED_CASES],
            *[([case_id], False, "release context") for case_id in context],
            (core[:2] + context[:1], False, "release context"),
            (context[:1], True, "release critical failures"),
            *[([case_id], False, "release pragmatics") for case_id in pragmatics],
            (core[:2] + pragmatics[:1], False, "release pragmatics"),
            (pragmatics[:1], True, "release critical failures"),
        )
        for failed, critical, expected in scenarios:
            with self.subTest(failed=failed, critical=critical):
                rows = [dict(row) for row in base]
                for row in rows:
                    if row["id"] in failed:
                        row["case_pass"] = False
                        row["critical_failure"] = critical
                self.write("evals/runs/v0.1.0.jsonl", "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
                report = validator.Report()
                validator.check_release(self.root, cases, report)
                if expected is None:
                    self.assertEqual([], report.errors)
                else:
                    self.assertTrue(any(expected in error for error in report.errors), report.errors)

    def test_relative_gh_path_and_wrong_version_fail(self) -> None:
        report = validator.validate_repo(self.root, "pre-eval", Path("gh"))
        self.assertTrue(any("absolute executable path" in error for error in report.errors))
        with patch.object(validator, "command", return_value="gh version 2.92.0\n"):
            report = validator.validate_repo(self.root, "pre-eval", self.gh_path)
        self.assertTrue(any("2.97.0 is required" in error for error in report.errors))

    def test_subprocess_uses_argument_list_and_strict_utf8(self) -> None:
        args = [str(self.gh_path), "--version"]
        result = subprocess.CompletedProcess(args, 0, "version\n", "")
        with patch.object(validator.subprocess, "run", return_value=result) as executed:
            self.assertEqual("version\n", REAL_COMMAND(args, self.root))
        self.assertEqual(args, executed.call_args.args[0])
        self.assertFalse(executed.call_args.kwargs["shell"])
        self.assertEqual("utf-8", executed.call_args.kwargs["encoding"])
        self.assertEqual("strict", executed.call_args.kwargs["errors"])
        self.assertEqual(30, executed.call_args.kwargs["timeout"])

    def test_successful_command_does_not_hide_stderr(self) -> None:
        result = subprocess.CompletedProcess(["git"], 0, "", "warning: fixture warning\n")
        stderr = io.StringIO()
        with patch.object(validator.subprocess, "run", return_value=result), redirect_stderr(stderr):
            REAL_COMMAND(["git", "status"], self.root)
        self.assertEqual("warning: fixture warning\n", stderr.getvalue())

    def test_owner_check_exempts_unrelated_official_sources(self) -> None:
        self.write("README.en.md", "https://github.com/cli/cli/releases\nhttps://github.com/actions/checkout\ngh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing\n")
        self.assertEqual([], self.validate("pre-eval").errors)
        self.write("README.en.md", "https://github.com/wrong-account/natural-korean-writing\n")
        self.assert_fails("GitHub owner", "pre-eval")

    def test_local_contributor_identity_does_not_replace_public_owner(self) -> None:
        def command(args: list[str], root: Path, **kwargs: object) -> str:
            if args[1:] == ["api", "user", "--jq", ".login"]:
                return "other-contributor\n"
            return self.gh_command(args, root, **kwargs)

        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "wrong-account/unrelated"}), \
                patch.object(validator, "command", side_effect=command) as executed:
            report = validator.validate_repo(self.root, "pre-eval", self.gh_path)
        self.assertEqual([], report.errors)
        api_calls = [call.args[0] for call in executed.call_args_list if call.args[0][1] == "api"]
        self.assertEqual([
            [str(self.gh_path), "api", "user", "--jq", ".login"],
            [str(self.gh_path), "api", f"repos/{validator.PUBLIC_REPOSITORY}", "--jq", ".full_name"],
        ], api_calls)

    def test_local_identity_rejects_invalid_account_response(self) -> None:
        for account in ("", "invalid/login\n"):
            with self.subTest(account=account):
                def command(args: list[str], root: Path, account: str = account, **kwargs: object) -> str:
                    if args[1:] == ["api", "user", "--jq", ".login"]:
                        return account
                    return self.gh_command(args, root, **kwargs)

                with patch.object(validator, "command", side_effect=command):
                    report = validator.validate_repo(self.root, "pre-eval", self.gh_path)
                self.assertTrue(any("valid account login" in error for error in report.errors), report.errors)

    def test_actions_identity_uses_repository_owner_and_checks_public_links(self) -> None:
        repository = "jiyeong-kor/natural-korean-writing"
        api_args = [str(self.gh_path), "api", f"repos/{repository}", "--jq", ".owner.login"]

        def command(args: list[str], root: Path, **kwargs: object) -> str:
            return "Jiyeong-kor\n" if args == api_args else self.gh_command(args, root, **kwargs)

        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": repository}), \
                patch.object(validator, "command", side_effect=command) as executed:
            report = validator.validate_repo(self.root, "pre-eval", self.gh_path)
            self.assertEqual([], report.errors)
            api_calls = [call.args[0] for call in executed.call_args_list if call.args[0][1] == "api"]
            self.assertEqual([
                api_args,
                [str(self.gh_path), "api", f"repos/{validator.PUBLIC_REPOSITORY}", "--jq", ".full_name"],
            ], api_calls)
            self.write("README.en.md", "https://github.com/wrong-account/natural-korean-writing\n")
            report = validator.validate_repo(self.root, "pre-eval", self.gh_path)
        self.assertTrue(any("GitHub owner" in error for error in report.errors), report.errors)

    def test_fork_actions_preserves_canonical_public_links(self) -> None:
        repository = "other-contributor/forked-skill"
        api_args = [str(self.gh_path), "api", f"repos/{repository}", "--jq", ".owner.login"]

        def command(args: list[str], root: Path, **kwargs: object) -> str:
            return "other-contributor\n" if args == api_args else self.gh_command(args, root, **kwargs)

        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": repository}), \
                patch.object(validator, "command", side_effect=command) as executed:
            report = validator.validate_repo(self.root, "pre-eval", self.gh_path)
            self.assertEqual([], report.errors)
            api_calls = [call.args[0] for call in executed.call_args_list if call.args[0][1] == "api"]
            self.assertEqual([
                api_args,
                [str(self.gh_path), "api", f"repos/{validator.PUBLIC_REPOSITORY}", "--jq", ".full_name"],
            ], api_calls)
            self.write("README.en.md", "https://github.com/other-contributor/natural-korean-writing\n")
            report = validator.validate_repo(self.root, "pre-eval", self.gh_path)
        self.assertTrue(any("GitHub owner" in error for error in report.errors), report.errors)

    def test_canonical_repository_identity_must_match(self) -> None:
        invalid_identities = ("", "wrong-account/natural-korean-writing", "Jiyeong-kor/wrong-repository",
                              "Jiyeong-kor/natural-korean-writing/extra")
        for identity in invalid_identities:
            with self.subTest(identity=identity):
                def command(args: list[str], root: Path, identity: str = identity, **kwargs: object) -> str:
                    if args[1:] == ["api", f"repos/{validator.PUBLIC_REPOSITORY}", "--jq", ".full_name"]:
                        return identity
                    return self.gh_command(args, root, **kwargs)

                with patch.object(validator, "command", side_effect=command):
                    report = validator.validate_repo(self.root, "pre-eval", self.gh_path)
                self.assertTrue(any("canonical repository identity" in error for error in report.errors), report.errors)

    def test_actions_rejects_missing_or_malformed_repository_before_api_call(self) -> None:
        invalid_repositories = (None, "", "missing-owner", "/repo", "owner/", "owner/repo/extra",
                                "owner/../repo", "owner/.", "owner/..", "owner/repo?query=1",
                                "owner/repo\n", "owner_name/repo", "-owner/repo")
        for repository in invalid_repositories:
            with self.subTest(repository=repository), \
                    patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), \
                    patch.object(validator, "command", side_effect=self.gh_command) as executed:
                if repository is None:
                    os.environ.pop("GITHUB_REPOSITORY", None)
                else:
                    os.environ["GITHUB_REPOSITORY"] = repository
                report = validator.validate_repo(self.root, "pre-eval", self.gh_path)
                self.assertTrue(any("GITHUB_REPOSITORY must contain" in error for error in report.errors), report.errors)
                self.assertFalse(any(call.args[0][1] == "api" for call in executed.call_args_list))

    def test_actions_rejects_wrong_or_invalid_owner_response(self) -> None:
        repository = "Jiyeong-kor/natural-korean-writing"
        for owner, error in (("wrong-account\n", "owner does not match"), ("", "valid account login"),
                             ("invalid/login\n", "valid account login")):
            with self.subTest(owner=owner):
                def command(args: list[str], root: Path, owner: str = owner, **kwargs: object) -> str:
                    if args[1:] == ["api", f"repos/{repository}", "--jq", ".owner.login"]:
                        return owner
                    return self.gh_command(args, root, **kwargs)

                with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": repository}), \
                        patch.object(validator, "command", side_effect=command):
                    report = validator.validate_repo(self.root, "pre-eval", self.gh_path)
                self.assertTrue(any(error in message for message in report.errors), report.errors)

    def test_wrong_public_author(self) -> None:
        self.write("README.en.md", "Author: Jiyeong Jung\n")
        self.assert_fails("author", "pre-eval")

    def test_generic_user_paths_fail_without_personal_identifiers(self) -> None:
        for account in ("sample-user-a", "sample-user-b"):
            for user_path in (
                "Users/" + account + "/draft.md",
                "C:/Users/" + account + "/draft.md",
                "D:\\Users\\" + account + "\\draft.md",
            ):
                with self.subTest(user_path=user_path):
                    self.write("README.en.md", user_path + "\n")
                    self.assert_fails("public content", "pre-eval")

    def test_fixture_literals_do_not_exempt_comments_or_docstrings(self) -> None:
        self.write("tests/test_validate_repo.py", 'value = "OWNER/REPO"\n')
        self.assertEqual([], self.validate("pre-eval").errors)
        for extra in ('# OWNER/REPO\n', '"""OWNER/REPO"""\n'):
            self.write("tests/test_validate_repo.py", extra + 'value = "OWNER/REPO"\n')
            self.assert_fails("public content", "pre-eval")

    def test_validator_pattern_definitions_do_not_exempt_other_strings(self) -> None:
        self.write("scripts/validate_repo.py", 'FORBIDDEN_PATTERNS = ("TODO", "OWNER/REPO")\n')
        self.assertEqual([], self.validate("pre-eval").errors)
        self.write("scripts/validate_repo.py", 'FORBIDDEN_PATTERNS = ("TODO",)\nmessage = "OWNER/REPO"\n')
        self.assert_fails("public content", "pre-eval")

    def test_print_digest_ignores_phase_and_prints_only_digest(self) -> None:
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(validator.run_evals, "compute_digest", return_value="A" * 64), patch.object(validator, "validate_repo") as validated:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = validator.main(["--root", str(self.root), "--print-digest"])
        self.assertEqual(0, code)
        self.assertEqual("A" * 64 + "\n", stdout.getvalue())
        self.assertEqual("", stderr.getvalue())
        validated.assert_not_called()

    @unittest.skipUnless(shutil.which("git"), "Git is required for staged-manifest tests")
    def test_staged_manifest_includes_selected_release(self) -> None:
        for relative in validator.release_files("v0.1.1"):
            self.write(relative, "release fixture\n")
        REAL_COMMAND(["git", "init", "-b", "main"], self.root)
        REAL_COMMAND(["git", "-c", "core.autocrlf=false", "add", "--",
                      *validator.MANIFEST, *validator.release_files("v0.1.1")], self.root)
        report = validator.Report()
        validator.check_staged(self.root, report, version="v0.1.1")
        self.assertEqual([], report.errors)
        REAL_COMMAND(["git", "rm", "--cached", "--", "evals/runs/v0.1.1.inputs.json"], self.root)
        report = validator.Report()
        validator.check_staged(self.root, report, version="v0.1.1")
        self.assertTrue(any("v0.1.1.inputs.json" in error for error in report.errors))

    @unittest.skipUnless(shutil.which("git"), "Git is required for staged-manifest tests")
    def test_staged_manifest_missing_and_ignored_file(self) -> None:
        def git(*args: str) -> None:
            subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True,
                           encoding="utf-8", errors="strict", shell=False, timeout=30, check=True)
        git("init", "-b", "main")
        git("-c", "core.autocrlf=false", "add", "--", *validator.MANIFEST)
        report = validator.Report()
        validator.check_staged(self.root, report)
        self.assertEqual([], report.errors)
        git("rm", "--cached", "--", "README.en.md")
        report = validator.Report()
        validator.check_staged(self.root, report)
        self.assertTrue(any("staged manifest" in error for error in report.errors))
        git("-c", "core.autocrlf=false", "add", "--", "README.en.md")
        self.write(".gitignore", "README.md\n")
        report = validator.Report()
        validator.check_staged(self.root, report)
        self.assertTrue(any("ignored=" in error and "README.md" in error for error in report.errors))


if __name__ == "__main__":
    unittest.main()
