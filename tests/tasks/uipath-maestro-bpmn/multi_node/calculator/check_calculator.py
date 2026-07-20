#!/usr/bin/env python3
"""Structural check for the calculator BPMN port.

Enforces the ported intent: a multi-way exclusive gateway that routes on an
operator variable to one script task per arithmetic operation, with a valid
diagram. Grades authored XML shape, not runtime output (the BPMN skill is
authoring-only and cannot debug/run locally).
"""

from __future__ import annotations

import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    one_or_more,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)


def main() -> None:
    path, root = parse_bpmn("CalculatorBpmn")

    one_or_more(root, "startEvent")
    one_or_more(root, "endEvent")

    scripts = elements(root, "scriptTask")
    if len(scripts) < 3:
        fail(f"expected at least 3 script tasks (one per operation), found {len(scripts)}")

    gateways = one_or_more(root, "exclusiveGateway")
    flows = elements(root, "sequenceFlow")

    routed = False
    for gw in gateways:
        gw_id = attr(gw, "id")
        outgoing = [f for f in flows if attr(f, "sourceRef") == gw_id]
        if len(outgoing) < 3:
            continue
        default_id = attr(gw, "default")
        if not default_id:
            fail(f"multi-way gateway {gw_id} has no default flow")
        for flow in outgoing:
            fid = attr(flow, "id")
            has_condition = flow.find("bpmn:conditionExpression", NS) is not None
            if fid != default_id and not has_condition:
                fail(f"non-default flow {fid} from gateway {gw_id} has no condition")
        routed = True

    if not routed:
        fail("no exclusive gateway with >= 3 outgoing branches (multi-way operator routing)")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} routes an operator through a multi-way exclusive gateway with per-branch script tasks")


if __name__ == "__main__":
    main()
