#!/usr/bin/env python3
"""Grades the repaired LoanRules fixture, whose graph held a requirement on a missing input and a requirement cycle.

The policy still holds through an acyclic graph, both decisions keep their ids,
and the user's shapes and published entry points are kept.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import (  # noqa: E402
    LOAN_CASES,
    LOAN_PROJECT,
    check_entry_points_kept,
    check_graph_cases,
    check_shapes_kept,
    decision_for_output,
)
from rules_check import fail, find_project, load_graph  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / LOAN_PROJECT
DECISION_IDS = {"riskBand": "decision_risk", "interestRate": "decision_rate"}

if __name__ == "__main__":
    project = find_project(LOAN_PROJECT)
    _, root = load_graph(project)
    for output, decision_id in DECISION_IDS.items():
        if decision_for_output(root, output).get("id") != decision_id:
            fail(f"the decision returning {output} is no longer {decision_id}; consumers bound to it would break")
    check_graph_cases(root, LOAN_CASES)
    # A repair may legitimately delete what the hand edit left behind, so only the shapes that
    # remain are held to their old positions.
    check_shapes_kept(ET.parse(FIXTURE / "Business rule.dmn").getroot(), root, elements_may_go=True)
    check_entry_points_kept(project, FIXTURE)
    print(f"OK: the graph is acyclic and complete, all {len(LOAN_CASES)} cases hold, and the diagram and entry points are kept")
