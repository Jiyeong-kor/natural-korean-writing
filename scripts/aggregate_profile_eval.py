"""Validate a separate profile's attested role receipts; never execute models."""
import argparse
import json
from pathlib import Path
import sys
import subprocess
import uuid
import prepare_profile_eval as prep
import run_evals as baseline


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def receipt(work, reference):
    path = (work / reference["path"]).resolve()
    require(path.is_relative_to(work.resolve()), "receipt outside candidate directory")
    require(not (work / reference["path"]).is_symlink(), "symlink receipt")
    data = path.read_bytes()
    require(prep.sha(data) == reference["sha256"], "receipt digest mismatch")
    return json.loads(data.decode("utf-8"))


def validate_candidate(work):
    meta = read(work / "candidate.json")
    contract = meta["contract"]
    require(prep.sha(prep.encoded(contract)) == meta["evaluation_identity"], "candidate identity mismatch")
    require(contract["profile"] == read(prep.PROFILE), "profile changed")
    required = {"scripts/run_evals.py", "scripts/validate_repo.py"}
    required.update("evals/" + name for name in baseline.CASE_COUNTS)
    required.update(p.relative_to(prep.ROOT).as_posix() for p in (prep.ROOT / "skills/natural-korean-writing").rglob("*") if p.is_file())
    require(set(contract["inputs"]) == required, "candidate inputs missing or extra")
    for name, digest in contract["inputs"].items():
        original = subprocess.check_output(["git", "show", contract["profile"]["source_commit"] + ":" + name], cwd=prep.ROOT)
        require(prep.sha(original) == digest, "candidate differs from pinned input")
        require(prep.sha((prep.ROOT / name).read_bytes()) == digest, "evaluated input changed: " + name)
    for name, key in (("evals/profiles/README.md", "profile_protocol_sha256"),
                      ("scripts/prepare_profile_eval.py", "preparation_tool_sha256"),
                      ("scripts/aggregate_profile_eval.py", "aggregation_tool_sha256")):
        require(prep.sha((prep.ROOT / name).read_bytes()) == contract.get(key), "candidate tool/protocol changed: " + name)
    require(meta["baseline_identity"] == baseline.compute_evaluation_identity(prep.ROOT), "baseline identity changed")
    require(meta["status"] == "prepared_not_started", "preparation metadata was rewritten")
    return meta


def validate_role(work, event, case, profile, identity, contexts, agents, expected_prompt):
    require(event["evaluation_identity"] == identity, "role identity mismatch")
    require(event["attempt"] == 1, "only first completed attempt supported; recovery requires separate review")
    context = event["context_id"]
    require(str(uuid.UUID(context)) == context, "invalid context UUID")
    require(context not in contexts, "duplicate context ID")
    require(event["agent_id"] not in agents and bool(event["agent_id"]), "duplicate or empty agent ID")
    contexts.add(context)
    agents.add(event["agent_id"])
    require(event["prompt"] == expected_prompt, "prompt mismatch or leaked context")
    require(bool(event["output"]) and isinstance(event["output"], str), "missing raw output")
    att = receipt(work, event["provider_attestation"])
    require(att["source"] == "provider", "self-reported runtime is not provider evidence")
    for key in ("model", "reasoning_effort", "runtime_surface", "sampling", "fork_turns"):
        require(att[key] == profile[key], "attested runtime mismatch: " + key)
    require(bool(att["runtime_version"]), "missing actual runtime version/explicit unversioned provider value")
    for key in ("context_id", "agent_id", "case_id", "role"):
        require(att[key] == event[key], "attestation binding mismatch: " + key)
    require(att["first_completed_output"] is True and att["fresh_context"] is True, "first independent output not attested")
    require(att["evaluation_identity"] == identity, "attestation identity mismatch")
    require(att["prompt_sha256"] == prep.sha(expected_prompt.encode("utf-8")), "attested prompt mismatch")
    require(att["output_sha256"] == prep.sha(event["output"].encode("utf-8")), "attested output mismatch")
    # Independently inspect original request/response, not an agent's claim.
    request = receipt(work, event["spawn_request"])
    response = receipt(work, event["spawn_response"])
    for key in ("model", "reasoning_effort", "fork_turns"):
        require(request[key] == profile[key], "dispatch mismatch: " + key)
    require(request["prompt"] == expected_prompt, "dispatch prompt mismatch")
    require(response["agent_id"] == event["agent_id"], "dispatch agent mismatch")
    if event["role"] == "generator":
        return None
    judgment = json.loads(event["output"])
    baseline._validate_judgment(judgment, case)
    return judgment


