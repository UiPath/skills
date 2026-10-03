#!/usr/bin/env python3
"""Grades the fixed RiskRules fixture: high scores reach the Low row again, every policy band still holds, and rows 1, 3, and 4 are untouched."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from rules_check import (  # noqa: E402
    NS,
    POLICY,
    POLICY_INPUTS,
    POLICY_OUTPUTS,
    check_annotations_in_order,
    check_cases,
    check_contract,
    check_input_data,
    fail,
    find_project,
    load_rule,
    table_of,
)

HIGH_SCORES = [
    ({"creditScore": 720, "income": 90000}, "Low"),
    ({"creditScore": 700, "income": 50000}, "Low"),
    ({"creditScore": 850, "income": 120000}, "Low"),
]
ANNOTATIONS = ["Subprime", "Near-prime, sufficient income", "Near-prime, low income", "Prime"]
UNTOUCHED = {0: (["< 580", "-"], ['"High"']), 2: (["[580..700)", "-"], ['"High"']), 3: ([">= 700", "-"], ['"Low"'])}


def entries(rule, tag: str) -> list[str]:
    return [(e.findtext("dmn:text", default="", namespaces=NS) or "").strip() for e in rule.findall(f"dmn:{tag}", NS)]


def check_untouched(table) -> None:
    rules = table.findall("dmn:rule", NS)
    if len(rules) != len(ANNOTATIONS):
        fail(f"the table has {len(rules)} rows, expected the fixture's {len(ANNOTATIONS)}")
    check_annotations_in_order(table, ANNOTATIONS)
    for index, (inputs, outputs) in UNTOUCHED.items():
        if (entries(rules[index], "inputEntry"), entries(rules[index], "outputEntry")) != (inputs, outputs):
            fail(f"row {index + 1} changed; only row 2 holds the defect")


if __name__ == "__main__":
    project = find_project()
    dmn_file, root = load_rule(project)
    check_input_data(root, POLICY_INPUTS)
    check_contract(project, dmn_file, root, POLICY_INPUTS, POLICY_OUTPUTS)
    check_untouched(table_of(root))
    check_cases(table_of(root), "riskBand", HIGH_SCORES + POLICY)
    print(f"OK: rows 1, 3, and 4 untouched; all {len(HIGH_SCORES) + len(POLICY)} cases return the expected band")
