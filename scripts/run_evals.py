"""Prepare and verify file-based evaluations; never invoke or simulate a model."""

import argparse
import ast
import hashlib
import json
import os
import re
import stat
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0.1.0"
OPERATIONS_VERSION = "3"
OUTPUT_CONTRACTS = ("whole-response-v1", "final-answer-v1")
IDENTITY_FIELDS = {"evaluation_identity", "operations_version", "output_contract"}
DEPENDENCY_FIELDS = {"dependency_sha256"}
RESPONSE_FIELDS = {"response_evidence"}
LEGACY_EVIDENCE = "evals/compatibility-v0.1.0.json"
LEGACY_EVIDENCE_SHA256 = "2420CAFA38D421FA1D81488C6186997DFC2199A25CFEF7E7B3373739B63BABE4"
NORMATIVE_SECTIONS = (
    "평가 자료", "사례 형식", "평가 항목", "실행 설정", "판정과 릴리스 조건",
)
PROTOCOL_SECTIONS = (
    "평가 자료", "사례 형식", "평가 항목", "실행 설정", "평가 준비", "실행과 원문 저장",
    "판정과 릴리스 조건", "결과 생성과 검증", "평가 대상 해시", "검증 범위와 한계",
)
CASE_COUNTS = {
    "core.json": 24, "approved-copy.json": 2, "punctuation.json": 7,
    "context.json": 10, "pragmatics.json": 7,
}
CORE_CATEGORIES = {
    "meaning": 4, "grammar": 4, "reference": 3, "register": 3,
    "artifact": 4, "literal": 2, "certainty": 2, "delivery": 2,
}
RUBRIC = (
    "meaning_preservation", "no_unsupported_addition", "audience_fit",
    "natural_korean", "register_consistency", "literal_preservation", "output_format",
)
CASE_FIELDS = {
    "id", "category", "context", "instruction", "input", "must_preserve",
    "must_include", "must_not_add", "review_points", "critical_failures", "applicable_rubric",
}
ROLES = ("generator", "reviewer-a", "reviewer-b", "adjudicator")
SETTINGS = {
    "agent": "codex", "model": "gpt-5.6-sol",
    "reasoning_effort": "high", "sampling": "runtime_default",
}
ROLE_FIELDS = {"role", *SETTINGS, "attempt_log"}
JUDGMENT_FIELDS = {"rubric", "critical_failure", "reason"}
ATTEMPT_FIELDS = {
    "attempt", "context_id", "runtime_surface", "runtime_version", "status", "retry_reason",
}
RECORD_FIELDS = {
    "id", "prompt_sha256", "output", "generator", "reviewers", "adjudicator",
    "final_rubric", "case_pass", "critical_failure", "tested_at", "tested_skill_digest",
}
INTRODUCTION = "원래 의미를 그대로 유지하면서 번역투와 어색한 표현을 글의 목적과 독자에 맞게 다듬을 수 있는 자연스러운 한국어 스킬입니다."
REQUIRED_CASES = {
    "register-honorific-001": ("네 문장이 낫습니다.", None),
    "meaning-close-001": ("기획서 전체의 충돌도 함께 닫는다.", None),
    "approved-introduction-001": (INTRODUCTION, INTRODUCTION),
}
CONTEXT_CASE_IDS = (
    "boundary-drafting-history-001",
    "priority-later-edit-001",
    "register-remote-draft-001",
    "register-neutral-actions-001",
    "preference-no-middle-dot-001",
    "preference-protected-middle-dot-001",
    "boundary-private-measurement-001",
    "artifact-proposal-need-001",
    "artifact-expected-benefit-001",
    "literal-familiar-korean-001",
)
PRAGMATICS_CASE_IDS = (
    "pragmatics-speaker-001",
    "pragmatics-relationship-001",
    "pragmatics-time-001",
    "pragmatics-place-001",
    "pragmatics-channel-001",
    "pragmatics-intent-001",
    "pragmatics-unknown-001",
)
GENERATOR_TEMPLATE = """$natural-korean-writing을 사용하세요.

문맥:
{context}

요청:
{instruction}

원문:
{input}

요청한 결과만 출력하세요.
"""
REVIEWER_TEMPLATE = """다음 출력이 case의 요구 조건을 충족하는지 평가하세요.

보존 조건과 필수 포함 조건은 별도의 정확 표기 지시가 없으면 의미와 사실을 기준으로 판정하세요. 조건을 설명한 문장을 출력의 고정 문구로 취급하지 마세요.

literal_preservation은 코드, 경로, URL, 기술 식별자와 그대로 유지하라고 명시한 문구의 정확한 보존을 판정합니다. 보호 대상 밖에서 의미가 같은 표현이나 조사, 어순이 달라진 것만으로 이 항목을 fail로 판정하지 마세요.

완전 일치 기준이 null이 아니면 출력 전체의 문자, 공백과 문장부호가 그 값과 일치해야 합니다. null이어도 보호할 개별 원문은 정확히 유지해야 합니다.

Case ID: {id}
문맥: {context}
요청: {instruction}
원문: {input}
보존 조건: {must_preserve}
필수 포함 조건: {must_include}
추가 금지 조건: {must_not_add}
검토 기준: {review_points}
핵심 실패 조건: {critical_failures}
완전 일치 기준: {expected_exact_if_present}
적용할 rubric: {applicable_rubric}

실제 출력:
{output}

적용할 rubric 항목마다 pass 또는 fail을 판정하세요. 핵심 실패 여부와 근거를 함께 기록하세요. 문장을 다시 작성하지 마세요.
다음 JSON object 하나만 출력하세요.
{{"id":"{id}","rubric":{{"rubric_name":"pass_or_fail"}},"critical_failure":false,"reason":"판정 근거"}}
"""


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _keys(value, required, optional=()):
    _require(type(value) is dict, "expected a JSON object")
    _require(required <= value.keys() <= required | set(optional), "missing or unknown JSON fields")


