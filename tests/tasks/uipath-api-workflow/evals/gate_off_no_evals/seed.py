#!/usr/bin/env python3
"""Seed an `init`-scaffolded, EMPTY project with NO evals/ folder — the Evaluations feature
is not enabled for it. Rule 22 must therefore stay silent: no test or loop-mode question,
no evals/ created, the workflow simply gets authored."""
import hashlib
import os
import sys
from pathlib import Path

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-api-workflow", "evals", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else str(Path(__file__).resolve().parent.parent / "_shared")
)
sys.path.insert(0, _shared_root)
from eval_fixtures import scaffold_project  # noqa: E402

project = Path("AddNumbers")
scaffold_project(project)
workflow = project / "Workflow.json"
if not workflow.is_file():
    sys.exit("FAIL: scaffold produced no Workflow.json")
Path(".gate").mkdir(exist_ok=True)
Path(".gate/workflow.sha256").write_text(hashlib.sha256(workflow.read_bytes()).hexdigest())
print(f"OK: scaffolded {project} without evals/; recorded scaffold Workflow.json hash")
