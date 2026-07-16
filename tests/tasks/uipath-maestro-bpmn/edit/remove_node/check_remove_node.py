#!/usr/bin/env python3
"""Structural check for the remove-node edit task.

Verifies the agent deleted the autoApprove script task from the seeded
OrderTriage process, rewired the routeByRisk gateway's default branch straight to
the end event, kept the flagForReview branch and all other ids, and left no
dangling sequence-flow refs or orphaned diagram shapes/edges pointing at the
deleted node. Reuses the shared uipath-maestro-bpmn check helpers (stdlib ET, same
trust boundary as the rest of the fixture corpus — input is locally authored, not
untrusted).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)

PRESERVED_IDS = {
    "Event_start",
    "Activity_Classify",
    "Gateway_Route",
    "Activity_Review",
    "Event_end",
}


def main() -> None:
    path, root = parse_bpmn("OrderTriage")

    ids = {attr(e, "id") for e in root.iter() if attr(e, "id")}
    missing = sorted(PRESERVED_IDS - ids)
    if missing:
        fail(f"edit dropped elements that should have been preserved: {missing}")

    # autoApprove fully gone: neither its id nor its name remains.
    if "Activity_Approve" in ids:
        fail("autoApprove node id 'Activity_Approve' still present")
    if any(attr(e, "name").strip().lower() == "autoapprove" for e in elements(root, "scriptTask")):
        fail("a script task named 'autoApprove' still present")

    # Gateway still exclusive with a default branch, now targeting the end event.
    gateways = elements(root, "exclusiveGateway")
    if len(gateways) != 1:
        fail(f"expected exactly one exclusive gateway, found {len(gateways)}")
    gw = gateways[0]
    default_id = attr(gw, "default")
    if not default_id:
        fail("routeByRisk lost its default flow")
    flows_by_id = {attr(f, "id"): f for f in elements(root, "sequenceFlow")}
    default_flow = flows_by_id.get(default_id)
    if default_flow is None:
        fail(f"default flow {default_id} not found")
    if attr(default_flow, "targetRef") != "Event_end":
        fail("gateway default branch was not rewired to the end event")

    # flagForReview branch still intact off the gateway.
    gw_id = attr(gw, "id")
    review_flows = [
        f for f in flows_by_id.values()
        if attr(f, "sourceRef") == gw_id and attr(f, "targetRef") == "Activity_Review"
    ]
    if not review_flows:
        fail("flagForReview branch off the gateway was lost")

    # No orphaned diagram element references a deleted id.
    for shape in root.findall(".//bpmndi:BPMNShape", NS):
        if shape.attrib.get("bpmnElement") not in ids:
            fail(f"orphan BPMNShape references deleted element {shape.attrib.get('bpmnElement')!r}")
    for edge in root.findall(".//bpmndi:BPMNEdge", NS):
        if edge.attrib.get("bpmnElement") not in flows_by_id:
            fail(f"orphan BPMNEdge references deleted flow {edge.attrib.get('bpmnElement')!r}")

    # Diagram + reference integrity (importable on the canvas).
    require_di_for_visible_elements(root)
    require_sequence_integrity(root)

    print(f"OK: {path} has autoApprove removed and the default branch rewired to end")


if __name__ == "__main__":
    main()