def _text(value, label, allow_empty=False):
    _require(type(value) is str, f"{label} must be a string")
    _require(allow_empty or bool(value.strip()), f"{label} must not be empty")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as error:
        raise ValueError(f"{label} is not valid UTF-8 text") from error
    return value


def _read_text(path):
    try:
        result = path.read_bytes().decode("utf-8", errors="strict")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"cannot read UTF-8 file: {path}") from error
    _require(not result.startswith("\ufeff"), f"UTF-8 BOM is not allowed: {path}")
    return result


def _object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def _loads(text):
    try:
        return json.loads(text, object_pairs_hook=_object, parse_constant=_invalid_constant)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError(f"invalid JSON: {error}") from error


def _read_json(path):
    return _loads(_read_text(path))


def _read_jsonl(path):
    return [_loads(line) for line in _read_text(path).splitlines()]


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def _version(version):
    _require(type(version) is str and re.fullmatch(r"v\d+\.\d+\.\d+", version), "invalid version")


def load_cases(root: Path) -> list[dict]:
    """Validate every case and return the order declared by CASE_COUNTS."""
    cases = []
    for filename, count in CASE_COUNTS.items():
        group = _read_json(root / "evals" / filename)
        _require(type(group) is list and len(group) == count, f"{filename} requires {count} cases")
        for case in group:
            _keys(case, CASE_FIELDS, {"expected_exact"})
            for field in ("id", "category", "context", "instruction", "input"):
                _text(case[field], field, allow_empty=field == "input")
            _require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", case["id"]), "invalid case ID")
            for field in (
                "must_preserve", "must_include", "must_not_add", "review_points",
                "critical_failures", "applicable_rubric",
            ):
                _require(type(case[field]) is list, f"{field} must be an array")
                for item in case[field]:
                    _text(item, field)
            applicable = case["applicable_rubric"]
            _require(bool(applicable) and len(applicable) == len(set(applicable)), "duplicate or empty rubric")
            _require(set(applicable) <= set(RUBRIC), "unknown applicable rubric")
            if "expected_exact" in case:
                _text(case["expected_exact"], "expected_exact")
        if filename == "core.json":
            _require(Counter(case["category"] for case in group) == CORE_CATEGORIES, "wrong core distribution")
        else:
            category = filename.removesuffix(".json")
            _require(all(case["category"] == category for case in group), f"wrong {category} category")
            if category == "approved-copy":
                _require(all("expected_exact" in case for case in group), "approved copies require exact text")
            if category == "context":
                _require({case["id"] for case in group} == set(CONTEXT_CASE_IDS),
                         "context cases must contain every required context regression")
            if category == "pragmatics":
                _require({case["id"] for case in group} == set(PRAGMATICS_CASE_IDS),
                         "pragmatics cases must contain every required pragmatics regression")
        cases.extend(group)
    ids = [case["id"] for case in cases]
    _require(len(ids) == len(set(ids)), "duplicate case ID")
    indexed = {case["id"]: case for case in cases}
    for case_id, (source, expected) in REQUIRED_CASES.items():
        _require(case_id in indexed, f"missing required regression: {case_id}")
        case = indexed[case_id]
        _require(case["input"] == source, f"required regression text changed: {case_id}")
        if expected is None:
            _require("expected_exact" not in case, f"free rewriting must not require exact text: {case_id}")
        else:
            _require(case.get("expected_exact") == expected, f"required regression text changed: {case_id}")
    return cases


def compute_digest(root: Path, *, protocol_bytes=None) -> str:
    """Hash specified source bytes in relative POSIX-path UTF-8 byte order."""
    paths = [root / "evals" / name for name in ("README.md", *CASE_COUNTS)]
    runtime = root / "skills" / "natural-korean-writing"
    pending = [runtime]
    try:
        while pending:
            directory = pending.pop()
            info = directory.lstat()
            _require(stat.S_ISDIR(info.st_mode), f"not a runtime directory: {directory}")
            _require(not getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT,
                     f"linked runtime directory: {directory}")
            with os.scandir(directory) as entries:
                for entry in entries:
                    info = entry.stat(follow_symlinks=False)
                    _require(not stat.S_ISLNK(info.st_mode)
                             and not getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT,
                             f"linked runtime input: {entry.path}")
                    if stat.S_ISDIR(info.st_mode):
                        pending.append(Path(entry.path))
                    elif stat.S_ISREG(info.st_mode):
                        paths.append(Path(entry.path))
                    else:
                        raise ValueError(f"unsupported runtime input: {entry.path}")
        _require(any(path.is_relative_to(runtime) for path in paths), "empty runtime tree")
        inputs = [(path.relative_to(root).as_posix().encode("utf-8", errors="strict"), path) for path in paths]
        state = hashlib.sha256()
        for relative, path in sorted(inputs, key=lambda item: item[0]):
            _require(not path.is_symlink(), f"linked digest input: {path}")
            data = (protocol_bytes if protocol_bytes is not None and path == root / "evals" / "README.md"
                    else path.read_bytes())
            for piece in (relative, b"\0", str(len(data)).encode("ascii"), b"\0", data, b"\0"):
                state.update(piece)
        return state.hexdigest().upper()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"cannot calculate source digest: {error}") from error


def render_generator_prompt(case):
    return GENERATOR_TEMPLATE.format(
        context=case["context"], instruction=case["instruction"], input=case["input"]
    )


