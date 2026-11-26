#!/usr/bin/env python3
"""Grades the `Loan checks` set an agent writes for the two-decision LoanRules graph.

Passes when the graph still returns the loan policy, the set is scored by exact match, holds a
data point per requested applicant, and each one expects every output of both decisions, in
every evaluator's copy too.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import LOAN_CASES, LOAN_PROJECT, check_graph_cases, check_graph_data_points  # noqa: E402
from rules_check import (  # noqa: E402
    check_exact_match_only, check_scored_by_exact_match, data_point_inputs, fail, find_eval_set,
    find_project, load_graph,
)

SET_NAME = "Loan checks"
CASES = [
    {"creditScore": 550, "income": 90000, "loanAmount": 20000},
    {"creditScore": 650, "income": 60000, "loanAmount": 150000},
    {"creditScore": 720, "income": 30000, "loanAmount": 50000},
]

if __name__ == "__main__":
    project = find_project(LOAN_PROJECT)
    root = load_graph(project)[1]
    check_graph_cases(root, LOAN_CASES)
    check_exact_match_only(project)
    eval_set = find_eval_set(project, SET_NAME)
    check_graph_data_points(eval_set, root, check_scored_by_exact_match(project, eval_set))
    absent = [case for case in CASES if case not in data_point_inputs(eval_set)]
    if absent:
        fail(f"no data point has the inputs {absent}")
    print(f"OK: {SET_NAME} covers all {len(CASES)} applicants and expects both decisions")
