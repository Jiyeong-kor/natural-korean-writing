#!/usr/bin/env python3
"""Validate the public repository without generating evaluation results."""

from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import subprocess
import sys
import tokenize
from pathlib import Path
from urllib.parse import unquote, urlsplit

import run_evals

SKILL_NAME = "natural-korean-writing"
SKILL_DIR = f"skills/{SKILL_NAME}"
INTRODUCTION = "원래 의미를 그대로 유지하면서 번역투와 어색한 표현을 글의 목적과 독자에 맞게 다듬을 수 있는 자연스러운 한국어 스킬입니다."
AUTHOR = "Jiyoung Jung"
PUBLIC_REPOSITORY = "Jiyeong-kor/natural-korean-writing"
MANIFEST = (
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/installation.yml",
    ".github/ISSUE_TEMPLATE/writing-quality.yml",
    ".github/ISSUE_TEMPLATE/feature-request.yml",
    ".github/pull_request_template.md",
    ".github/workflows/validate.yml",
    "assets/social-preview.svg",
    "assets/social-preview.png",
    "evals/README.md",
    "evals/compatibility-v0.1.0.json",
    "evals/core.json",
    "evals/approved-copy.json",
    "evals/punctuation.json",
    "evals/context.json",
    "evals/pragmatics.json",
    "evals/supplemental/application-action.json",
    "evals/supplemental/revision-review.json",
    "evals/supplemental/evidence-selection.json",
    "evals/supplemental/ai-contribution-closing.json",
    "evals/supplemental/application-contribution-tone.json",
    "evals/supplemental/application-duty-evidence.json",
    "evals/supplemental/application-tone-approval.json",
    "evals/supplemental/application-workflow.json",
    "evals/supplemental/korean-document-layout.json",
    "evals/supplemental/name-quotation-scope.json",
    "evals/supplemental/resume-information-selection.json",
    "evals/supplemental/resume-project-status.json",
    "evals/supplemental/resume-technology-outline.json",
    "evals/supplemental/scoped-korean-wording.json",
    "evals/results-v0.1.0.md",
    "evals/runs/v0.1.0.jsonl",
    "examples/before-after.md",
    "scripts/run_evals.py",
    "scripts/validate_repo.py",
    f"{SKILL_DIR}/SKILL.md",
    f"{SKILL_DIR}/agents/openai.yaml",
    f"{SKILL_DIR}/references/artifact-style-profiles.md",
    f"{SKILL_DIR}/references/application-answer-workflow.md",
    f"{SKILL_DIR}/references/context-audience-boundary.md",
    f"{SKILL_DIR}/references/korean-language-principles.md",
    f"{SKILL_DIR}/references/official-korean-sources.md",
    f"{SKILL_DIR}/references/rewrite-examples.md",
    f"{SKILL_DIR}/references/korean-punctuation-rules.md",
    "tests/test_run_evals.py",
    "tests/test_validate_repo.py",
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.en.md",
    "README.md",
)
FORBIDDEN_PATTERNS = (
    "TODO", "[TODO", "OWNER/REPO", "OWNER/", "<owner>",
    "author@example.com", "example.com", "C:\\Users\\", "Users/",
)
RESULT_FILES = {"evals/results-v0.1.0.md", "evals/runs/v0.1.0.jsonl"}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".gz", ".ico", ".woff", ".woff2", ".ttf"}


class Report:
    def __init__(self) -> None:
        self.checks = 0
        self.errors: list[str] = []

    def check(self, condition: bool, path: str, item: str, reason: str) -> None:
        self.checks += 1
        if not condition:
            self.errors.append(f"{path} [{item}]: {reason}")


def command(args: list[str], root: Path, *, input_text: str | None = None,
            allowed_codes: tuple[int, ...] = (0,)) -> str:
    """Keep subprocess execution explicit, bounded, and UTF-8 strict."""
    result = subprocess.run(args, cwd=root, input=input_text, capture_output=True,
                            text=True, encoding="utf-8", errors="strict",
                            shell=False, timeout=30, check=False)
    if result.returncode not in allowed_codes:
        detail = (result.stderr or result.stdout).strip()
        raise ValueError(f"command exited {result.returncode}: {detail}")
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr)
    return result.stdout


def read_text(path: Path) -> str:
    value = path.read_text(encoding="utf-8", errors="strict")
    if value.startswith("\ufeff"):
        raise ValueError("UTF-8 BOM is not allowed")
    return value


