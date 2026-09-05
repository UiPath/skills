#!/usr/bin/env python3
"""Rule 22 (TDD gate): on a create request the agent must END ITS TURN with the two
questions — nothing authored yet. Graded deterministically: Workflow.json is still the
scaffold, the panel-seeded eval set still has zero rows, and the evaluator is unchanged."""
import hashlib
import json
import os
import sys
from pathlib import Path

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-api-workflow", "evals", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else str(Path(__file__).resolve().parent.parent / "_shared")
)
sys.path.insert(0, _shared_root)
from eval_fixtures import build_eval_set, build_evaluator, eval_set_path, evaluator_path  # noqa: E402

project = Path("AddNumbers")
workflow = project / "Workflow.json"
recorded = Path(".gate/workflow.sha256").read_text().strip()
problems = []
if not workflow.is_file():
    problems.append("Workflow.json is gone")
elif hashlib.sha256(workflow.read_bytes()).hexdigest() != recorded:
    problems.append("Workflow.json was authored before the user answered the tests / loop-mode questions")
if not eval_set_path(project).is_file() or json.loads(eval_set_path(project).read_text()) != build_eval_set([]):
    problems.append("the eval set was changed before the user said whether they want tests")
if not evaluator_path(project).is_file() or json.loads(evaluator_path(project).read_text()) != build_evaluator():
    problems.append("the evaluator was changed")
if problems:
    sys.exit("FAIL: " + "; ".join(problems))
print("OK: nothing authored — the agent stopped at the TDD gate")
