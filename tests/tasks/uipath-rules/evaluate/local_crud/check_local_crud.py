#!/usr/bin/env python3
"""Grades the agent's cleanup of the `Rule tests` set the Evaluate tab wrote for RiskRules.

`points`: the table still holds the policy, and every data point expects what it returns, in
every evaluator's copy too (the wrong `Prime` band is fixed). `edits`: `Legacy` is gone, the
kept and boundary data points are there. `kept`: the set keeps its id, file and the tab's
`selectedEntrypoint`, and still links only exact-match evaluators.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from rules_check import (  # noqa: E402
    POLICY, check_cases, check_data_points, check_exact_match_only, data_point_inputs,
    decision_of, eval_sets, fail, find_eval_set, find_project, load_rule, table_of,
)

SET_NAME = "Rule tests"
SET_ID = "ab9a6050-a9a8-4fc6-89ef-2b8275f02de5"
KEPT = ["Subprime", "Prime"]
BOUNDARIES = [
    {"creditScore": 579, "income": 50000},
    {"creditScore": 580, "income": 50000},
    {"creditScore": 650, "income": 49999},
    {"creditScore": 700, "income": 0},
]


def check_points() -> None:
    project = find_project()
    root = load_rule(project)[1]
    check_cases(table_of(root), "riskBand", POLICY)
    check_data_points(find_eval_set(project, SET_NAME), table_of(root), decision_of(root).get("name"))
    print("OK: the policy is unchanged and every data point expects what the rule returns")


def check_edits() -> None:
    eval_set = find_eval_set(find_project(), SET_NAME)
    names = [point.get("name") for point in eval_set.get("evaluations") or []]
    if "Legacy" in names:
        fail("data point Legacy is still in the set")
    missing = [name for name in KEPT if name not in names]
    if missing:
        fail(f"data points {missing} were removed; only Legacy was to go")
    inputs = data_point_inputs(eval_set)
    absent = [case for case in BOUNDARIES if case not in inputs]
    if absent:
        fail(f"no data point has the boundary inputs {absent}")
    print(f"OK: Legacy removed, {KEPT} kept, all {len(BOUNDARIES)} boundaries added")


def check_kept() -> None:
    project = find_project()
    if len(eval_sets(project)) != 1:
        fail(f"expected the one set {SET_NAME!r}, found {len(eval_sets(project))}; edit it in place")
    eval_set = find_eval_set(project, SET_NAME)
    if eval_set.get("id") != SET_ID or eval_set.get("selectedEntrypoint") != "__br_eval_trigger__":
        fail("the set lost its id or the Evaluate tab's selectedEntrypoint; it was recreated, not edited")
    linked = set(eval_set.get("evaluatorRefs") or [])
    exact = {e.get("id") for e in check_exact_match_only(project)}
    if not linked or not linked <= exact:
        fail(f"the set links {sorted(linked)}, expected exact-match evaluators among {sorted(exact)}")
    print("OK: the tab's set is edited in place and scored by exact match")


if __name__ == "__main__":
    modes = {"points": check_points, "edits": check_edits, "kept": check_kept}
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in modes:
        fail(f"usage: check_local_crud.py {'|'.join(modes)}")
    modes[mode]()
