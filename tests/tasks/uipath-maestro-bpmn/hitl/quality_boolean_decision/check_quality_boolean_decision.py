#!/usr/bin/env python3
"""HITL boolean-decision check.

Asserts the approval decision is a boolean-typed HITL output bound to a
boolean-typed variable, and the gateway condition treats it as a boolean rather
than comparing it to a quoted string literal. Reuses shared stdlib-ET helpers.
"""

from __future__ import annotations

import os
import re
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

STRINGLY = re.compile(r'(==|!=)\s*["\']')


def declared_var_types(root) -> dict[str, str]:
    types: dict[str, str] = {}
    for var in root.findall(".//uipath:variables/*", NS):
        ident = var.attrib.get("id") or var.attrib.get("name")
        if ident:
            types[ident] = (var.attrib.get("type") or "").lower()
    return types


def main() -> None:
    path, root = parse_bpmn("VendorApprovalBpmn")

    hitl = [t for t in elements(root, "userTask") if has_uipath_extension(t, "Actions.HITL")]
    if not hitl:
        fail("no bpmn:userTask carrying an Actions.HITL uipath:activity shell")

    bool_outputs = [
        o
        for o in hitl[0].findall("bpmn:extensionElements/uipath:activity/uipath:output", NS)
        if (o.attrib.get("type") or "").lower() in {"boolean", "bool"} and o.attrib.get("var")
    ]
    if not bool_outputs:
        fail("HITL has no boolean-typed output bound to a variable (decision is missing or stringly-typed)")

    declared = declared_var_types(root)
    bool_vars = []
    for o in bool_outputs:
        var = o.attrib.get("var")
        if var in declared and declared[var] not in {"boolean", "bool"}:
            fail(f"decision variable {var!r} declared as {declared[var]!r}, not boolean (stringly-typed)")
        bool_vars.append(var)

    cond_texts = [(c.text or "") for c in root.findall(".//bpmn:conditionExpression", NS)]
    ref_conditions = [c for c in cond_texts if any(f"vars.{v}" in c for v in bool_vars)]
    if not ref_conditions:
        fail(f"no gateway condition references the boolean HITL output variable(s) {bool_vars}")

    for cond in ref_conditions:
        if STRINGLY.search(cond):
            fail(f"boolean decision compared to a string literal (stringly-typed): {cond!r}")

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} models the approval as a boolean and routes on it as a boolean")


if __name__ == "__main__":
    main()
