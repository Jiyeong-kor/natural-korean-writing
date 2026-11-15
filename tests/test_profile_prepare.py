"""Preparation tests only; these tests do not execute or evaluate a model."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_profile_eval as profile
sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_source_fixture import pinned_source


class ProfilePreparationTests(unittest.TestCase):
    def test_fixed_independent_configuration(self):
        config = json.loads(profile.PROFILE.read_text(encoding="utf-8"))
        self.assertEqual(config["model"], "gpt-6-astra")
        self.assertEqual(config["reasoning_effort"], "xhigh")
        self.assertEqual(config["fork_turns"], "none")
        self.assertFalse(config["prior_results_reusable"])

    def test_prepare_is_not_a_model_run(self):
        with tempfile.TemporaryDirectory() as folder:
            pinned_source(self, folder)
            work = Path(folder) / "candidate"
            with contextlib.redirect_stdout(io.StringIO()):
                profile.prepare(work)
            metadata = json.loads((work / "candidate.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["status"], "prepared_not_started")
            self.assertEqual(metadata["model_cases_executed"], 0)
            self.assertIsNone(metadata["actual_runtime_version"])
            self.assertEqual(len(list((work / "prompts/generator").glob("*.txt"))), 50)
            self.assertNotIn("tested_at", metadata)
            with self.assertRaises(FileExistsError):
                profile.prepare(work)

    def test_changed_skill_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pinned_source(self, folder)
            skill = root / "skills/natural-korean-writing/SKILL.md"
            skill.write_text(skill.read_text(encoding="utf-8") + "\nChanged fixture input.\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Evaluated input changed"):
                profile.prepare(Path(folder) / "rejected-candidate")
            self.assertFalse((Path(folder) / "rejected-candidate").exists())

    def test_missing_runtime_evidence_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic-empty-evidence.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "runtime_surface"):
                profile.preflight(path)

    def test_requested_settings_alone_do_not_verify_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic-request-only.json"
            config = json.loads(profile.PROFILE.read_text(encoding="utf-8"))
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "spawn_request"):
                profile.preflight(path)


if __name__ == "__main__":
    unittest.main()
