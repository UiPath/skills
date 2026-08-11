#!/usr/bin/env python3
"""HITL result-consumed-downstream check.

Asserts the Actions.HITL activity binds a decision to a process variable and a
downstream gateway condition references that variable via vars.<id>, and that
the referenced variable is declared. Reuses shared stdlib-ET helpers.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    elements,
    fail,
    has_uipath_extension,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)


def declared_var_ids(root) -> set[str]:
    ids: set[str] = set()
    for var in root.findall(".//uipath:variables/*", NS):
        ident = var.attrib.get("id") or var.attrib.get("name")
        if ident:
            ids.add(ident)
    return ids


def main() -> None:
    path, root = parse_bpmn("ExpenseApprovalBpmn")

    hitl = [t for t in elements(root, "userTask") if has_uipath_extension(t, "Actions.HITL")]
    if not hitl:
        fail("no bpmn:userTask carrying an Actions.HITL uipath:activity shell")

    if not elements(root, "exclusiveGateway"):
        fail("no exclusive gateway consuming the HITL decision")

    out_vars = [
        o.attrib.get("var")
        for o in hitl[0].findall("bpmn:extensionElements/uipath:activity/uipath:output", NS)
        if o.attrib.get("var")
    ]
    if not out_vars:
        fail("HITL activity has no output mapping binding a variable (var=); decision not captured")

    cond_blob = " ".join(
        (c.text or "") for c in root.findall(".//bpmn:conditionExpression", NS)
    )
    referenced = [v for v in out_vars if f"vars.{v}" in cond_blob]
    if not referenced:
        fail(
            f"no downstream condition references the HITL output variable(s) {out_vars} "
            "via vars.<id>"
        )

    declared = declared_var_ids(root)
    undeclared = [v for v in referenced if v not in declared]
    if undeclared:
        fail(f"HITL output variable(s) referenced downstream but not declared: {undeclared}")

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} routes downstream on the HITL decision variable(s) {referenced}")


if __name__ == "__main__":
    main()
