"""Prepare an isolated candidate profile; never invoke models or claim a pass."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import run_evals as baseline

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "evals/profiles/astra-xhigh-v1.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")


def prepare(work):
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    cases = baseline.load_cases(ROOT)
    commit = profile["source_commit"]
    subprocess.check_output(["git", "cat-file", "-e", commit + "^{commit}"], cwd=ROOT)
    # All evaluated inputs and the inherited renderer must match the approved source.
    inputs = ["scripts/run_evals.py", "scripts/validate_repo.py"]
    inputs += ["evals/" + name for name in baseline.CASE_COUNTS]
    inputs += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "skills/natural-korean-writing").rglob("*")) if p.is_file()]
    hashes = {}
    for name in inputs:
        data = (ROOT / name).read_bytes()
        original = subprocess.check_output(["git", "show", commit + ":" + name], cwd=ROOT)
        if data != original:
            raise ValueError("Evaluated input changed: " + name)
        hashes[name] = sha(data)
    if len(cases) != profile["case_count"]:
        raise ValueError("Baseline case count changed")
    contract = {"profile": profile, "inputs": hashes,
                "profile_protocol_sha256": sha((ROOT / "evals/profiles/README.md").read_bytes()),
                "preparation_tool_sha256": sha(Path(__file__).read_bytes())}
    metadata = {"status": "prepared_not_started", "prepared_at": datetime.now(timezone.utc).isoformat(),
                "evaluation_identity": sha(encoded(contract)), "contract": contract,
                "baseline_identity": baseline.compute_evaluation_identity(ROOT),
                "actual_runtime_version": None, "model_cases_executed": 0}
    work.mkdir(parents=True, exist_ok=False)
    (work / "candidate.json").write_bytes(encoded(metadata) + b"\n")
    for case in cases:
        path = work / "prompts/generator" / (case["id"] + ".txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(baseline.render_generator_prompt(case), encoding="utf-8")
    print(json.dumps({"status": metadata["status"], "case_count": len(cases),
                      "evaluation_identity": metadata["evaluation_identity"]}))


def preflight(evidence):
    """Check transport receipts, not a worker's unsupported claim of its model."""
    value = json.loads(evidence.read_text(encoding="utf-8"))
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    for key in ("runtime_surface", "model", "reasoning_effort", "sampling", "fork_turns"):
        if value.get(key) != profile[key]:
            raise ValueError("Missing/mismatching runtime evidence: " + key)
    # A request by itself only proves what was requested. Preserve the provider's
    # acceptance and any actual-model/runtime metadata separately.
    for key in ("spawn_request", "spawn_response", "runtime_attestation"):
        record = value.get(key, {})
        path = evidence.parent / record.get("path", "")
        if not path.is_file() or sha(path.read_bytes()) != record.get("sha256"):
            raise ValueError("Missing or changed evidence receipt: " + key)
    if value.get("model_verified_by_provider") is not True:
        raise ValueError("Provider model verification unavailable; request alone is insufficient")
    if not value.get("runtime_version"):
        raise ValueError("Actual runtime version or provider unversioned attestation required")
    print("Runtime receipt structure verified; receipt contents require independent inspection. No model quality verdict.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare").add_argument("--work-dir", type=Path, required=True)
    sub.add_parser("preflight").add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare(args.work_dir)
        else:
            preflight(args.evidence)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
