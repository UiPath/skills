#!/usr/bin/env python3
"""Structural check for the author-validate smoke task.

Verifies the agent authored a well-formed, importable Maestro BPMN: a diagram
shape for every node, an edge for every flow, resolvable sequence-flow refs, and
an exclusive gateway whose non-default branches carry conditions with exactly
one default. Reuses the shared uipath-maestro-bpmn check helpers (stdlib ET, same
trust boundary as the rest of the fixture corpus — input is locally authored,
not untrusted).
"""

from __future__ import annotations

import os
import sys

# Import shared helpers from the task suite's _shared module.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))

from bpmn_check import (  # noqa: E402
    attr,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)


def main() -> None:
    path, root = parse_bpmn("InvoiceApproval")

    if not elements(root, "startEvent"):
        fail("no start event")
    if not elements(root, "endEvent"):
        fail("no end event")

    gateways = elements(root, "exclusiveGateway")
    if not gateways:
        fail("no exclusive gateway authored")

    # Diagram + reference integrity (importable on the canvas).
    require_di_for_visible_elements(root)
    require_sequence_integrity(root)

    # Exclusive-gateway routing: exactly one default; every other outgoing flow
    # carries a condition expression.
    flows_by_id = {attr(f, "id"): f for f in elements(root, "sequenceFlow")}
    for gw in gateways:
        gw_id = attr(gw, "id")
        outgoing = [f for f in flows_by_id.values() if attr(f, "sourceRef") == gw_id]
        if len(outgoing) < 2:
            fail(f"exclusive gateway {gw_id} has fewer than 2 outgoing flows")
        default_id = attr(gw, "default")
        if not default_id:
            fail(f"exclusive gateway {gw_id} has no default flow")
        for flow in outgoing:
            fid = attr(flow, "id")
            has_condition = flow.find("bpmn:conditionExpression", {
                "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"
            }) is not None
            if fid != default_id and not has_condition:
                fail(f"non-default flow {fid} from gateway {gw_id} has no condition")

    print(f"OK: {path} is well-formed, fully shaped, and gateway-routed")


if __name__ == "__main__":
    main()
