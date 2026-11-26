#!/usr/bin/env python3
"""Grades the agent's `Policy` set for RiskRules, locally and by running it through the tenant.

`set`: every data point expects what the rule returns, and the boundaries are covered.
`run`: the `set` checks hold, then `uip rules eval runs start --wait` on the set completes and
scores every data point in full.
The grader starts its own run instead of reading the agent's, so the outcome does not depend on
a run record the agent's session kept.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from rules_check import (  # noqa: E402
    POLICY, check_cases, check_data_points, check_exact_match_only, check_scored_by_exact_match,
    data_point_inputs,
    decision_of, fail, find_eval_set, find_project, load_rule, table_of,
)

SET_NAME = "Policy"
BOUNDARIES = [
    {"creditScore": 579, "income": 50000},
    {"creditScore": 580, "income": 50000},
    {"creditScore": 650, "income": 49999},
    {"creditScore": 699, "income": 75000},
    {"creditScore": 700, "income": 0},
]


def check_set() -> None:
    project = find_project()
    root = load_rule(project)[1]
    check_cases(table_of(root), "riskBand", POLICY)
    check_exact_match_only(project)
    eval_set = find_eval_set(project, SET_NAME)
    refs = check_scored_by_exact_match(project, eval_set)
    check_data_points(eval_set, table_of(root), decision_of(root).get("name"), refs)
    absent = [case for case in BOUNDARIES if case not in data_point_inputs(eval_set)]
    if absent:
        fail(f"no data point has the boundary inputs {absent}")
    print(f"OK: {SET_NAME} matches the rule and covers the boundaries")


def full_marks(score: object) -> bool:
    # A miss is false or a number below 1 (the CLI's own `isMiss`); "-" means no score.
    return score is True or (isinstance(score, (int, float)) and not isinstance(score, bool) and score >= 1)


def check_run() -> None:
    # A run of a set that misses the boundaries scores in full too, so the set is graded first.
    check_set()
    project = find_project()
    points = len(find_eval_set(project, SET_NAME).get("evaluations") or [])
    completed = subprocess.run(
        ["uip", "rules", "eval", "runs", "start", "--set", SET_NAME, "--wait", "--timeout", "900",
         "--path", str(project), "--output", "json"],
        capture_output=True, text=True, timeout=1200,
    )
    try:
        envelope = json.loads(completed.stdout)
    except ValueError:
        fail(f"runs start exited {completed.returncode} with no JSON envelope: {(completed.stdout or completed.stderr)[-1500:]}")
        raise AssertionError
    data = envelope.get("Data") or {}
    if completed.returncode != 0 or envelope.get("Code") != "RulesEvalRunCompleted":
        fail(f"runs start exited {completed.returncode}: {json.dumps(envelope)[-1500:]}")
    results = data.get("Results") or []
    if data.get("DataPoints") != points or len(results) != points:
        fail(f"the run scored {data.get('DataPoints')} data points, the set holds {points}")
    missed = [row.get("DataPoint") for row in results if not full_marks(row.get("Score"))]
    if missed:
        fail(f"data points {missed} did not score in full: {json.dumps(results)[-1500:]}")
    print(f"OK: the run completed and all {points} data points scored in full")


if __name__ == "__main__":
    modes = {"set": check_set, "run": check_run}
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in modes:
        fail(f"usage: check_eval_run.py {'|'.join(modes)}")
    modes[mode]()
