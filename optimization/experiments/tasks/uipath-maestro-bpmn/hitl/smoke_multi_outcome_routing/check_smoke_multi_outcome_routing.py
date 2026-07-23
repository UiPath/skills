#!/usr/bin/env python3
"""HITL multi-outcome routing check.

Asserts an Actions.HITL user task feeds an exclusive gateway that routes into
three distinct targets via two conditioned branches (referencing a vars.*
expression) plus exactly one default. Reuses the shared stdlib-ET helpers.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    has_uipath_extension,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)


def hitl_output_vars(task):
    return [
        o.attrib.get("var")
        for o in task.findall("bpmn:extensionElements/uipath:activity/uipath:output", NS)
        if o.attrib.get("var")
    ]


def main() -> None:
    path, root = parse_bpmn("LeaveRequestBpmn")

    hitl = [t for t in elements(root, "userTask") if has_uipath_extension(t, "Actions.HITL")]
    if not hitl:
        fail("no bpmn:userTask carrying an Actions.HITL uipath:activity shell")

    flows = elements(root, "sequenceFlow")
    gateways = elements(root, "exclusiveGateway")
    if not gateways:
        fail("no exclusive gateway to route HITL outcomes")

    routing_gw = None
    routing_outs: list = []
    for gw in gateways:
        outs = [f for f in flows if attr(f, "sourceRef") == attr(gw, "id")]
        if len(outs) >= 3:
            routing_gw, routing_outs = gw, outs
            break
    if routing_gw is None:
        fail("no exclusive gateway with >=3 outgoing branches (approve/reject/escalate)")

    if not attr(routing_gw, "default"):
        fail("routing gateway has no default branch")

    conditioned = [f for f in routing_outs if f.find("bpmn:conditionExpression", NS) is not None]
    if len(conditioned) < 2:
        fail("routing gateway needs >=2 conditioned branches plus a default")

    targets = {attr(f, "targetRef") for f in routing_outs}
    if len(targets) < 3:
        fail(f"routing branches lead to only {len(targets)} distinct targets, need 3")

    cond_blob = " ".join(
        (c.text or "")
        for f in routing_outs
        for c in f.findall("bpmn:conditionExpression", NS)
    )
    if "vars." not in cond_blob:
        fail("routing conditions do not reference any vars.* output expression")

    out_vars = hitl_output_vars(hitl[0])
    if out_vars and not any(f"vars.{v}" in cond_blob for v in out_vars):
        fail(f"routing conditions do not reference the HITL output variable(s) {out_vars}")

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} routes the HITL outcome into three distinct gateway branches")


if __name__ == "__main__":
    main()