def render_reviewer_prompt(case, output):
    values = {key: _json(case[key]) for key in (
        "must_preserve", "must_include", "must_not_add", "review_points",
        "critical_failures", "applicable_rubric",
    )}
    values.update(
        id=case["id"], context=case["context"], instruction=case["instruction"],
        input=case["input"], output=output,
        expected_exact_if_present=_json(case.get("expected_exact")),
    )
    return REVIEWER_TEMPLATE.format(**values)


def render_adjudicator_prompt(case, output, reviewer_a, reviewer_b):
    _validate_judgment(reviewer_a, case)
    _validate_judgment(reviewer_b, case)
    return (
        render_reviewer_prompt(case, output)
        + "\n두 평가를 참고하되 같은 기준으로 독립적으로 판정하세요.\n"
        + "Reviewer A:\n" + _json(reviewer_a)
        + "\nReviewer B:\n" + _json(reviewer_b) + "\n"
    )


def capture_response(source_bytes):
    """Capture a complete supported read_thread export, without inventing channels."""
    _require(type(source_bytes) is bytes, "response source must be original bytes")
    source = _loads(source_bytes.decode("utf-8", errors="strict"))
    _require(type(source) is dict and source.get("schemaVersion") == 1,
             "unsupported response export schema")
    turns = source.get("turns")
    _require(type(turns) is list and len(turns) == 1, "capture exactly one complete turn")
    turn = turns[0]
    _require(type(turn) is dict, "invalid response turn")
    _require(turn.get("status") == "completed" and turn.get("error") is None,
             "response turn did not complete")
    _require(not turn.get("truncated", False), "response turn is truncated")
    items = turn.get("items")
    _require(type(items) is list, "response turn has no item list")
    messages = []
    for index, item in enumerate(items):
        _require(type(item) is dict and item.get("type") in {
            "agentMessage", "userMessage", "commandExecution", "reasoning", "contextCompaction",
        }, "unsupported response item type")
        if item.get("type") != "agentMessage":
            continue
        _require(not item.get("truncated", False), "assistant message is truncated")
        messages.append({"index": index, "id": item.get("id"),
                         "phase": item.get("phase"), "text": item.get("text")})
    evidence = {"contract": "final-answer-v1", "source_sha256": _sha(source_bytes),
                "turn_id": turn.get("id"), "messages": messages,
                "messages_sha256": _sha(_json(messages).encode("utf-8"))}
    response_output(evidence)
    return evidence


def response_output(evidence):
    """Select one typed final answer; preserve every commentary message unchanged."""
    _keys(evidence, {"contract", "source_sha256", "turn_id", "messages", "messages_sha256"})
    _require(evidence["contract"] == "final-answer-v1", "unknown response contract")
    _text(evidence["turn_id"], "response turn ID")
    for name in ("source_sha256", "messages_sha256"):
        _require(type(evidence[name]) is str and re.fullmatch(r"[0-9A-F]{64}", evidence[name]),
                 "invalid response source hash")
    messages = evidence["messages"]
    _require(type(messages) is list and messages, "missing assistant messages")
    _require(_sha(_json(messages).encode("utf-8")) == evidence["messages_sha256"],
             "response message bytes changed")
    identifiers, previous, finals = set(), -1, []
    for message in messages:
        _keys(message, {"index", "id", "phase", "text"})
        _require(type(message["index"]) is int and message["index"] > previous,
                 "response message order changed")
        previous = message["index"]
        identifier = _text(message["id"], "response message ID")
        _require(identifier not in identifiers, "duplicate response message ID")
        identifiers.add(identifier)
        _require(message["phase"] in {"commentary", "final_answer"}, "unknown response channel")
        _text(message["text"], "response message text")
        if message["phase"] == "final_answer":
            finals.append(message)
    _require(len(finals) == 1 and finals[0] is messages[-1],
             "response must end with exactly one final answer")
    return finals[0]["text"]


def public_response_evidence(evidence):
    """Keep internal IDs in private source exports; publish opaque SHA256 identifiers."""
    response_output(evidence)
    messages = [{**message, "id": _sha(message["id"].encode("utf-8"))}
                for message in evidence["messages"]]
    return {**evidence, "turn_id": _sha(evidence["turn_id"].encode("utf-8")),
            "messages": messages, "messages_sha256": _sha(_json(messages).encode("utf-8"))}


def _validate_record_responses(record, response_turns=None):
    evidence = record.get("response_evidence")
    if record.get("output_contract", "whole-response-v1") == "whole-response-v1":
        _require(evidence is None, "unexpected channel evidence for whole-response contract")
        return
    roles = {"generator", "reviewer-a", "reviewer-b"}
    if record["adjudicator"] is not None:
        roles.add("adjudicator")
    _keys(evidence, roles)
    response_turns = set() if response_turns is None else response_turns
    for role in sorted(roles):
        response_output(evidence[role])
        turn_id = evidence[role]["turn_id"]
        identifiers = [turn_id, *(message["id"] for message in evidence[role]["messages"])]
        _require(all(re.fullmatch(r"[0-9A-F]{64}", identifier) for identifier in identifiers),
                 "public response identifiers must be hashes")
        _require(turn_id not in response_turns, "response turn reused across cases or roles")
        response_turns.add(turn_id)
    _require(response_output(evidence["generator"]) == record["output"],
             "generator output differs from complete final answer")
    participants = dict(zip(("reviewer-a", "reviewer-b"), record["reviewers"], strict=True))
    if record["adjudicator"] is not None:
        participants["adjudicator"] = record["adjudicator"]
    for role, participant in participants.items():
        expected = {"id": record["id"], **{key: participant[key] for key in JUDGMENT_FIELDS}}
        _require(_loads(response_output(evidence[role])) == expected,
                 "judgment differs from complete final answer")


