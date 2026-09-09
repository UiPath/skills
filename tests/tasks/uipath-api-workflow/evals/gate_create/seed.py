#!/usr/bin/env python3
"""Seed the state a user really starts from: an `init`-scaffolded, EMPTY project in which
Studio Web's Evaluations panel has already been opened once — so `evals/default/` holds
the seeded exact-match evaluator and an eval set with ZERO rows. Records the scaffold
Workflow.json hash outside the project so the check can prove the agent stopped at the
TDD gate (rule 22) instead of authoring."""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from eval_fixtures import build_eval_set, build_evaluator, eval_set_path, evaluator_path, scaffold_project, write_json  # noqa: E402

project = Path("AddNumbers")
scaffold_project(project)
workflow = project / "Workflow.json"
if not workflow.is_file():
    sys.exit("FAIL: scaffold produced no Workflow.json")
write_json(evaluator_path(project), build_evaluator())
write_json(eval_set_path(project), build_eval_set([]))
Path(".gate").mkdir(exist_ok=True)
Path(".gate/workflow.sha256").write_text(hashlib.sha256(workflow.read_bytes()).hexdigest())
print(f"OK: scaffolded {project} with a panel-seeded evaluator and an empty eval set; recorded Workflow.json hash")
