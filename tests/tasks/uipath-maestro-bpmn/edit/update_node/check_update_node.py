#!/usr/bin/env python3
"""Structural check for the update-node edit task.

Verifies the agent edited the routeByRisk gateway's conditioned branch in place so
it now fires on risk >= 75 (the old `risk > 10` threshold is gone), without adding
or removing nodes and while preserving every element id and the diagram. Reuses
the shared uipath-maestro-bpmn check helpers (stdlib ET, same trust boundary as
the rest of the fixture corpus — input is locally authored, not untrusted).
"""

from __future__ import annotations

import os
import re
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

EXPECTED_IDS = {
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
    if not EXPECTED_IDS.issubset(ids):
        fail(f"edit changed the node id set; missing: {sorted(EXPECTED_IDS - ids)}")

    # No nodes added or removed: exactly the three seeded script tasks remain.
    script_tasks = elements(root, "scriptTask")
    if len(script_tasks) != 3:
        fail(f"expected the original 3 script tasks, found {len(script_tasks)}")

    # Locate the gateway's conditioned (non-default) flow to flagForReview.
    gateways = elements(root, "exclusiveGateway")
    if len(gateways) != 1:
        fail(f"expected exactly one exclusive gateway, found {len(gateways)}")
    gw = gateways[0]
    gw_id = attr(gw, "id")
    default_id = attr(gw, "default")
    conditioned = [
        f for f in elements(root, "sequenceFlow")
        if attr(f, "sourceRef") == gw_id
        and attr(f, "targetRef") == "Activity_Review"
        and attr(f, "id") != default_id
    ]
    if not conditioned:
        fail("no conditioned gateway flow to flagForReview found")

    expr_el = conditioned[0].find("bpmn:conditionExpression", NS)
    if expr_el is None or not (expr_el.text or "").strip():
        fail("conditioned flow has no condition expression")
    expr = expr_el.text.strip()

    if "75" not in expr:
        fail(f"condition was not updated to the 75 threshold: {expr!r}")
    if re.search(r"\b10\b", expr):
        fail(f"old threshold 10 still present in condition: {expr!r}")
    if "risk" not in expr:
        fail(f"condition no longer references risk: {expr!r}")

    # Diagram + reference integrity (importable on the canvas).
    require_di_for_visible_elements(root)
    require_sequence_integrity(root)

    print(f"OK: {path} routes to flagForReview on risk >= 75")


if __name__ == "__main__":
    main()
