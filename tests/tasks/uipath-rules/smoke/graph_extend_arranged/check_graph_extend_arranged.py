#!/usr/bin/env python3
"""Grades a decision added to the LoanRules fixture, a graph whose shapes the user arranged by hand.

`diagram` checks the added decision is drawn, every shape the fixture placed is
where the user left it, no two cards overlap, and the published entry points are
kept. `behavior` checks the new `approved` decision and the two existing ones.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import (  # noqa: E402
    LOAN_CASES,
    LOAN_INPUTS,
    LOAN_OUTPUTS,
    LOAN_PROJECT,
    check_chain,
    check_entry_points_kept,
    check_new_elements_drawn,
    check_graph_cases,
    check_diagram_kept,
    check_no_overlap,
    check_whole_file_contract,
)
from rules_check import fail, find_project, load_graph  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / LOAN_PROJECT
CASES = [
    ({**inputs, "debtRatio": ratio}, {**expected, "approved": expected["riskBand"] != "High" and ratio <= 0.45})
    for inputs, expected in LOAN_CASES
    for ratio in (0.3, 0.45, 0.5)
]


def check_diagram() -> None:
    project = find_project(LOAN_PROJECT)
    _, root = load_graph(project)
    # First: the edit drew something. Kept-shapes, no-overlap and kept-entry-points are all
    # true of the staged fixture, so without this the criterion scored a sandbox nobody touched.
    check_new_elements_drawn(FIXTURE, root)
    check_diagram_kept(FIXTURE, root)
    check_no_overlap(root)
    check_entry_points_kept(project, FIXTURE)
    print("OK: the new decision is drawn, the user's shapes are where they were, no cards "
          "overlap, and the entry points are kept")


def check_behavior() -> None:
    project = find_project(LOAN_PROJECT)
    dmn_file, root = load_graph(project)
    check_chain(root, "approved", "riskBand")
    check_graph_cases(root, CASES)
    check_whole_file_contract(project, dmn_file, {**LOAN_INPUTS, "debtRatio": "number"}, {**LOAN_OUTPUTS, "approved": "boolean"})
    print(f"OK: approved requires riskBand and all {len(CASES)} cases match")


if __name__ == "__main__":
    {"diagram": check_diagram, "behavior": check_behavior}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: fail("mode: diagram | behavior"))()
