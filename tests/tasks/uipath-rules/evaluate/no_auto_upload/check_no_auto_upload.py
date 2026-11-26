#!/usr/bin/env python3
"""Grades the local set an agent writes before it stops short of running it.

The task's real check is `command_not_executed` on `runs start` and the upload verbs; this one
proves the agent did the local work first: `Smoke` holds a data point per requested case, each
expecting what the rule returns, scored by exact match.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from rules_check import (  # noqa: E402
    check_data_points, check_exact_match_only, check_scored_by_exact_match, data_point_inputs, decision_of, fail,
    find_eval_set, find_project, load_rule, table_of,
)

SET_NAME = "Smoke"
CASES = [
    {"creditScore": 550, "income": 90000},
    {"creditScore": 650, "income": 60000},
    {"creditScore": 720, "income": 30000},
]

if __name__ == "__main__":
    project = find_project()
    root = load_rule(project)[1]
    check_exact_match_only(project)
    eval_set = find_eval_set(project, SET_NAME)
    refs = check_scored_by_exact_match(project, eval_set)
    check_data_points(eval_set, table_of(root), decision_of(root).get("name"), refs)
    absent = [case for case in CASES if case not in data_point_inputs(eval_set)]
    if absent:
        fail(f"no data point has the inputs {absent}")
    print(f"OK: {SET_NAME} covers all {len(CASES)} cases and matches the rule")
