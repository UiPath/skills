#!/usr/bin/env python3
"""Structural check for the debug-not-validation discipline task.

Verifies the agent authored a well-formed, importable Maestro BPMN: a start, an
end, an exclusive gateway with exactly one default and conditioned non-default
branches, a diagram shape per node, an edge per flow, and resolvable
sequence-flow refs. Grades authored XML shape only — the discipline (no cloud
debug) is graded separately by the task's command_not_executed criterion.
"""

from __future__ import annotations

import os
import sys

# Walk up to the suite root that holds the shared check helpers.
_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)


def main() -> None:
    path, root = parse_bpmn("PriorityRouting")

    if not elements(root, "startEvent"):
        fail("no start event")
    if not elements(root, "endEvent"):
        fail("no end event")

    gateways = elements(root, "exclusiveGateway")
    if not gateways:
        fail("no exclusive gateway authored")

    require_di_for_visible_elements(root)
    require_sequence_integrity(root)

    flows = elements(root, "sequenceFlow")
    routed = False
    for gw in gateways:
        gw_id = attr(gw, "id")
        outgoing = [f for f in flows if attr(f, "sourceRef") == gw_id]
        if len(outgoing) < 2:
            continue
        default_id = attr(gw, "default")
        if not default_id:
            fail(f"exclusive gateway {gw_id} has no default flow")
        for flow in outgoing:
            fid = attr(flow, "id")
            has_condition = flow.find("bpmn:conditionExpression", NS) is not None
            if fid != default_id and not has_condition:
                fail(f"non-default flow {fid} from gateway {gw_id} has no condition")
        routed = True

    if not routed:
        fail("no exclusive gateway with >= 2 outgoing branches (priority routing)")

    print(f"OK: {path} is well-formed, fully shaped, and gateway-routed")


if __name__ == "__main__":
    main()
