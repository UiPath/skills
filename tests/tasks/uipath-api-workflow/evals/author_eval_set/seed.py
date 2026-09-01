#!/usr/bin/env python3
"""Seed a VALID score->grade project (PASS when score >= 60) whose Evaluations panel has
been opened once — `evals/default/` holds the seeded exact-match evaluator and an eval set
with ZERO rows. The feature is therefore ON for this project; the agent's job is to author
the rows, not to touch the workflow."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from eval_fixtures import build_workflow, seed_project  # noqa: E402

project = seed_project(build_workflow(threshold=60, op=">=", response_key="grade"), eval_rows=[])
print(f"OK: seeded {project}/Workflow.json + panel-seeded evaluator and an empty eval set")