def _protocol_semantics(text):
    """Only the explicitly classified operational sections may vary."""
    pieces = re.split(r"(?m)^## ([^\r\n]+)\r?\n", text)
    headings = tuple(pieces[1::2])
    _require(headings == PROTOCOL_SECTIONS, "unknown, missing, or reordered evaluation sections")
    sections = dict(zip(headings, pieces[2::2], strict=True))
    templates = {}
    for heading in ("생성용 프롬프트", "평가용 프롬프트"):
        pattern = rf"(?m)^### {heading}\r?\n\r?\n```text\r?\n(.*?)\r?\n```"
        found = re.findall(pattern, text, flags=re.DOTALL)
        _require(len(found) == 1, f"missing or ambiguous documented prompt: {heading}")
        templates[heading] = found[0]
    _require(templates["생성용 프롬프트"] == GENERATOR_TEMPLATE.rstrip("\n"),
             "documented generator prompt differs")
    _require(templates["평가용 프롬프트"] == REVIEWER_TEMPLATE.replace("{{", "{").replace("}}", "}").rstrip("\n"),
             "documented reviewer prompt differs")
    return {"preamble": pieces[0], "normative": {key: sections[key] for key in NORMATIVE_SECTIONS},
            "documented_prompts": templates}


def _semantic_code(source, release_source):
    """Hash executable evaluation rules and their local transitive dependencies."""
    selected = {}
    harness_roots = ["load_cases", "render_generator_prompt", "render_reviewer_prompt",
                     "render_adjudicator_prompt", "_make_record", "SETTINGS", "ROLES",
                     "OUTPUT_CONTRACTS", "capture_response", "public_response_evidence",
                     "_validate_record_responses"]
    for text, pending, prefix in (
        (release_source, ["check_release", "Report"], "validate_repo."),
        (source, harness_roots, ""),
    ):
        nodes = {}
        for node in ast.parse(text).body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                nodes[node.name] = node
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    nodes[alias.asname or alias.name.split(".")[0]] = node
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        nodes[target.id] = node
        while pending:
            name = pending.pop()
            if prefix + name in selected:
                continue
            _require(name in nodes, f"missing evaluation rule: {prefix}{name}")
            node = nodes[name]
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = [node.module] if isinstance(node, ast.ImportFrom) else [alias.name for alias in node.names]
                allowed = {"collections", "hashlib", "json", "pathlib", "re"}
                if prefix:
                    allowed.add("run_evals")
                _require(all(module in allowed for module in modules),
                         f"unclassified evaluation dependency: {prefix}{name}")
            selected[prefix + name] = _sha(ast.dump(node, include_attributes=False).encode("utf-8"))
            for item in ast.walk(node):
                if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and item.id in nodes:
                    pending.append(item.id)
                elif prefix and isinstance(item, ast.Attribute) and isinstance(item.value, ast.Name):
                    if item.value.id == "run_evals":
                        harness_roots.append(item.attr)
    return selected


def _semantic_contract(root, *, protocol_text=None, source=None, release_source=None,
                       output_contract="whole-response-v1"):
    _require(output_contract in OUTPUT_CONTRACTS, "unknown output contract")
    cases = load_cases(root)
    scripts = Path(__file__).resolve().parent
    code = _semantic_code(source if source is not None else _read_text(scripts / "run_evals.py"),
                          release_source if release_source is not None else _read_text(scripts / "validate_repo.py"))
    prompts = {}
    for case in cases:
        vote = {"id": case["id"], "rubric": dict.fromkeys(case["applicable_rubric"], "pass"),
                "critical_failure": False, "reason": "identity dependency sentinel"}
        alternate = {**vote, "critical_failure": True, "reason": "second independent sentinel"}
        prompts[case["id"]] = [
            _sha(prompt.encode("utf-8")) for prompt in (
                render_generator_prompt(case), render_reviewer_prompt(case, "{output}"),
                render_adjudicator_prompt(case, "{output}", vote, alternate),
            )
        ]
    return {
        "schema": 1, "code": code, "settings": SETTINGS, "fork_turns": "none",
        "output_contract": output_contract,
        "protocol": _protocol_semantics(protocol_text if protocol_text is not None
                                          else _read_text(root / "evals" / "README.md")),
        "prompts": prompts,
    }


def compute_evaluation_identity(root, output_contract="whole-response-v1"):
    """Keep raw runtime/case bytes, quality rules, prompts, and settings in identity."""
    contract = _semantic_contract(root, output_contract=output_contract)
    return compute_digest(root, protocol_bytes=_json(contract).encode("utf-8"))


def _legacy_evidence(root, metadata):
    path = root / LEGACY_EVIDENCE
    _require(_sha(path.read_bytes()) == LEGACY_EVIDENCE_SHA256, "legacy compatibility evidence changed")
    evidence = _read_json(path)
    _require(metadata == evidence["metadata"], "unrecognized legacy evaluation metadata")
    original = evidence["original_protocol"].encode("utf-8")
    _require(compute_digest(root, protocol_bytes=original) == metadata["tested_skill_digest"],
             "tested skill digest mismatch against frozen legacy inputs")
    _require(_semantic_contract(root) == evidence["semantic_contract"],
             "legacy evaluation semantics changed or impact is unknown")
    return evidence


def _record_dependencies(case, record):
    judgments = [{"id": case["id"], **{key: vote[key] for key in JUDGMENT_FIELDS}}
                 for vote in record["reviewers"]]
    prompts = {"generator": render_generator_prompt(case)}
    for role in ("reviewer-a", "reviewer-b"):
        prompts[role] = render_reviewer_prompt(case, record["output"])
    if record["adjudicator"] is not None:
        prompts["adjudicator"] = render_adjudicator_prompt(case, record["output"], *judgments)
    return {role: _sha(prompt.encode("utf-8")) for role, prompt in prompts.items()}


