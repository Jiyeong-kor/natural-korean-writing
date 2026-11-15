"""Entirely synthetic receipts; not model outputs or provider evidence."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import aggregate_profile_eval as agg
import prepare_profile_eval as prep
import run_evals as base


class ProfileAggregateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name) / "candidate"
        with contextlib.redirect_stdout(io.StringIO()):
            prep.prepare(self.work)
        self.meta = agg.read(self.work / "candidate.json")
        self.cases = base.load_cases(prep.ROOT)
        self.events = []

    def save(self):
        (self.work / "events.jsonl").write_text("".join(json.dumps(e)+"\n" for e in self.events), encoding="utf-8")

    def evidence(self, data, label):
        name = f"synthetic-{len(self.events)}-{label}.json"
        raw = prep.encoded(data)
        (self.work / name).write_bytes(raw)
        return {"path": name, "sha256": prep.sha(raw)}

    def event(self, case, role, output, prompt):
        event = {"case_id": case["id"], "role": role, "attempt": 1, "context_id": str(uuid.uuid4()),
                 "agent_id": str(uuid.uuid4()), "evaluation_identity": self.meta["evaluation_identity"],
                 "prompt": prompt, "output": output}
        att = {**self.meta["contract"]["profile"], **{k:event[k] for k in ("case_id","role","context_id","agent_id","evaluation_identity")},
               "source":"provider", "runtime_version":"synthetic-test-only", "first_completed_output":True,"fresh_context":True,
               "prompt_sha256":prep.sha(prompt.encode()),"output_sha256":prep.sha(output.encode())}
        event["provider_attestation"] = self.evidence(att, "attestation")
        event["spawn_request"] = self.evidence({**self.meta["contract"]["profile"], "prompt":prompt}, "request")
        event["spawn_response"] = self.evidence({"agent_id":event["agent_id"]}, "response")
        self.events.append(event)
        return event

    def case(self, case, fail=False, disagree=False):
        output = case.get("expected_exact", "가상 검사 출력입니다.")
        self.event(case,"generator",output,base.render_generator_prompt(case))
        vote = {"id":case["id"],"rubric":dict.fromkeys(case["applicable_rubric"], "fail" if fail else "pass"),
                "critical_failure":fail,"reason":"가상 테스트 판정입니다."}
        second = {**vote,"critical_failure":not vote["critical_failure"]} if disagree else vote
        for role,v in (("reviewer-a",vote),("reviewer-b",second)):
            self.event(case,role,json.dumps(v),base.render_reviewer_prompt(case,output))
        return vote,second,output

    def test_prepared_and_partial(self):
        self.assertEqual(agg.aggregate(self.work)["status"],"prepared")
        c=self.cases[0]
        self.event(c,"generator","가상 출력",base.render_generator_prompt(c))
        self.save()
        self.assertEqual(agg.aggregate(self.work)["status"],"partial")

    def test_complete_verified_and_quality_failure(self):
        for i,c in enumerate(self.cases):self.case(c, fail=i==0)
        self.save()
        summary=agg.aggregate(self.work)
        self.assertEqual(summary["status"],"complete")
        self.assertFalse(summary["quality_gate_passed"])
        audit={k:summary[k] for k in ("evaluation_identity","events_sha256")}
        audit.update(summary_sha256=prep.sha(prep.encoded(summary)), reviewer_id="synthetic-independent-auditor",
                     provider_receipts_verified=True,first_outputs_and_independence_verified=True,
                     evidence_source="synthetic fixture; no actual provider",reviewed_at="synthetic")
        assessment={key:audit[key] for key in ("reviewer_id","evaluation_identity","events_sha256","summary_sha256",
                    "provider_receipts_verified","first_outputs_and_independence_verified")}
        audit["independent_review_response"]=self.evidence(assessment,"audit-response")
        audit["independent_review_attestation"]=self.evidence({"source":"provider","reviewer_id":audit["reviewer_id"],
            "response_sha256":audit["independent_review_response"]["sha256"],"fresh_context":True,"context_id":str(uuid.uuid4())},"audit-provider")
        path=self.work/"synthetic-audit.json";path.write_bytes(prep.encoded(audit))
        self.assertEqual(agg.aggregate(self.work,path)["status"],"verified")
        del audit["independent_review_attestation"];path.write_bytes(prep.encoded(audit))
        with self.assertRaises(KeyError):agg.aggregate(self.work,path)

    def test_missing_adjudication_is_partial_then_majority(self):
        c=self.cases[0];a,b,out=self.case(c,disagree=True);self.save()
        self.assertEqual(agg.aggregate(self.work)["cases_completed"],0)
        self.event(c,"adjudicator",json.dumps(a),base.render_adjudicator_prompt(c,out,a,b));self.save()
        self.assertEqual(agg.aggregate(self.work)["cases_completed"],1)

    def test_duplicate_context_rejected(self):
        self.case(self.cases[0]); self.events[1]["context_id"]=self.events[0]["context_id"];self.save()
        with self.assertRaisesRegex(ValueError,"duplicate context"):agg.aggregate(self.work)

    def test_duplicate_role_rejected(self):
        self.case(self.cases[0]);self.events.append(self.events[0]);self.save()
        with self.assertRaisesRegex(ValueError,"duplicate role"):agg.aggregate(self.work)

    def test_missing_attestation_rejected(self):
        self.case(self.cases[0]);(self.work/self.events[0]["provider_attestation"]["path"]).unlink();self.save()
        with self.assertRaises(OSError):agg.aggregate(self.work)

    def test_request_cannot_substitute_actual_model(self):
        self.case(self.cases[0]);e=self.events[0];ref=e["provider_attestation"];p=self.work/ref["path"]
        value=agg.read(p);value["model"]="different-model";p.write_bytes(prep.encoded(value));ref["sha256"]=prep.sha(p.read_bytes());self.save()
        with self.assertRaisesRegex(ValueError,"attested runtime mismatch"):agg.aggregate(self.work)

    def test_cli_candidate_error(self):
        self.events=[{"case_id":"unknown","role":"generator"}];self.save()
        with patch.object(sys,"argv",["aggregate_profile_eval.py","--work-dir",str(self.work)]),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(agg.main(),1)
        self.assertEqual(json.loads(out.getvalue())["status"],"candidate-error")

    def test_prompt_leak_rejected(self):
        self.case(self.cases[0]); self.events[1]["prompt"] += " leaked history"; self.save()
        with self.assertRaisesRegex(ValueError,"prompt mismatch"):agg.aggregate(self.work)

    def test_mandatory_case_fail_is_not_offset_by_total(self):
        for c in self.cases:self.case(c)
        required="meaning-close-001"
        for e in self.events:
            if e["case_id"] == required and e["role"] in ("reviewer-a","reviewer-b"):
                vote=json.loads(e["output"]);vote["rubric"][next(iter(vote["rubric"]))]="fail"
                e["output"]=json.dumps(vote)
                ref=e["provider_attestation"];p=self.work/ref["path"];att=agg.read(p)
                att["output_sha256"]=prep.sha(e["output"].encode());p.write_bytes(prep.encoded(att));ref["sha256"]=prep.sha(p.read_bytes())
        self.save();result=agg.aggregate(self.work)
        self.assertEqual(result["status"],"complete")
        self.assertFalse(result["quality_gate_passed"])

    def test_contract_input_omission_rejected(self):
        self.meta["contract"]["inputs"].pop(next(iter(self.meta["contract"]["inputs"])))
        self.meta["evaluation_identity"]=prep.sha(prep.encoded(self.meta["contract"]))
        (self.work/"candidate.json").write_bytes(prep.encoded(self.meta))
        with self.assertRaisesRegex(ValueError,"inputs missing"):agg.aggregate(self.work)


if __name__ == "__main__":unittest.main()
