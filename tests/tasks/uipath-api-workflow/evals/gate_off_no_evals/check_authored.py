#!/usr/bin/env python3
"""No evals/ folder = feature off: the agent must author the workflow (Workflow.json differs
from the scaffold and computes the sum) and must NOT create an evals/ folder."""
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
from eval_scoring import deep_equal, run_row, wrap_output  # noqa: E402

project = Path("AddNumbers")
workflow = project / "Workflow.json"
problems = []
if not workflow.is_file():
    problems.append("Workflow.json is missing")
elif hashlib.sha256(workflow.read_bytes()).hexdigest() == Path(".gate/workflow.sha256").read_text().strip():
    problems.append("Workflow.json is still the untouched scaffold — the agent stopped instead of authoring")
if (project / "evals").exists():
    problems.append("an evals/ folder was created although the feature is not enabled for this project")
if not problems:
    ok, raw, error = run_row(workflow, {"a": 2, "b": 3})
    if not ok:
        problems.append(f"authored workflow does not run: {error}")
    elif not deep_equal(wrap_output(raw), {"sum": 5}):
        problems.append(f"raw output {json.dumps(raw)} != {{\"sum\": 5}}")
if problems:
    sys.exit("FAIL: " + "; ".join(problems))
print("OK: workflow authored without any test gate; no evals/ created")
