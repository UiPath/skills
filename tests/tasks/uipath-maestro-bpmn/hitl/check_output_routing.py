#!/usr/bin/env python3
"""Structural check for the HITL output-routing task.

Verifies the agent authored a HITL userTask (Actions.HITL uipath:activity shell)
whose outgoing flow reaches an exclusive gateway with a default branch, at least
one conditioned branch, and both branches wired toward an end — i.e. the human
outcome drives downstream routing. Reuses the shared uipath-maestro-bpmn check
helpers (stdlib ET, same trust boundary as the rest of the fixture corpus — input
is locally authored, not untrusted).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))

from bpmn_check import (  # noqa: E402
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


def main() -> None:
    path, root = parse_bpmn("ApprovalRouting")

    hitl = [t for t in elements(root, "userTask") if has_uipath_extension(t, "Actions.HITL")]
    if not hitl:
        fail("missing bpmn:userTask with an Actions.HITL uipath:activity shell")

    if not elements(root, "endEvent"):
        fail("no end event")

    flows = elements(root, "sequenceFlow")
    flows_by_id = {attr(f, "id"): f for f in flows}
    hitl_ids = {attr(t, "id") for t in hitl}
    gateways = elements(root, "exclusiveGateway")

    # A gateway must sit immediately downstream of a HITL task.
    routed = [
        gw for gw in gateways
        if any(attr(f, "sourceRef") in hitl_ids and attr(f, "targetRef") == attr(gw, "id")
               for f in flows)
    ]
    if not routed:
        fail("no exclusive gateway is wired downstream of the HITL task (HITL -> gateway)")

    gw = routed[0]
    gw_id = attr(gw, "id")
    outgoing = [f for f in flows if attr(f, "sourceRef") == gw_id]
    if len(outgoing) < 2:
        fail(f"outcome gateway {gw_id} has fewer than 2 branches")
    default_id = attr(gw, "default")
    if not default_id or default_id not in flows_by_id:
        fail("outcome gateway has no valid default branch")
    for flow in outgoing:
        fid = attr(flow, "id")
        has_condition = flow.find("bpmn:conditionExpression", NS) is not None
        if fid != default_id and not has_condition:
            fail(f"non-default outcome branch {fid} has no condition")

    require_no_private_connector_values(root)
    require_di_for_visible_elements(root)
    require_sequence_integrity(root)

    print(f"OK: {path} routes a HITL outcome through a two-branch exclusive gateway")


if __name__ == "__main__":
    main()
