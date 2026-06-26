#!/usr/bin/env python3
"""Structural check for the move-node edit task.

Verifies the agent relocated the existing flagForReview task off the gateway's
conditioned branch onto the default branch (autoApprove -> flagForReview -> end),
routed the conditioned branch straight to the end event, kept the node set and all
ids unchanged, and left the diagram fully shaped with resolvable refs. Reuses the
shared uipath-maestro-bpmn check helpers (stdlib ET, same trust boundary as the
rest of the fixture corpus — input is locally authored, not untrusted).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from bpmn_check import (  # noqa: E402
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
    "Activity_Approve",
    "Event_end",
}


def main() -> None:
    path, root = parse_bpmn("OrderTriage")

    ids = {attr(e, "id") for e in root.iter() if attr(e, "id")}
    missing = sorted(PRESERVED_IDS - ids)
    if missing:
        fail(f"move changed the node id set; missing: {missing}")

    # No nodes added or removed: the original three script tasks remain.
    script_tasks = elements(root, "scriptTask")
    if len(script_tasks) != 3:
        fail(f"expected the original 3 script tasks, found {len(script_tasks)}")

    edges = {(attr(f, "sourceRef"), attr(f, "targetRef")) for f in elements(root, "sequenceFlow")}

    # New position: autoApprove -> flagForReview -> end.
    if ("Activity_Approve", "Activity_Review") not in edges:
        fail("missing sequence flow autoApprove -> flagForReview (node not moved onto default branch)")
    if ("Activity_Review", "Event_end") not in edges:
        fail("missing sequence flow flagForReview -> end")

    # Conditioned branch now routes the gateway straight to the end event.
    if ("Gateway_Route", "Event_end") not in edges:
        fail("conditioned branch was not rewired from the gateway to the end event")

    # Stale wiring must be gone.
    if ("Gateway_Route", "Activity_Review") in edges:
        fail("stale conditioned flow gateway -> flagForReview still present")
    if ("Activity_Approve", "Event_end") in edges:
        fail("stale flow autoApprove -> end still present (should now pass through flagForReview)")

    # Diagram + reference integrity (importable on the canvas).
    require_di_for_visible_elements(root)
    require_sequence_integrity(root)

    print(f"OK: {path} has flagForReview moved onto the default branch")


if __name__ == "__main__":
    main()
