#!/usr/bin/env python3
"""Grades the evaluator an agent creates when asked for an LLM judge on a business rule.

A business rule is scored by exact match only, so the right answer to "an LLM judge that scores
only riskBand" is an exact-match evaluator whose target key narrows it to that output.
`evaluator`: `band-judge` is exact match, targeting riskBand, and no evaluator is of another type.
`set`: `Band checks` links only `band-judge` and its data points expect what the rule returns.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from rules_check import (  # noqa: E402
    check_data_points, check_exact_match_only, check_scored_by_exact_match, decision_of, fail,
    find_eval_set, find_project, load_rule, table_of,
)

EVALUATOR = "band-judge"
SET_NAME = "Band checks"
CASES = [{"creditScore": 550, "income": 90000}, {"creditScore": 720, "income": 30000}]


def band_judge(project) -> dict:
    found = [e for e in check_exact_match_only(project) if e.get("name") == EVALUATOR]
    if len(found) != 1:
        fail(f"expected one exact-match evaluator named {EVALUATOR}, found {len(found)}")
    return found[0]


def check_evaluator() -> None:
    project = find_project()
    decision = decision_of(load_rule(project)[1]).get("name")
    target = (band_judge(project).get("evaluatorConfig") or {}).get("targetOutputKey")
    # The decision has one output, so targeting the decision scores only riskBand too.
    if target not in (f"{decision}.riskBand", decision):
        fail(f"{EVALUATOR} targets {target!r}, expected {decision}.riskBand")
    print(f"OK: {EVALUATOR} is exact match on {target}")


def check_set() -> None:
    project = find_project()
    root = load_rule(project)[1]
    eval_set = find_eval_set(project, SET_NAME)
    refs = check_scored_by_exact_match(project, eval_set)
    if refs != [band_judge(project).get("id")]:
        fail(f"{SET_NAME} links {refs}, expected only {EVALUATOR}")
    check_data_points(eval_set, table_of(root), decision_of(root).get("name"), refs)
    inputs = [point.get("inputs") for point in eval_set.get("evaluations") or []]
    absent = [case for case in CASES if case not in inputs]
    if absent:
        fail(f"no data point has the inputs {absent}")
    print(f"OK: {SET_NAME} links only {EVALUATOR} and its data points match the rule")


if __name__ == "__main__":
    modes = {"evaluator": check_evaluator, "set": check_set}
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in modes:
        fail(f"usage: check_type_choice.py {'|'.join(modes)}")
    modes[mode]()
