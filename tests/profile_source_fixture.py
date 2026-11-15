"""Stage source-controlled inputs for old-profile tooling tests, never model runs."""
import json
from pathlib import Path
import shutil
import subprocess
from unittest.mock import patch

import prepare_profile_eval as prep
import run_evals as base


def pinned_source(test, parent):
    """Keep current production checks intact while isolating their pinned fixture."""
    source = prep.ROOT
    root = Path(parent) / "pinned-source"
    subprocess.run(["git", "clone", "--quiet", "--shared", str(source), str(root)], check=True)
    config = json.loads(prep.PROFILE.read_text(encoding="utf-8"))
    commit = config["source_commit"]
    skill_dir = "skills/natural-korean-writing"
    shutil.rmtree(root / skill_dir)
    names = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", commit, "--", skill_dir], cwd=source
    ).decode("utf-8").splitlines()
    names += ["scripts/run_evals.py", "scripts/validate_repo.py"]
    names += ["evals/" + name for name in base.CASE_COUNTS]
    for name in names:
        data = subprocess.check_output(["git", "show", commit + ":" + name], cwd=source)
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    # Exercise current tooling against original inputs, not a new profile identity.
    for name in ("prepare_profile_eval.py", "aggregate_profile_eval.py"):
        shutil.copyfile(source / "scripts" / name, root / "scripts" / name)
    scope = patch.object(prep, "ROOT", root)
    scope.start()
    test.addCleanup(scope.stop)
    return root
