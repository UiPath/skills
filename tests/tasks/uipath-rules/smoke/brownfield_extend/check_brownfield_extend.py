#!/usr/bin/env python3
"""Grades the edit to the RiskRules fixture: a boolean `existingCustomer` input and an 800-or-more "Very Low" row.

`identity` checks the decision, entry point `filePath`, and original rows'
annotations kept their values and the regenerated contract carries the new input. `behavior`
checks the new and the unchanged bands.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from rules_check import (  # noqa: E402
    POLICY,
    check_annotations_in_order,
    check_cases,
    check_contract,
    check_input_data,
    decision_of,
    fail,
    find_project,
    load_rule,
    table_of,
)

DECISION_ID = "decision_25a2c471-1c6f-46cb-a22a-f4b2dfdb7ee7"
DECISION_NAME = "decision1"
ANNOTATIONS = ["Subprime", "Near-prime, sufficient income", "Near-prime, low income", "Prime"]
INPUTS = {"creditScore": "number", "income": "number", "existingCustomer": "boolean"}
UNCHANGED = [({**inputs, "existingCustomer": False}, band) for inputs, band in POLICY if inputs["creditScore"] < 800]
EDITED = [
    ({"creditScore": 650, "income": 30000, "existingCustomer": True}, "Medium"),
    ({"creditScore": 699, "income": 0, "existingCustomer": True}, "Medium"),
    ({"creditScore": 650, "income": 30000, "existingCustomer": False}, "High"),
    ({"creditScore": 579, "income": 90000, "existingCustomer": True}, "High"),
    ({"creditScore": 720, "income": 0, "existingCustomer": True}, "Low"),
    ({"creditScore": 799, "income": 90000, "existingCustomer": False}, "Low"),
    ({"creditScore": 800, "income": 0, "existingCustomer": False}, "Very Low"),
    ({"creditScore": 820, "income": 20000, "existingCustomer": True}, "Very Low"),
]


def check_identity() -> None:
    project = find_project()
    dmn_file, root = load_rule(project)
    decision = decision_of(root)
    if decision.get("id") != DECISION_ID or decision.get("name") != DECISION_NAME:
        fail("the decision's id or name changed; consumers bound to it would break")
    check_contract(project, dmn_file, root, INPUTS, {"riskBand": "string"})
    check_annotations_in_order(table_of(root), ANNOTATIONS)
    print("OK: decision, filePath, and the original rows' annotations kept; the contract carries existingCustomer")


def check_behavior() -> None:
    _, root = load_rule(find_project())
    check_input_data(root, INPUTS)
    check_cases(table_of(root), "riskBand", UNCHANGED + EDITED)
    print(f"OK: {len(EDITED)} edited and {len(UNCHANGED)} unchanged cases return the expected band")


if __name__ == "__main__":
    {"identity": check_identity, "behavior": check_behavior}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: fail("mode: identity | behavior"))()
