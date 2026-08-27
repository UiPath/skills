#!/usr/bin/env python3
"""Seed an `init`-scaffolded, EMPTY project with NO evals/ folder — the Evaluations feature
is not enabled for it. Rule 22 must therefore stay silent: no test or loop-mode question,
no evals/ created, the workflow simply gets authored."""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from eval_fixtures import scaffold_project  # noqa: E402

project = Path("AddNumbers")
scaffold_project(project)
workflow = project / "Workflow.json"
if not workflow.is_file():
    sys.exit("FAIL: scaffold produced no Workflow.json")
Path(".gate").mkdir(exist_ok=True)
Path(".gate/workflow.sha256").write_text(hashlib.sha256(workflow.read_bytes()).hexdigest())
print(f"OK: scaffolded {project} without evals/; recorded scaffold Workflow.json hash")
