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
PROFILE_ROUTES = {
    "conversation": "1. Conversation",
    "technical": "2. Technical explanation",
    **ROUTES,
    "learning": "7. Learning material",
    "proposal": "8. Proposal or service introduction",
}
DOCUMENT = "Shared document drafting checks"
LAYOUT = "Korean document and PDF layout"
SPLIT_FILES = {
    DOCUMENT: "references/document-drafting-checks.md",
    LAYOUT: "references/document-layout.md",
    "1. Conversation": "references/profile-conversation.md",
    "2. Technical explanation": "references/profile-technical.md",
    "3. GitHub PR, issue, review, or comment": "references/profile-github.md",
    "4. UI label and guidance": "references/profile-ui.md",
    "5. External email": "references/profile-email.md",
    "6. Portfolio or resume": "references/profile-application.md",
    "7. Learning material": "references/profile-learning.md",
    "8. Proposal or service introduction": "references/profile-proposal.md",
}
BASELINE = "2419612d3deebf1913ca596af400955cb5d53846"
REVIEWED = "42d1c2653b3d97dd3d5fccabdf4e4f2462082b40"
BEFORE_SPLIT = "817e1667cb5c0cd1c8c171bc42c234fdff6a6165"
SCENARIOS = {
    "mixed_email_proposal_document": {"routes": ("email", "proposal"), "document": True},
    "document_evidence": {"routes": (), "document": True},
    "application_template": {"routes": ("application",), "document": True, "layout": True},
}


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


def selected_units(routes, *, document=False, layout=False):
    """Choose whole profile units while counting shared units only once."""
    units = []
    for route in routes:
        if route not in PROFILE_ROUTES:
            raise ValueError("Unknown artifact route: " + route)
        units.append(PROFILE_ROUTES[route])
    if document:
        units.append(DOCUMENT)
    if layout:
        units.append(LAYOUT)
    return tuple(dict.fromkeys(units))


def measure_path(reader, routes, *, whole_profiles=False, split_profiles=False,
                 document=False, layout=False):
    """Sum declared UTF-8 reading units, not a model's observed read trace."""
    routes = tuple(routes)
    units = selected_units(routes, document=document, layout=layout)
    files = list(CORE)
    if split_profiles:
        if units:
            files.append(PROFILES)
            files.extend(SPLIT_FILES[heading] for heading in units)
        selected = b""
    elif units:
        profiles = checked_utf8(reader(SKILL + PROFILES))
        if whole_profiles:
            selected = profiles
        else:
            intro, sections = profile_parts(profiles)
            missing = [heading for heading in units if heading not in sections]
            if missing:
                raise ValueError("Missing profile heading: " + ", ".join(missing))
            selected = intro + b"".join(sections[heading] for heading in units)
    else:
        selected = b""
    if "application" in routes:
        files.append(WORKFLOW)
    total = len(selected)
    for path in dict.fromkeys(files):
        content = checked_utf8(reader(SKILL + path))
        if not content.strip():
            raise ValueError("Empty reading file: " + path)
        total += len(content)
    return total


def measure(reader, *, whole_profiles=False, split_profiles=False):
    """Model plain drafting paths; optional document/layout work is excluded."""
    result = {"core": measure_path(reader, ())}
    for route in ROUTES:
        result[route] = measure_path(reader, (route,), whole_profiles=whole_profiles,
                                     split_profiles=split_profiles)
    return result


def measure_scenarios(reader, *, whole_profiles=False, split_profiles=False):
    return {
        name: measure_path(reader, **scenario, whole_profiles=whole_profiles,
                           split_profiles=split_profiles)
        for name, scenario in SCENARIOS.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    def at_commit(commit):
        return lambda path: subprocess.check_output(
            ["git", "show", commit + ":" + path], cwd=args.root)

    try:
        working = lambda path: (args.root / path).read_bytes()
        before_split = at_commit(BEFORE_SPLIT)
        result = {
            "unit": "utf8_bytes",
            "scope": "Plain drafting only; no extra editing, language, document, or layout references. "
                     "Application includes profile 6 with all children and the entire workflow. "
                     "No model execution, token, speed, or quality measurement. "
                     "Whole-profile alternatives model hosts requiring every selected file in full. "
                     "Current split paths always read the whole index and selected files. "
                     "Extended scenarios explicitly add document evidence or layout units and "
                     "count each shared unit once; they still exclude editing and language analysis.",
            "baseline_commit": BASELINE,
            "reviewed_commit": REVIEWED,
            "before_split_commit": BEFORE_SPLIT,
            "baseline": measure(at_commit(BASELINE)),
            "reviewed": measure(at_commit(REVIEWED), whole_profiles=True),
            "before_split": measure(before_split),
            "before_split_whole_profiles": measure(before_split, whole_profiles=True),
            "working": measure(working, split_profiles=True),
            "baseline_whole_profiles": measure(at_commit(BASELINE), whole_profiles=True),
            "working_whole_profiles": measure(
                working, whole_profiles=True, split_profiles=True),
            "extended_paths": {
                "before_split": measure_scenarios(before_split),
                "before_split_whole_profiles": measure_scenarios(before_split, whole_profiles=True),
                "working": measure_scenarios(working, split_profiles=True),
                "working_whole_profiles": measure_scenarios(
                    working, whole_profiles=True, split_profiles=True),
            },
        }
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