def scalar(value: str, *, quoted: bool = False) -> str:
    value = value.strip()
    if value.startswith('"'):
        parsed = json.loads(value)
        if not isinstance(parsed, str):
            raise ValueError("expected a quoted string")
        return parsed
    if re.fullmatch(r"'(?:[^']|'')*'", value):
        return value[1:-1].replace("''", "'")
    if quoted or not value or value in {"|", ">", "null", "~"}:
        raise ValueError("expected a nonempty string" if not quoted else "strings must be quoted")
    # The repository uses simple scalar fields, not general YAML documents.
    reserved = {"null", "true", "false", "yes", "no", "on", "off", ".inf", "+.inf", "-.inf", ".nan"}
    number = (r"[+-]?(?:[0-9][0-9_]*(?:\.[0-9_]*)?(?:[eE][+-]?[0-9]+)?"
              r"|\.[0-9_]+(?:[eE][+-]?[0-9]+)?|0x[0-9a-fA-F_]+|0o[0-7_]+|0b[01_]+"
              r"|[0-9]+(?::[0-5]?[0-9])+(?:\.[0-9_]*)?)")
    if value.lower() in reserved or re.fullmatch(number, value) or re.match(r"\d{4}-\d{2}-\d{2}(?:[Tt ]|$)", value):
        raise ValueError("frontmatter values must be strings; quote numeric, date, boolean, or null-like text")
    if value[0] in "'[{&*!|>@`" or ": " in value or " #" in value:
        raise ValueError("quote complex YAML scalar text")
    return value


def frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise ValueError("missing YAML frontmatter delimiters")
    fields: dict[str, str] = {}
    for line in lines[1:lines.index("---", 1)]:
        if not line.strip():
            continue
        match = re.fullmatch(r"([a-z_]+):\s*(.*)", line)
        if not match or match[1] in fields:
            raise ValueError("frontmatter must contain unique top-level scalar fields")
        fields[match[1]] = scalar(match[2])
    return fields


def interface_strings(text: str) -> dict[str, str]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines or lines[0] != "interface:":
        raise ValueError("expected an interface mapping")
    fields: dict[str, str] = {}
    for line in lines[1:]:
        match = re.fullmatch(r"  ([a-z_]+):\s*(.*)", line)
        if not match or match[1] in fields:
            raise ValueError("expected unique interface string fields")
        fields[match[1]] = scalar(match[2], quoted=True)
    if set(fields) != {"display_name", "short_description", "default_prompt"}:
        raise ValueError("expected display_name, short_description, and default_prompt")
    return fields


def prose_markdown(text: str) -> str:
    """Exclude examples in code fences from Markdown link interpretation."""
    kept: list[str] = []
    fence = ""
    width = 0
    for line in text.splitlines(keepends=True):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            if match and match[1][0] == fence and len(match[1]) >= width:
                fence = ""
            kept.append("\n")
        elif match:
            fence, width = match[1][0], len(match[1])
            kept.append("\n")
        else:
            kept.append(line)
    return re.sub(r"(`+).*?\1", "", "".join(kept), flags=re.DOTALL)


def relative_targets(text: str) -> list[str]:
    text = prose_markdown(text)
    inline = re.findall(r"\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)", text)
    definitions = re.findall(r"^ {0,3}\[[^\]\n]+\]:\s*(<[^>]+>|\S+)", text, flags=re.MULTILINE)
    targets = []
    for target in inline + definitions:
        target = target.strip("<>")
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        targets.append(unquote(parsed.path))
    return targets


def scan_text(path: str, text: str) -> str:
    """Exclude only validation definitions and synthetic Python string fixtures."""
    is_test = path.startswith("tests/test_") and path.endswith(".py")
    if not is_test and path != "scripts/validate_repo.py":
        return text
    try:
        tree = ast.parse(text)
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (SyntaxError, tokenize.TokenError):
        return text
    docstring_lines = set()
    definition_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.body and isinstance(node.body[0], ast.Expr):
                value = node.body[0].value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    docstring_lines.update(range(value.lineno, value.end_lineno + 1))
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "FORBIDDEN_PATTERNS" for t in node.targets):
            definition_lines.update(range(node.lineno, node.end_lineno + 1))
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    masked = list(text)
    for token in tokens:
        permitted = (is_test and token.start[0] not in docstring_lines) or token.start[0] in definition_lines
        if token.type == tokenize.STRING and permitted:
            start = offsets[token.start[0] - 1] + token.start[1]
            end = offsets[token.end[0] - 1] + token.end[1]
            masked[start:end] = ["\n" if char == "\n" else " " for char in text[start:end]]
    return "".join(masked)


