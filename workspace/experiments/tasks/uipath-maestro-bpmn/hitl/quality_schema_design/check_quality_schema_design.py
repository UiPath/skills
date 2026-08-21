#!/usr/bin/env python3
"""HITL data-mapping design check.

Asserts the Actions.HITL activity presents context (input mapping), captures the
reviewer's returned data as typed output mappings, and binds every output to a
declared process variable (no dangling bindings). Reuses shared stdlib-ET helpers.
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
    path, root = parse_bpmn("VendorPOReviewBpmn")

    hitl = [t for t in elements(root, "userTask") if has_uipath_extension(t, "Actions.HITL")]
    if not hitl:
        fail("no bpmn:userTask carrying an Actions.HITL uipath:activity shell")
    task = hitl[0]

    inputs = task.findall(
        "bpmn:extensionElements/uipath:activity/uipath:context/uipath:input", NS
    ) + task.findall("bpmn:extensionElements/uipath:activity/uipath:input", NS)
    if not inputs:
        fail("HITL activity has no input mapping presenting context to the reviewer")

    outputs = [
        o
        for o in task.findall("bpmn:extensionElements/uipath:activity/uipath:output", NS)
        if o.attrib.get("var")
    ]
    if not outputs:
        fail("HITL activity has no output mapping (with var=) capturing the reviewer's returned data")

    if not any(o.attrib.get("type") for o in outputs):
        fail("HITL output mappings are untyped (no type= on any captured field)")

    declared = declared_var_ids(root)
    dangling = [o.attrib.get("var") for o in outputs if o.attrib.get("var") not in declared]
    if dangling:
        fail(f"HITL output variables not declared in uipath:variables (dangling bindings): {dangling}")

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} HITL presents context and captures typed, declared reviewer outputs")


if __name__ == "__main__":
    main()