def _bound_record_dependencies(case, record):
    original = {key: value for key, value in record.items() if key != "dependency_sha256"}
    return {"prompts": _record_dependencies(case, record),
            "record": _sha(_json(original).encode("utf-8"))}


def _verify_legacy_records(root, metadata, cases, records):
    evidence = _legacy_evidence(root, metadata)
    data = "".join(_json(record) + "\n" for record in records).encode("utf-8")
    _require(_sha(data) == evidence["records_sha256"], "original legacy output or judgment changed")
    actual = {case["id"]: _record_dependencies(case, record) for case, record in zip(cases, records, strict=True)}
    _require(actual == evidence["actual_prompt_sha256"], "legacy prompt dependencies changed")


def new_context_id():
    """Call immediately before creating an agent; record it with that attempt."""
    return str(uuid.uuid4())


def _work_path(root, work_dir):
    return work_dir if work_dir.is_absolute() else root / work_dir


def _write(path, text, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8", errors="strict", newline="\n") as stream:
        stream.write(text)


def prepare(root: Path, version=VERSION, work_dir=Path(".eval-work"), *,
            output_contract="whole-response-v1"):
    _version(version)
    cases = load_cases(root)
    source_digest = compute_digest(root)
    work = _work_path(root, work_dir)
    _require(not work.exists(), f"evaluation work directory already exists: {work}")
    metadata = {
        "version": version,
        "tested_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "tested_skill_digest": source_digest,
        "evaluation_identity": compute_evaluation_identity(root, output_contract),
        "operations_version": OPERATIONS_VERSION,
        "output_contract": output_contract,
        "source_protocol": _read_text(root / "evals" / "README.md"),
    }
    work.mkdir(parents=True, exist_ok=False)
    _write(work / "run.json", _json(metadata) + "\n", exclusive=True)
    _write(work / "execution.jsonl", "", exclusive=True)
    for role in ROLES:
        (work / role).mkdir()
        if output_contract == "final-answer-v1":
            (work / "responses" / role).mkdir(parents=True)
            (work / "sources" / role).mkdir(parents=True)
    for case in cases:
        _write(work / "prompts" / "generator" / f"{case['id']}.txt",
               render_generator_prompt(case), exclusive=True)
        for role in ("reviewer-a", "reviewer-b"):
            _write(work / "prompts" / role / f"{case['id']}.txt",
                   render_reviewer_prompt(case, "{output}"), exclusive=True)
    return metadata


def _timestamp(value):
    _text(value, "tested_at")
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("tested_at must be an ISO UTC timestamp") from error
    _require(moment.tzinfo is not None and moment.utcoffset().total_seconds() == 0,
             "tested_at must be an ISO UTC timestamp")


def _metadata(root, metadata, version):
    _keys(metadata, {"version", "tested_at", "tested_skill_digest"}, IDENTITY_FIELDS | {"source_protocol"})
    _require(metadata["version"] == version, "run version mismatch")
    _timestamp(metadata["tested_at"])
    _require(bool(IDENTITY_FIELDS & metadata.keys()) == (IDENTITY_FIELDS <= metadata.keys()),
             "incomplete evaluation identity metadata")
    _require(("source_protocol" in metadata) == ("evaluation_identity" in metadata),
             "missing or unexpected source protocol snapshot")
    _text(metadata["tested_skill_digest"], "tested_skill_digest")
    _require(re.fullmatch(r"[0-9A-F]{64}", metadata["tested_skill_digest"]), "invalid raw source digest")
    if "evaluation_identity" in metadata:
        _require(type(metadata["operations_version"]) is str and metadata["operations_version"] == OPERATIONS_VERSION,
                 "unknown operations version")
        _require(metadata["output_contract"] in OUTPUT_CONTRACTS, "unknown output contract")
        _text(metadata["source_protocol"], "source_protocol")
        _text(metadata["evaluation_identity"], "evaluation_identity")
        _require(compute_digest(root, protocol_bytes=metadata["source_protocol"].encode("utf-8"))
                 == metadata["tested_skill_digest"], "tested skill digest mismatch against source snapshot")
        _require(_protocol_semantics(metadata["source_protocol"])
                 == _protocol_semantics(_read_text(root / "evals" / "README.md")),
                 "source snapshot evaluation semantics changed")
        _require(metadata["evaluation_identity"] == compute_evaluation_identity(root, metadata["output_contract"]),
                 "tested skill digest mismatch: evaluation identity changed")
    else:
        _legacy_evidence(root, metadata)


def _validate_envelope(envelope, case_id, role, contexts):
    _keys(envelope, {"id", *ROLE_FIELDS})
    _require(envelope["id"] == case_id and envelope["role"] == role, "execution case or role mismatch")
    _require(role in ROLES, "unknown execution role")
    for key, expected in SETTINGS.items():
        _require(envelope[key] == expected, f"incorrect execution setting: {key}")
    attempts = envelope["attempt_log"]
    _require(type(attempts) is list and 1 <= len(attempts) <= 2, "only one output-free error retry is allowed")
    for index, attempt in enumerate(attempts, 1):
        _keys(attempt, ATTEMPT_FIELDS)
        _require(type(attempt["attempt"]) is int and attempt["attempt"] == index, "invalid attempt order")
        _require(attempt["runtime_surface"] == "codex-desktop", "incorrect runtime surface")
        version = _text(attempt["runtime_version"], "runtime_version")
        _require(version.strip() == version and "\n" not in version and "\r" not in version
                 and version.lower() not in {"...", "unknown", "unavailable", "n/a", "runtime_default"},
                 "runtime_version must identify the observed runtime")
        context_id = _text(attempt["context_id"], "context_id")
        try:
            identity = uuid.UUID(context_id)
        except ValueError as error:
            raise ValueError("context_id must be a UUID") from error
        _require(identity not in contexts, "context_id reused across cases, roles, or attempts")
        contexts.add(identity)
        if index == len(attempts):
            _require(attempt["status"] == "completed" and attempt["retry_reason"] is None,
                     "final attempt must complete without a retry reason")
        else:
            _require(attempt["status"] in {"delivery_error", "runtime_error", "transport_error"},
                     "only output-free delivery or runtime errors may retry")
            _text(attempt["retry_reason"], "retry reason")
    return {key: envelope[key] for key in ROLE_FIELDS}


def _validate_rubric(value, case):
    _keys(value, set(case["applicable_rubric"]))
    _require(all(type(item) is str and item in {"pass", "fail"} for item in value.values()),
             "rubric values must be pass or fail")


def _validate_judgment(judgment, case):
    _keys(judgment, {"id", *JUDGMENT_FIELDS})
    _require(judgment["id"] == case["id"], "reviewer case ID mismatch")
    _validate_rubric(judgment["rubric"], case)
    _require(type(judgment["critical_failure"]) is bool, "critical_failure must be boolean")
    _text(judgment["reason"], "reviewer reason")
    return {key: judgment[key] for key in JUDGMENT_FIELDS}


def _disagree(first, second):
    return (first["rubric"] != second["rubric"]
            or first["critical_failure"] != second["critical_failure"])


def _make_record(case, output, generator, reviewers, adjudicator, metadata):
    _text(output, "generator output")
    _require(len(reviewers) == 2, "exactly two reviewers are required")
    disagreement = _disagree(*reviewers)
    _require((adjudicator is not None) == disagreement, "adjudicator must exist only for disagreement")
    votes = reviewers + ([adjudicator] if adjudicator is not None else [])
    final = {
        key: "pass" if sum(vote["rubric"][key] == "pass" for vote in votes) >= 2 else "fail"
        for key in case["applicable_rubric"]
    }
    critical = sum(vote["critical_failure"] for vote in votes) >= 2
    return {
        "id": case["id"], "prompt_sha256": _sha(render_generator_prompt(case).encode("utf-8")),
        "output": output, "generator": generator, "reviewers": reviewers, "adjudicator": adjudicator,
        "final_rubric": final, "case_pass": all(value == "pass" for value in final.values()) and not critical,
        "critical_failure": critical, "tested_at": metadata["tested_at"],
        "tested_skill_digest": metadata["tested_skill_digest"],
    }


def _exact_files(directory, expected):
    try:
        entries = list(directory.iterdir())
    except OSError as error:
        raise ValueError(f"missing input directory: {directory}") from error
    _require(all(path.is_file() and not path.is_symlink() for path in entries),
             f"unexpected input type: {directory}")
    _require({path.name for path in entries} == set(expected), f"missing or extra files: {directory}")


def _collect(root, version, work_dir):
    _version(version)
    cases = load_cases(root)
    work = _work_path(root, work_dir)
    metadata = _read_json(work / "run.json")
    _metadata(root, metadata, version)
    text_names = [f"{case['id']}.txt" for case in cases]
    json_names = [f"{case['id']}.json" for case in cases]
    for role in ("generator", "reviewer-a", "reviewer-b"):
        _exact_files(work / "prompts" / role, text_names)
        _exact_files(work / role, text_names if role == "generator" else json_names)
    envelopes = {}
    contexts, response_turns = set(), set()
    case_ids = {case["id"] for case in cases}
    for envelope in _read_jsonl(work / "execution.jsonl"):
        _keys(envelope, {"id", *ROLE_FIELDS})
        case_id, role = envelope["id"], envelope["role"]
        _require(type(case_id) is str and case_id in case_ids, "unknown execution case")
        _require(type(role) is str and role in ROLES, "unknown execution role")
        key = (case_id, role)
        _require(key not in envelopes, "duplicate execution envelope")
        envelopes[key] = _validate_envelope(envelope, case_id, role, contexts)
    records, required_envelopes, adjudicator_names = [], set(), []
    for case in cases:
        case_id = case["id"]
        _require(_read_text(work / "prompts" / "generator" / f"{case_id}.txt")
                 == render_generator_prompt(case), "prepared generator prompt changed")
        output = _read_text(work / "generator" / f"{case_id}.txt")
        participants = {}
        for role in ("generator", "reviewer-a", "reviewer-b"):
            key = (case_id, role)
            required_envelopes.add(key)
            _require(key in envelopes, f"missing execution envelope: {key}")
            participant = dict(envelopes[key])
            if role != "generator":
                _require(_read_text(work / "prompts" / role / f"{case_id}.txt")
                         == render_reviewer_prompt(case, "{output}"), "prepared reviewer prompt changed")
                participant.update(_validate_judgment(_read_json(work / role / f"{case_id}.json"), case))
            participants[role] = participant
        reviewers = [participants["reviewer-a"], participants["reviewer-b"]]
        adjudicator = None
        if _disagree(*reviewers):
            key = (case_id, "adjudicator")
            required_envelopes.add(key)
            _require(key in envelopes, f"missing adjudicator execution: {case_id}")
            adjudicator = dict(envelopes[key])
            adjudicator.update(_validate_judgment(
                _read_json(work / "adjudicator" / f"{case_id}.json"), case
            ))
            adjudicator_names.append(f"{case_id}.json")
        record = _make_record(case, output, participants["generator"], reviewers, adjudicator, metadata)
        record.update({key: metadata[key] for key in IDENTITY_FIELDS if key in metadata})
        if metadata.get("output_contract") == "final-answer-v1":
            used_roles = ["generator", "reviewer-a", "reviewer-b"]
            if adjudicator is not None:
                used_roles.append("adjudicator")
            record["response_evidence"] = {
                role: _read_json(work / "responses" / role / f"{case_id}.json") for role in used_roles
            }
            for role in used_roles:
                original = capture_response((work / "sources" / role / f"{case_id}.json").read_bytes())
                _require(original == record["response_evidence"][role],
                         "response evidence differs from preserved source")
                record["response_evidence"][role] = public_response_evidence(original)
        _validate_record_responses(record, response_turns)
        if "evaluation_identity" in metadata:
            record["dependency_sha256"] = _bound_record_dependencies(case, record)
        records.append(record)
    _exact_files(work / "adjudicator", adjudicator_names)
    if metadata.get("output_contract") == "final-answer-v1":
        for role in ("generator", "reviewer-a", "reviewer-b"):
            _exact_files(work / "responses" / role, json_names)
            _exact_files(work / "sources" / role, json_names)
        _exact_files(work / "responses" / "adjudicator", adjudicator_names)
        _exact_files(work / "sources" / "adjudicator", adjudicator_names)
    _require(set(envelopes) == required_envelopes, "missing or unused execution envelopes")
    if "evaluation_identity" not in metadata:
        _verify_legacy_records(root, metadata, cases, records)
    return cases, records, metadata


def _markdown(value):
    return str(value).replace("|", r"\|").replace("\n", " ")


def _summary(cases, records, metadata):
    version = metadata["version"]
    lines = [
        f"# {version} 평가 결과", "",
        f"평가 시작: {metadata['tested_at']}", "",
        f"평가 대상 SHA256: {metadata['tested_skill_digest']}", "",
        "GitHub CLI: 2.97.0", "", "## 실행 환경", "",
        "| 역할 | 에이전트 | 모델 | 추론 설정 | 샘플링 | 실행 환경 | 버전 | 실행 횟수 | 재시도 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for role in ROLES:
        participants = []
        for record in records:
            candidates = [record["generator"], *record["reviewers"]]
            if record["adjudicator"] is not None:
                candidates.append(record["adjudicator"])
            participants.extend(item for item in candidates if item["role"] == role)
        attempts = [attempt for item in participants for attempt in item["attempt_log"]]
        versions = ", ".join(sorted({attempt["runtime_version"] for attempt in attempts})) or "해당 없음"
        cells = [role, *SETTINGS.values(), "codex-desktop" if attempts else "해당 없음",
                 versions, len(attempts), sum(len(item["attempt_log"]) - 1 for item in participants)]
        lines.append("| " + " | ".join(_markdown(cell) for cell in cells) + " |")
    contract = metadata.get("output_contract", "whole-response-v1")
    lines += ["", f"출력 계약: `{contract}`", ""]
    if contract == "final-answer-v1":
        commentary_count = sum(
            message["phase"] == "commentary" for record in records
            for evidence in record["response_evidence"].values() for message in evidence["messages"]
        )
        lines += ["실제 final_answer 전체를 평가했습니다. 진행 안내는 원문과 채널을 별도 보존했습니다.",
                  f"보존한 진행 안내: {commentary_count}개 메시지. 전체 응답에 안내가 없었다는 결과는 아닙니다.",
                  "수집할 때 비공개 원본과 전체 메시지를 대조했습니다. 공개 재검증은 저장된 근거와 최종 출력의 연결을 확인하며 원본 내보내기의 완전성을 다시 보증하지 않습니다.", ""]
    lines += ["## 결과", "", "| 평가 묶음 | 전체 | 통과 | 실패 |", "| --- | --- | --- | --- |"]
    for filename in CASE_COUNTS:
        group = filename.removesuffix(".json")
        selected = [
            record for case, record in zip(cases, records, strict=True)
            if ("core" if case["category"] in CORE_CATEGORIES else case["category"]) == group
        ]
        passed = sum(record["case_pass"] for record in selected)
        lines.append(f"| {group} | {len(selected)} | {passed} | {len(selected) - passed} |")
    passed = sum(record["case_pass"] for record in records)
    disagreements = sum(record["adjudicator"] is not None for record in records)
    critical = sum(record["critical_failure"] for record in records)
    lines += [
        f"| 전체 | {len(records)} | {passed} | {len(records) - passed} |", "",
        f"평가자 간 판정 불일치: {disagreements}개 사례", "",
        f"추가 평가자 판정: {disagreements}개 사례", "",
        f"핵심 실패: {critical}개 사례", "",
        "## 한계", "",
        "모델 출력과 판정은 별도로 수집한 뒤 집계했습니다. 이 도구가 모델 평가를 자동 실행한 결과는 아닙니다.",
        "평가는 기록된 모델과 설정에서 사례마다 한 번 생성한 출력에 한정되며 다른 모델의 품질을 뜻하지 않습니다.",
        "집계 도구는 저장된 실행 정보와 판정의 일관성을 검사하며 실제 실행 여부를 외부 시스템과 대조하지 않습니다.",
        "사례 통과 여부는 다수결 판정입니다. 완전 일치 기준과 배포 조건은 최종 검증 도구에서 별도로 검사합니다.",
        "", "## 재현", "",
        f"    python -X utf8 scripts/run_evals.py prepare --version {version} --work-dir .eval-work --output-contract {contract}", "",
        "이전 대화가 없는 새 실행에서 출력과 판정을 수집하고 실행 정보를 기록한 뒤 다음 명령을 실행합니다.", "",
        f"    python -X utf8 scripts/run_evals.py aggregate --version {version} --work-dir .eval-work",
        f"    python -X utf8 scripts/run_evals.py check --version {version} --work-dir .eval-work",
        f"    python -X utf8 scripts/run_evals.py verify-tracked --version {version}", "",
    ]
    return "\n".join(lines)


def _outputs(root, version, cases, records, metadata):
    outputs = {
        root / "evals" / "runs" / f"{version}.jsonl": "".join(_json(record) + "\n" for record in records),
        root / "evals" / f"results-{version}.md": _summary(cases, records, metadata),
    }
    if "evaluation_identity" in metadata:
        outputs[root / "evals" / "runs" / f"{version}.inputs.json"] = _json(metadata) + "\n"
    return outputs


def aggregate(root: Path, version=VERSION, work_dir=Path(".eval-work")):
    cases, records, metadata = _collect(root, version, work_dir)
    outputs = _outputs(root, version, cases, records, metadata)
    for path, text in outputs.items():
        if path.exists() and path.stat().st_size:
            _require(path.read_bytes() == text.encode("utf-8"), f"refusing to replace existing results: {path}")
    for path, text in outputs.items():
        _write(path, text)
    return records


def check(root: Path, version=VERSION, work_dir=Path(".eval-work")):
    cases, records, metadata = _collect(root, version, work_dir)
    _compare_outputs(_outputs(root, version, cases, records, metadata))


def _compare_outputs(outputs):
    for path, text in outputs.items():
        try:
            actual = path.read_bytes()
        except OSError as error:
            raise ValueError(f"missing tracked result: {path}") from error
        _require(actual == text.encode("utf-8", errors="strict"), f"tracked result differs: {path}")


def verify_tracked(root: Path, version=VERSION):
    """Verify recorded evidence, including failed cases; release gates belong to the validator."""
    _version(version)
    cases = load_cases(root)
    records = _read_jsonl(root / "evals" / "runs" / f"{version}.jsonl")
    _require(len(records) == len(cases), "tracked case count mismatch")
    contexts, response_turns, rebuilt = set(), set(), []
    metadata = None
    for case, record in zip(cases, records, strict=True):
        _keys(record, RECORD_FIELDS, IDENTITY_FIELDS | DEPENDENCY_FIELDS | RESPONSE_FIELDS)
        _require(record["id"] == case["id"], "tracked case ID or order mismatch")
        current = {"version": version, "tested_at": record["tested_at"],
                   "tested_skill_digest": record["tested_skill_digest"]}
        current.update({key: record[key] for key in IDENTITY_FIELDS if key in record})
        if metadata is None:
            metadata = (_read_json(root / "evals" / "runs" / f"{version}.inputs.json")
                        if "evaluation_identity" in current else current)
            _metadata(root, metadata, version)
        _require(current == {key: value for key, value in metadata.items() if key != "source_protocol"},
                 "mixed evaluation metadata")
        _text(record["output"], "generator output")
        _require(type(record["case_pass"]) is bool and type(record["critical_failure"]) is bool,
                 "final decisions must be boolean")
        _validate_rubric(record["final_rubric"], case)

        def participant(value, role, case=case):
            expected = ROLE_FIELDS | (JUDGMENT_FIELDS if role != "generator" else set())
            _keys(value, expected)
            result = _validate_envelope(
                {"id": case["id"], **{key: value[key] for key in ROLE_FIELDS}},
                case["id"], role, contexts,
            )
            if role != "generator":
                result.update(_validate_judgment(
                    {"id": case["id"], **{key: value[key] for key in JUDGMENT_FIELDS}}, case
                ))
            return result

        generator = participant(record["generator"], "generator")
        _require(type(record["reviewers"]) is list and len(record["reviewers"]) == 2, "invalid reviewers")
        reviewers = [participant(value, role) for value, role in
                     zip(record["reviewers"], ("reviewer-a", "reviewer-b"), strict=True)]
        adjudicator = participant(record["adjudicator"], "adjudicator") if record["adjudicator"] is not None else None
        expected = _make_record(case, record["output"], generator, reviewers, adjudicator, metadata)
        expected.update({key: metadata[key] for key in IDENTITY_FIELDS if key in metadata})
        if metadata.get("output_contract") == "final-answer-v1":
            expected["response_evidence"] = record.get("response_evidence")
        _validate_record_responses(expected, response_turns)
        if "evaluation_identity" in metadata:
            expected["dependency_sha256"] = _bound_record_dependencies(case, expected)
        _require(record == expected, f"recorded prompt hash or final judgment differs: {case['id']}")
        rebuilt.append(expected)
    if "evaluation_identity" not in metadata:
        _verify_legacy_records(root, metadata, cases, rebuilt)
    _compare_outputs(_outputs(root, version, cases, rebuilt, metadata))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "aggregate", "check", "verify-tracked"):
        child = commands.add_parser(command)
        child.add_argument("--version", default=VERSION)
        if command != "verify-tracked":
            child.add_argument("--work-dir", type=Path, default=Path(".eval-work"))
        if command == "prepare":
            child.add_argument("--output-contract", choices=OUTPUT_CONTRACTS, default="whole-response-v1")
    capture = commands.add_parser("capture-response")
    capture.add_argument("--source", type=Path, required=True)
    capture.add_argument("--evidence", type=Path, required=True)
    capture.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "capture-response":
            evidence = capture_response(args.source.read_bytes())
            _require(not args.evidence.exists() and not args.output.exists(), "capture destination exists")
            _write(args.evidence, _json(evidence) + "\n", exclusive=True)
            _write(args.output, response_output(evidence), exclusive=True)
        elif args.command == "prepare":
            prepare(args.root, args.version, args.work_dir, output_contract=args.output_contract)
        elif args.command == "verify-tracked":
            verify_tracked(args.root, args.version)
        else:
            operation = {"prepare": prepare, "aggregate": aggregate, "check": check}[args.command]
            operation(args.root, args.version, args.work_dir)
    except (ValueError, OSError) as error:
        print(f"run_evals: {error}", file=sys.stderr)
        return 1
    print(f"{args.command}: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
