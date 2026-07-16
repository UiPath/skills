#!/usr/bin/env python3
"""Structural check for the HITL brownfield-insert task.

Verifies the agent inserted a HITL userTask (Actions.HITL uipath:activity shell)
onto the classifyOrder -> routeByRisk edge of the seeded OrderTriage process,
rewired the flows so the gateway is reached through the approval, preserved every
pre-existing node and id, and kept the diagram integral. Reuses the shared
uipath-maestro-bpmn check helpers (stdlib ET, same trust boundary as the rest of
the fixture corpus — input is locally authored, not untrusted).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))

from bpmn_check import (  # noqa: E402
    attr,
    elements,
    fail,
    has_uipath_extension,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

PRESERVED_IDS = {
    "Event_start",
    "Activity_Classify",
    "Gateway_Route",
    "Activity_Review",
    "Activity_Approve",
    "Event_end",
}


def main() -> None:
    path, root = parse_bpmn("OrderTriage")

    ids = {attr(e, "id") for e in root.iter() if attr(e, "id")}
    missing = sorted(PRESERVED_IDS - ids)
    if missing:
        fail(f"insert dropped pre-existing elements: {missing}")

    # The original three script tasks are untouched (no script added/removed).
    if len(elements(root, "scriptTask")) != 3:
        fail(f"expected the original 3 script tasks, found {len(elements(root, 'scriptTask'))}")

    hitl = [t for t in elements(root, "userTask") if has_uipath_extension(t, "Actions.HITL")]
    if not hitl:
        fail("no bpmn:userTask with an Actions.HITL uipath:activity shell was inserted")
    if len(hitl) > 1:
        fail("more than one HITL userTask found")
    hitl_id = attr(hitl[0], "id")
    if hitl_id in PRESERVED_IDS:
        fail("inserted HITL reused a pre-existing id")

    edges = {(attr(f, "sourceRef"), attr(f, "targetRef")) for f in elements(root, "sequenceFlow")}
    if ("Activity_Classify", hitl_id) not in edges:
        fail("missing sequence flow classifyOrder -> HITL approval")
    if (hitl_id, "Gateway_Route") not in edges:
        fail("missing sequence flow HITL approval -> routeByRisk")
    if ("Activity_Classify", "Gateway_Route") in edges:
        fail("stale direct flow classifyOrder -> routeByRisk still present")

    require_no_private_connector_values(root)
    require_di_for_visible_elements(root)
    require_sequence_integrity(root)

    print(f"OK: {path} has a HITL approval inserted on the classify->gateway edge")


if __name__ == "__main__":
    main()
