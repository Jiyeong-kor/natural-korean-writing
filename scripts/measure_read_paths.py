"""Measure explicit reading paths in UTF-8 bytes, not tokens or agent compliance."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = "skills/natural-korean-writing/"
CORE = ("SKILL.md", "references/context-audience-boundary.md",
        "references/korean-punctuation-rules.md")
PROFILES = "references/artifact-style-profiles.md"
WORKFLOW = "references/application-answer-workflow.md"
ROUTES = {"email": "5. External email", "ui": "4. UI label and guidance",
          "github": "3. GitHub PR, issue, review, or comment",
          "application": "6. Portfolio or resume"}
BASELINE = "2419612d3deebf1913ca596af400955cb5d53846"
REVIEWED = "42d1c2653b3d97dd3d5fccabdf4e4f2462082b40"


def checked_utf8(data):
    data.decode("utf-8", errors="strict")
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is not allowed")
    return data


def profile_parts(data):
    """Preserve the introduction and complete H2 sections, including H3 children."""
    checked_utf8(data)
    headings, offset, fence = [], 0, None
    for line in data.splitlines(keepends=True):
        marker = re.match(rb"^ {0,3}(`{3,}|~{3,})([^\r\n]*)", line)
        if fence:
            if (marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1]
                    and not marker[2].strip()):
                fence = None
        elif marker:
            fence = (marker[1][0], len(marker[1]))
        else:
            heading = re.fullmatch(rb"## ([^\r\n]+)(?:\r?\n)?", line)
            if heading:
                headings.append((offset, heading[1].decode("utf-8", errors="strict")))
        offset += len(line)
    if not headings:
        raise ValueError("No profile sections found")
    sections = {}
    for index, (start, name) in enumerate(headings):
        if name in sections:
            raise ValueError("Duplicate profile heading: " + name)
        end = headings[index + 1][0] if index + 1 < len(headings) else len(data)
        sections[name] = data[start:end]
    return data[:headings[0][0]], sections


def selected_profile(data, heading):
    intro, sections = profile_parts(data)
    if heading not in sections:
        raise ValueError("Missing profile heading: " + heading)
    return intro + sections[heading]


def measure(reader, *, whole_profiles=False):
    """Model plain drafting paths; extra document/layout/language work is excluded."""
    core = sum(len(checked_utf8(reader(SKILL + path))) for path in CORE)
    profiles = checked_utf8(reader(SKILL + PROFILES))
    result = {"core": core}
    for route, heading in ROUTES.items():
        selected = profiles if whole_profiles else selected_profile(profiles, heading)
        total = core + len(selected)
        if route == "application":
            total += len(checked_utf8(reader(SKILL + WORKFLOW)))
        result[route] = total
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    def at_commit(commit):
        return lambda path: subprocess.check_output(
            ["git", "show", commit + ":" + path], cwd=args.root)

    try:
        result = {
            "unit": "utf8_bytes",
            "scope": "Plain drafting only; no extra editing, language, document, or layout references. "
                     "Application includes profile 6 with all children and the entire workflow. "
                     "No model execution, token, speed, or quality measurement. "
                     "Whole-profile alternatives model hosts requiring every selected file in full.",
            "baseline_commit": BASELINE,
            "reviewed_commit": REVIEWED,
            "baseline": measure(at_commit(BASELINE)),
            "reviewed": measure(at_commit(REVIEWED), whole_profiles=True),
            "working": measure(lambda path: (args.root / path).read_bytes()),
            "baseline_whole_profiles": measure(at_commit(BASELINE), whole_profiles=True),
            "working_whole_profiles": measure(
                lambda path: (args.root / path).read_bytes(), whole_profiles=True),
        }
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
