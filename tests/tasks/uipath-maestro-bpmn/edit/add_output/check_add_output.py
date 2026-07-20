#!/usr/bin/env python3
"""Add-output edit check.

A new output must be added to Task_Calc's mapping and backed by a new variable
declared in the process BPMN.Variables block, without disturbing the existing
output / variables / preserve-only payloads.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared.bpmn_assertions import mapping_outputs, variable_ids  # noqa: E402
from _shared.bpmn_check import parse_bpmn, require_di_for_visible_elements, require_sequence_integrity  # noqa: E402
from _shared.edit_check import (  # noqa: E402
    assert_no_orphan_di,
    assert_preserved,
    assert_uipath_preserved,
    by_id,
    fail,
    load_original,
)


def _output_vars(task) -> set[str]:
    return {o.attrib.get("var") or o.attrib.get("target") for o in mapping_outputs(task)}


def main() -> None:
    _path, edited = parse_bpmn("Invoicing")
    original = load_original(__file__, "Invoicing.bpmn")

    orig_vars = variable_ids(original)
    new_vars = variable_ids(edited)
    added_vars = new_vars - orig_vars
    if not added_vars:
        fail("no new variable declared in BPMN.Variables")
    if not orig_vars.issubset(new_vars):
        fail(f"existing variables were dropped: {sorted(orig_vars - new_vars)}")

    calc = by_id(edited, "Task_Calc")
    if calc is None:
        fail("Task_Calc is missing after the edit")
    outs = _output_vars(calc)
    if "Var_Total" not in outs:
        fail("the original Task_Calc output (Var_Total) was not preserved")
    if not (added_vars & outs):
        fail("Task_Calc has no output wired to the newly declared variable")
    if len(mapping_outputs(calc)) < 2:
        fail("Task_Calc must have at least two outputs after the edit")

    # Endpoints and preserve-only payloads stay untouched (variables legitimately change).
    assert_preserved(original, edited, ["Start_1", "End_1"])
    assert_uipath_preserved(original, edited, "migrationVersion")
    assert_uipath_preserved(original, edited, "caseManagement")

    require_sequence_integrity(edited)
    require_di_for_visible_elements(edited)
    assert_no_orphan_di(edited)
    print("OK: new output + variable added, existing output and payloads preserved")


if __name__ == "__main__":
    main()
