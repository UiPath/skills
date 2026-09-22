#!/usr/bin/env python3
"""Add-output edit check.

A new output must be added to Task_Calc's mapping and backed by a new variable
declared in the process BPMN.Variables block, without disturbing the existing
output / variables / preserve-only payloads.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_assertions import mapping_outputs, variable_ids  # noqa: E402
from _shared.bpmn_check import parse_bpmn, require_di_for_visible_elements, require_sequence_integrity  # noqa: E402
from _shared.edit_check import (  # noqa: E402
    assert_no_orphan_di,
    assert_preserved,
    assert_uipath_preserved,
    assert_variables_extended_only,
    by_id,
    fail,
    load_original,
)


def _output_vars(task) -> set[str]:
    return {o.attrib.get("var") or o.attrib.get("target") for o in mapping_outputs(task)}


def main() -> None:
    _path, edited = parse_bpmn("Invoicing")
    original = load_original("edit/add_output", "Invoicing.bpmn")

    # This task REQUIRES an addition; the shared guard covers the other half:
    # pristine declarations round-trip untouched, and additions are validated
    # in the blocks the canvas reads (process root or bpmn:subProcess).
    assert_variables_extended_only(original, edited)
    orig_vars = variable_ids(original)
    added_vars = variable_ids(edited) - orig_vars
    if not added_vars:
        fail("no new variable declared in BPMN.Variables")

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
