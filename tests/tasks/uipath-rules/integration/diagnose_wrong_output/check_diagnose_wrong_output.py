#!/usr/bin/env python3
"""Grades the fixed RiskRules fixture: high scores reach the Low row again and every policy band still holds."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from rules_check import (  # noqa: E402
    POLICY,
    POLICY_INPUTS,
    POLICY_OUTPUTS,
    check_cases,
    check_contract,
    check_input_data,
    find_project,
    load_rule,
    table_of,
)

HIGH_SCORES = [
    ({"creditScore": 720, "income": 90000}, "Low"),
    ({"creditScore": 700, "income": 50000}, "Low"),
    ({"creditScore": 850, "income": 120000}, "Low"),
]


if __name__ == "__main__":
    project = find_project()
    dmn_file, root = load_rule(project)
    check_input_data(root, POLICY_INPUTS)
    check_contract(project, dmn_file, root, POLICY_INPUTS, POLICY_OUTPUTS)
    check_cases(table_of(root), "riskBand", HIGH_SCORES + POLICY)
    print(f"OK: all {len(HIGH_SCORES) + len(POLICY)} cases return the expected band")
