#!/usr/bin/env python3
"""Grades the edit that turns the single-table RiskRules fixture into a graph: a second decision returning `interestRate`.

`identity` checks the original decision, its entry point, its rows'
annotations, and the shapes already on the diagram kept their values. `behavior` checks the new decision requires the
original one and that both return the expected values.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import (  # noqa: E402
    LOAN_CASES,
    LOAN_INPUTS,
    LOAN_OUTPUTS,
    check_chain,
    check_diagram_kept,
    check_entry_points_kept,
    check_graph_cases,
    check_no_overlap,
    check_whole_file_contract,
    decision_for_output,
)
from rules_check import (  # noqa: E402
    NS,
    RISK_ANNOTATIONS,
    RISK_DECISION_ID,
    RISK_DECISION_NAME,
    RISK_FIXTURE,
    check_annotations_in_order,
    fail,
    find_project,
    load_graph,
)


def check_identity() -> None:
    project = find_project()
    dmn_file, root = load_graph(project)
    original = decision_for_output(root, "riskBand")
    if original.get("id") != RISK_DECISION_ID or original.get("name") != RISK_DECISION_NAME:
        fail("the original decision's id or name changed; consumers bound to it would break")
    check_entry_points_kept(project, RISK_FIXTURE)
    check_annotations_in_order(original.find("dmn:decisionTable", NS), RISK_ANNOTATIONS)
    check_whole_file_contract(project, dmn_file, LOAN_INPUTS, LOAN_OUTPUTS)
    check_diagram_kept(RISK_FIXTURE, root)
    check_no_overlap(root)
    print("OK: the original decision, its entry point, its rows, and its shapes are kept; the contract carries the new decision")


def check_behavior() -> None:
    _, root = load_graph(find_project())
    check_chain(root, "interestRate", "riskBand")
    check_graph_cases(root, LOAN_CASES)
    print(f"OK: interestRate requires riskBand and all {len(LOAN_CASES)} cases match")


if __name__ == "__main__":
    {"identity": check_identity, "behavior": check_behavior}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: fail("mode: identity | behavior"))()