def check_owner(text: str, owner: str) -> list[str]:
    mismatches = []
    patterns = (
        r"https?://(?:github\.com|raw\.githubusercontent\.com)/([A-Za-z0-9-]+)/natural-korean-writing(?:\.git)?(?=[/#?\s)\"']|$)",
        r"git@github\.com:([A-Za-z0-9-]+)/natural-korean-writing(?:\.git)?(?=[\s\"']|$)",
        r"\bgh\s+skill\s+(?:install|preview)\s+[\"']?([A-Za-z0-9-]+)/natural-korean-writing(?=[@/\s\"']|$)",
        r"https?://img\.shields\.io/github/(?:[^/\s]+/)*?([A-Za-z0-9-]+)/natural-korean-writing(?=[/?\s)\"']|$)",
    )
    for pattern in patterns:
        for found in re.findall(pattern, text, flags=re.IGNORECASE):
            if found != owner:
                mismatches.append(found)
    return sorted(set(mismatches))


def release_files(version: str) -> tuple[str, ...]:
    run_evals._version(version)
    if version == "v0.1.0":
        return ()
    return (f"evals/results-{version}.md", f"evals/runs/{version}.jsonl",
            f"evals/runs/{version}.inputs.json")


def check_staged(root: Path, report: Report, version: str = "v0.1.0") -> None:
    try:
        staged = set(filter(None, command(["git", "ls-files", "--cached", "-z"], root).split("\0")))
        manifest = (*MANIFEST, *release_files(version))
        expected = set(manifest)
        missing, extra = sorted(expected - staged), sorted(staged - expected)
        report.check(not missing and not extra, ".", "staged manifest", f"missing={missing}; extra={extra}")
        ignored = command(["git", "check-ignore", "--no-index", "--stdin", "-z"], root,
                          input_text="\0".join(manifest) + "\0", allowed_codes=(0, 1))
        report.check(not ignored, ".gitignore", "required paths", f"ignored={list(filter(None, ignored.split(chr(0))))}")
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired) as exc:
        report.check(False, ".", "staged manifest", str(exc))


def check_release(root: Path, cases: list[dict], report: Report, version: str = "v0.1.0") -> None:
    """Apply release criteria only after the harness verifies record integrity."""
    run_evals._version(version)
    path = f"evals/runs/{version}.jsonl"
    rows = [json.loads(line) for line in read_text(root / path).splitlines()]
    by_id = {row["id"]: row for row in rows}
    for group, minimum in (
        ("core", 22), ("approved-copy", 2), ("punctuation", 7), ("context", 10), ("pragmatics", 7),
    ):
        members = [case for case in cases
                   if ("core" if case["category"] in run_evals.CORE_CATEGORIES else case["category"]) == group]
        passed = sum(by_id[case["id"]]["case_pass"] is True for case in members)
        report.check(passed >= minimum, path, f"release {group}", f"{passed}/{len(members)} passed; need {minimum}")
    report.check(not any(row["critical_failure"] for row in rows), path,
                 "release critical failures", "critical failures must be zero")
    for case in cases:
        if "expected_exact" in case:
            report.check(by_id[case["id"]]["output"] == case["expected_exact"], path,
                         "release exact output", f"{case['id']} differs from the exact reference")
    for case_id in run_evals.REQUIRED_CASES:
        report.check(by_id[case_id]["case_pass"] is True, path, "release mandatory case", f"{case_id} failed")


