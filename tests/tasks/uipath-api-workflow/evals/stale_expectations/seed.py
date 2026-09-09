#!/usr/bin/env python3
"""Seed a VALID project (PASS when score >= 60) with a dataset whose rows are all
correct for the CURRENT behaviour. The task lowers the threshold to 50: the schema is
unchanged, but the `score 55` row's expectation becomes stale (FAIL -> PASS) while the
other three rows stay valid."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from eval_fixtures import build_workflow, seed_project  # noqa: E402

ROWS = [
    ("7d4e2a90-5b6c-4f1d-a2b3-000000000001", "score 85 passes", 85, "PASS"),
    ("7d4e2a90-5b6c-4f1d-a2b3-000000000002", "score 40 fails", 40, "FAIL"),
    ("7d4e2a90-5b6c-4f1d-a2b3-000000000003", "score 55 fails", 55, "FAIL"),
    ("7d4e2a90-5b6c-4f1d-a2b3-000000000004", "boundary score 60 passes", 60, "PASS"),
]

if __name__ == "__main__":
    project = seed_project(build_workflow(threshold=60, op=">=", response_key="grade"), ROWS)
    print(f"OK: seeded {project}/Workflow.json (threshold 60) + evals/ dataset ({len(ROWS)} rows)")
