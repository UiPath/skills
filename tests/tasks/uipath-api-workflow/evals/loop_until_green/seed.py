#!/usr/bin/env python3
"""Seed a project whose evals/ dataset is correct and whose workflow has TWO bugs:

- the Response emits `Grade` while output.schema (and every row) says `grade` — a key
  casing mismatch the CLI's PascalCased `Data` cannot reveal (`grade` prints as `Grade`
  either way), so only the raw output / the panel's strict deep-equal catches it;
- the threshold is `> 60` instead of `>= 60`, so the boundary row fails.

Rows: 85 -> PASS, 40 -> FAIL, 60 -> PASS. The dataset is the source of truth.
"""
import os
import sys
from pathlib import Path

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-api-workflow", "evals", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else str(Path(__file__).resolve().parent.parent / "_shared")
)
sys.path.insert(0, _shared_root)
from eval_fixtures import build_workflow, seed_project  # noqa: E402

ROWS = [
    ("2c0f3b1a-9a1e-4a4e-8e1a-000000000001", "score 85 passes", 85, "PASS"),
    ("2c0f3b1a-9a1e-4a4e-8e1a-000000000002", "score 40 fails", 40, "FAIL"),
    ("2c0f3b1a-9a1e-4a4e-8e1a-000000000003", "boundary score 60 passes", 60, "PASS"),
]

if __name__ == "__main__":
    project = seed_project(build_workflow(threshold=60, op=">", response_key="Grade"), ROWS)
    print(f"OK: seeded broken {project}/Workflow.json + evals/ dataset ({len(ROWS)} rows)")
