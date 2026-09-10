#!/usr/bin/env python3
"""Seed a VALID project (PASS when score >= 60) with a correct 4-row dataset. The task
then asks for a behaviour change that would make the `score 55` row stale; the agent
must ask before editing (rule 22, reference §3 step 5)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from eval_fixtures import build_workflow, seed_project  # noqa: E402

ROWS = [
    ("9b1d7c40-3e2f-4a5b-8c6d-000000000001", "score 85 passes", 85, "PASS"),
    ("9b1d7c40-3e2f-4a5b-8c6d-000000000002", "score 40 fails", 40, "FAIL"),
    ("9b1d7c40-3e2f-4a5b-8c6d-000000000003", "score 55 fails", 55, "FAIL"),
    ("9b1d7c40-3e2f-4a5b-8c6d-000000000004", "boundary score 60 passes", 60, "PASS"),
]

if __name__ == "__main__":
    project = seed_project(build_workflow(threshold=60, op=">=", response_key="grade"), ROWS)
    print(f"OK: seeded {project}/Workflow.json (threshold 60) + evals/ dataset ({len(ROWS)} rows)")