def validate_repo(root: Path, phase: str = "final", gh_path: Path | None = None,
                  *, check_staged_manifest: bool = False, version: str = "v0.1.0") -> Report:
    root = root.resolve()
    report = Report()
    if phase not in {"build", "pre-eval", "final"}:
        report.check(False, ".", "phase", f"unknown phase: {phase}")
        return report
    try:
        additional = release_files(version)
    except ValueError as exc:
        report.check(False, ".", "version", str(exc))
        return report
    if phase != "build":
        required = (*MANIFEST, *(additional if phase == "final" else ()))
        for relative in required:
            report.check((root / relative).is_file(), relative, "required file", "file is missing")
            if relative not in RESULT_FILES:
                report.check((root / relative).is_file() and (root / relative).stat().st_size > 0,
                             relative, "required content", "file is empty or missing")
    paths = {relative for relative in (*MANIFEST, *additional) if (root / relative).is_file()}
    if (root / ".git").exists():
        try:
            paths.update(filter(None, command(["git", "ls-files", "--cached", "-z"], root).split("\0")))
        except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired) as exc:
            report.check(False, ".", "tracked paths", str(exc))
    texts: dict[str, str] = {}
    for relative in sorted(paths):
        if Path(relative).suffix.lower() in BINARY_SUFFIXES:
            continue
        try:
            texts[relative] = read_text(root / relative)
            report.check(True, relative, "UTF-8", "")
        except (OSError, UnicodeError, ValueError) as exc:
            report.check(False, relative, "UTF-8", str(exc))
    skill_path = f"{SKILL_DIR}/SKILL.md"
    skill_text = texts.get(skill_path, "")
    try:
        fields = frontmatter(skill_text)
        name = fields.get("name", "")
        description = fields.get("description", "")
        report.check(name == Path(SKILL_DIR).name, skill_path, "name", "name differs from skill folder")
        report.check(1 <= len(name) <= 64, skill_path, "name length", "expected 1 to 64 characters")
        report.check(bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)), skill_path, "name syntax", "use lowercase letters, digits, and single internal hyphens")
        report.check(set(fields) == {"name", "description", "license"}, skill_path, "frontmatter fields", "exactly name, description, and license are required")
        report.check(fields.get("license") == "MIT", skill_path, "license", "license must be MIT")
        report.check(1 <= len(description) <= 1024, skill_path, "description", "expected 1 to 1024 characters")
    except ValueError as exc:
        report.check(False, skill_path, "frontmatter", str(exc))
    report.check(len(skill_text.splitlines()) <= 500, skill_path, "line count", "exceeds 500 lines")
    context_reference = "references/context-audience-boundary.md"
    report.check(bool(texts.get(f"{SKILL_DIR}/{context_reference}", "").strip()),
                 f"{SKILL_DIR}/{context_reference}", "context reference", "required reference is empty or missing")
    try:
        report.check(context_reference in relative_targets(skill_text), skill_path,
                     "context reference", "missing link to the required context reference")
    except ValueError as exc:
        report.check(False, skill_path, "context reference", str(exc))
    forbidden_files = {"README.md", "INSTALLATION_GUIDE.md", "QUICK_REFERENCE.md", "CHANGELOG.md"}
    extras = sorted(path.relative_to(root).as_posix() for path in (root / SKILL_DIR).rglob("*") if path.name in forbidden_files)
    report.check(not extras, SKILL_DIR, "runtime files", f"unexpected auxiliary files: {extras}")
    yaml_path = f"{SKILL_DIR}/agents/openai.yaml"
    try:
        interface = interface_strings(texts.get(yaml_path, ""))
        report.check(25 <= len(interface["short_description"]) <= 64, yaml_path, "short_description", "expected 25 to 64 characters")
        report.check(f"${SKILL_NAME}" in interface["default_prompt"], yaml_path, "default_prompt", "missing exact skill invocation")
        report.check(bool(interface["display_name"]), yaml_path, "display_name", "must not be empty")
    except ValueError as exc:
        report.check(False, yaml_path, "quoted strings", str(exc))
    cases = []
    try:
        cases = run_evals.load_cases(root)
        report.check(True, "evals", "case schema", "")
    except (OSError, ValueError, UnicodeError) as exc:
        report.check(False, "evals", "case schema", str(exc))
    for relative, text in texts.items():
        if relative.endswith(".md"):
            try:
                for target in relative_targets(text):
                    target_path = root / target.lstrip("/") if target.startswith("/") else (root / relative).parent / target
                    within_repo = target_path.resolve().is_relative_to(root)
                    report.check(within_repo and target_path.is_file(), relative, "relative link", f"missing or external file: {target}")
            except (OSError, ValueError) as exc:
                report.check(False, relative, "relative link", str(exc))
    if phase != "build":
        report.check(texts.get("README.md", "").count(INTRODUCTION) == 1, "README.md", "introduction", "approved sentence must appear exactly once")
        copyright_lines = [line for line in texts.get("LICENSE", "").splitlines() if line.lower().startswith("copyright ")]
        report.check(copyright_lines == ["Copyright (c) 2026 Jiyoung Jung"], "LICENSE", "author", "expected one exact copyright holder")
        for relative, text in texts.items():
            scanned = scan_text(relative, text)
            found = sorted({pattern for pattern in FORBIDDEN_PATTERNS if pattern in scanned})
            private_paths = bool(re.search(r"(?i)[a-z]:[\\/]Users[\\/]", scanned))
            report.check(not found and not private_paths, relative, "public content", f"forbidden patterns: {found}" if found else "private local path")
            authors = re.findall(r"(?im)^\s*[\"']?(?:author|author_name|copyright_holder|저자|작성자)[\"']?\s*:\s*[\"']?([^\n\"'<]+)", scanned)
            for author in authors:
                author = author.strip().rstrip(",")
                report.check(author in {AUTHOR, "정지영"}, relative, "author", "unexpected public author name")
        try:
            if gh_path is None or not gh_path.is_absolute() or not gh_path.is_file():
                raise ValueError("--gh-path must name an existing absolute executable path")
            gh_version = command([str(gh_path), "--version"], root)
            if not re.match(r"^gh version 2\.97\.0(?:\s|$)", gh_version):
                raise ValueError("GitHub CLI 2.97.0 is required")
            report.check(True, str(gh_path), "GitHub CLI version", "")
            expected_owner = None
            endpoint, query = "user", ".login"
            if os.environ.get("GITHUB_ACTIONS") == "true":
                repository = os.environ.get("GITHUB_REPOSITORY", "")
                match = re.fullmatch(r"([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)/([A-Za-z0-9_.-]+)", repository)
                if not match or match[2] in {".", ".."}:
                    raise ValueError("GITHUB_REPOSITORY must contain a valid owner/repository name")
                expected_owner = match[1]
                # The Actions installation token supports repository metadata, not /user.
                endpoint, query = f"repos/{repository}", ".owner.login"
            owner = command([str(gh_path), "api", endpoint, "--jq", query], root).strip()
            if not re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", owner):
                raise ValueError(f"gh api {endpoint} did not return a valid account login")
            if expected_owner is not None and owner.casefold() != expected_owner.casefold():
                raise ValueError("repository owner does not match GITHUB_REPOSITORY")
            public_repository = command(
                [str(gh_path), "api", f"repos/{PUBLIC_REPOSITORY}", "--jq", ".full_name"], root
            ).strip()
            if public_repository.casefold() != PUBLIC_REPOSITORY.casefold():
                raise ValueError("canonical repository identity does not match the public repository")
            public_owner = PUBLIC_REPOSITORY.split("/", 1)[0]
            command([str(gh_path), "skill", "--help"], root)
            report.check(True, str(gh_path), "gh skill", "")
            for relative, text in texts.items():
                mismatches = check_owner(scan_text(relative, text), public_owner)
                report.check(not mismatches, relative, "GitHub owner", f"expected {public_owner}; found {mismatches}")
        except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired) as exc:
            report.check(False, "--gh-path", "GitHub CLI", str(exc))
    if phase == "final":
        try:
            run_evals.verify_tracked(root, version=version)
            report.check(True, "evals", "recorded results", "")
            if cases:
                check_release(root, cases, report, version=version)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            report.check(False, "evals", "recorded results", str(exc))
    if check_staged_manifest:
        check_staged(root, report, version=version)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--phase", choices=("build", "pre-eval", "final"), default="final")
    parser.add_argument("--print-digest", action="store_true")
    parser.add_argument("--check-staged-manifest", action="store_true")
    parser.add_argument("--gh-path", type=Path)
    parser.add_argument("--version", default="v0.1.0", help="Evaluation version to validate for release")
    args = parser.parse_args(argv)
    if args.print_digest:
        try:
            print(run_evals.compute_digest(args.root.resolve()))
            return 0
        except (OSError, ValueError, UnicodeError) as exc:
            print(f"FAIL . [digest]: {exc}", file=sys.stderr)
            return 1
    report = validate_repo(args.root, args.phase, args.gh_path,
                           check_staged_manifest=args.check_staged_manifest, version=args.version)
    if report.errors:
        for error in report.errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"PASS {report.checks} checks ({args.phase})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
