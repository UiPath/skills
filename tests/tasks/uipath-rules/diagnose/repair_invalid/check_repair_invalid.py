#!/usr/bin/env python3
"""Grades the repaired RiskRules fixture: the policy still holds and the entry point carries the contract.

The fixture's single output was named `risk band`; any identifier name passes,
read from the table and checked in the regenerated contract.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from rules_check import (  # noqa: E402
    POLICY,
    POLICY_INPUTS,
    check_cases,
    check_contract,
    check_input_data,
    fail,
    find_project,
    load_rule,
    output_names,
    table_of,
)

if __name__ == "__main__":
    project = find_project()
    dmn_file, root = load_rule(project)
    check_input_data(root, POLICY_INPUTS)
    outputs = output_names(table_of(root))
    if len(outputs) != 1:
        fail(f"expected one output column, found {outputs}")
    check_contract(project, dmn_file, root, POLICY_INPUTS, {outputs[0]: "string"})
    check_cases(table_of(root), outputs[0], POLICY)
    print(f"OK: the contract matches and all {len(POLICY)} policy cases still hold")
