#!/usr/bin/env python3
"""Structural check for the add-node edit task.

Verifies the agent inserted a new `enrichOrder` script task onto the
classifyOrder -> routeByRisk edge of the seeded OrderTriage process, rewired the
sequence flows so the gateway is now reached through the new node, preserved every
pre-existing node and id, and kept the diagram fully shaped (a BPMNShape per node,
a BPMNEdge per flow) with resolvable refs. Reuses the shared uipath-maestro-bpmn
check helpers (stdlib ET, same trust boundary as the rest of the fixture corpus —
input is locally authored, not untrusted).
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
        fail(f"edit dropped pre-existing elements: {missing}")

    # New node: a script task named enrichOrder (case-insensitive), distinct from
    # the seeded ones.
    new_nodes = [
        e for e in elements(root, "scriptTask")
        if attr(e, "name").strip().lower() == "enrichorder"
    ]
    if not new_nodes:
        fail("no script task named 'enrichOrder' was inserted")
    if len(new_nodes) > 1:
        fail("more than one 'enrichOrder' script task found")
    new_id = attr(new_nodes[0], "id")
    if new_id in PRESERVED_IDS:
        fail("inserted node reused a pre-existing id")

    # Rewiring: classify -> enrich -> gateway, and no direct classify -> gateway.
    flows = elements(root, "sequenceFlow")
    edges = {(attr(f, "sourceRef"), attr(f, "targetRef")) for f in flows}
    if ("Activity_Classify", new_id) not in edges:
        fail("missing sequence flow classifyOrder -> enrichOrder")
    if (new_id, "Gateway_Route") not in edges:
        fail("missing sequence flow enrichOrder -> routeByRisk")
    if ("Activity_Classify", "Gateway_Route") in edges:
        fail("stale direct flow classifyOrder -> routeByRisk still present")

    # Diagram + reference integrity (importable on the canvas).
    require_di_for_visible_elements(root)
    require_sequence_integrity(root)

    print(f"OK: {path} has enrichOrder inserted on the classify->gateway edge")


if __name__ == "__main__":
    main()