def aggregate(work, audit=None):
    meta = validate_candidate(work)
    cases = baseline.load_cases(prep.ROOT)
    indexed = {case["id"]: case for case in cases}
    profile = meta["contract"]["profile"]
    stream = work / "events.jsonl"
    events = [json.loads(line) for line in stream.read_text(encoding="utf-8").splitlines() if line.strip()] if stream.exists() else []
    grouped, contexts, agents, records = {}, set(), set(), []
    for event in events:
        cid, role = event["case_id"], event["role"]
        require(cid in indexed and role in baseline.ROLES, "unknown case or role")
        case = indexed[cid]
        group = grouped.setdefault(cid, {})
        require(role not in group, "duplicate role output; first output must not be replaced")
        if role == "generator":
            prompt = baseline.render_generator_prompt(case)
        else:
            require("generator" in group, "review precedes generation")
            output = group["generator"]["output"]
            if role == "adjudicator":
                require("reviewer-a" in group and "reviewer-b" in group, "adjudication precedes reviewers")
                a, b = [group[r]["judgment"] for r in ("reviewer-a", "reviewer-b")]
                require(baseline._disagree(a, b), "unnecessary adjudication")
                prompt = baseline.render_adjudicator_prompt(case, output, a, b)
            else:
                prompt = baseline.render_reviewer_prompt(case, output)
        judgment = validate_role(work, event, case, profile, meta["evaluation_identity"], contexts, agents, prompt)
        group[role] = {"output": event["output"], "judgment": judgment}
    for cid, group in grouped.items():
        if not all(role in group for role in ("generator", "reviewer-a", "reviewer-b")):
            continue
        case = indexed[cid]
        a, b = [group[r]["judgment"] for r in ("reviewer-a", "reviewer-b")]
        disagreement = baseline._disagree(a, b)
        if disagreement and "adjudicator" not in group:
            continue
        extra = group.get("adjudicator", {}).get("judgment")
        record = baseline._make_record(case, group["generator"]["output"], {}, [a, b], extra,
                                       {"tested_at": "not-used-in-summary", "tested_skill_digest": "not-used-in-summary"})
        exact = "expected_exact" not in case or record["output"] == case["expected_exact"]
        records.append({"id": cid, "final_rubric": record["final_rubric"], "case_pass": record["case_pass"],
                        "critical_failure": record["critical_failure"], "exact_match": exact})
    status = "prepared" if not events else "partial" if len(records) < 50 else "complete"
    groups = {}
    for filename in baseline.CASE_COUNTS:
        ids = {c["id"] for c in read(prep.ROOT / "evals" / filename)}
        subset = [r for r in records if r["id"] in ids]
        groups[filename] = {"completed": len(subset), "passed": sum(r["case_pass"] for r in subset)}
    quality = None
    if status == "complete":
        quality = (groups["core.json"]["passed"] >= 22 and
                   all(groups[name]["passed"] == count for name, count in baseline.CASE_COUNTS.items() if name != "core.json") and
                   not any(r["critical_failure"] or not r["exact_match"] for r in records) and
                   all(r["case_pass"] for r in records if r["id"] in baseline.REQUIRED_CASES))
    summary = {"status": status, "evaluation_identity": meta["evaluation_identity"],
               "events_sha256": prep.sha(stream.read_bytes()) if stream.exists() else None,
               "roles_recorded": len(events), "cases_completed": len(records), "groups": groups,
               "quality_gate_passed": quality, "records": records,
               "limitation": "Local receipt consistency is not independent proof of provider authenticity."}
    if audit is not None:
        require(status == "complete", "cannot verify incomplete candidate")
        review = read(audit)
        for key in ("evaluation_identity", "events_sha256"):
            require(review[key] == summary[key], "audit binding mismatch")
        require(review["summary_sha256"] == prep.sha(prep.encoded(summary)), "audit summary mismatch")
        require(review["reviewer_id"] not in agents and bool(review["reviewer_id"]), "audit reviewer is not independent")
        require(review["provider_receipts_verified"] is True and review["first_outputs_and_independence_verified"] is True,
                "independent evidence inspection incomplete")
        require(bool(review["evidence_source"]) and bool(review["reviewed_at"]), "missing audit provenance")
        assessment = receipt(work, review["independent_review_response"])
        attestation = receipt(work, review["independent_review_attestation"])
        for key in ("reviewer_id", "evaluation_identity", "events_sha256", "summary_sha256",
                    "provider_receipts_verified", "first_outputs_and_independence_verified"):
            require(assessment[key] == review[key], "independent audit response mismatch: " + key)
        require(attestation["source"] == "provider" and attestation["reviewer_id"] == review["reviewer_id"],
                "audit provider/runtime binding missing")
        require(attestation["response_sha256"] == review["independent_review_response"]["sha256"],
                "audit provider response digest mismatch")
        require(attestation["fresh_context"] is True and attestation["context_id"] not in contexts,
                "audit context was reused")
        require(str(uuid.UUID(attestation["context_id"])) == attestation["context_id"], "invalid audit context UUID")
        summary["status"] = "verified"
        summary["audit_sha256"] = prep.sha(audit.read_bytes())
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = aggregate(args.work_dir, args.audit)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        result = {"status": "candidate-error", "error": str(error), "quality_gate_passed": None}
    data = prep.encoded(result) + b"\n"
    if args.output:
        with args.output.open("xb") as target:
            target.write(data)
    else:
        print(data.decode("utf-8"), end="")
    return 1 if result["status"] == "candidate-error" else 0


if __name__ == "__main__":
    sys.exit(main())
