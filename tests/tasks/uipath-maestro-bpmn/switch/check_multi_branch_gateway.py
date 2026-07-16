#!/usr/bin/env python3
"""Structural check for the multi-branch switch task.

Verifies the agent authored a single exclusive gateway with three or more
outgoing branches, exactly one of which is the gateway default, with a
condition expression on every non-default branch, and a fully shaped, integral
diagram. Reuses the shared uipath-maestro-bpmn check helpers (stdlib ET, same
trust boundary as the rest of the fixture corpus — input is locally authored,
not untrusted).
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
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)


def main() -> None:
    path, root = parse_bpmn("TierRouting")

    flows = elements(root, "sequenceFlow")
    gateways = elements(root, "exclusiveGateway")
    if not gateways:
        fail("no exclusive gateway authored")

    multi = []
    for gw in gateways:
        outgoing = [f for f in flows if attr(f, "sourceRef") == attr(gw, "id")]
        if len(outgoing) >= 3:
            multi.append((gw, outgoing))
    if not multi:
        fail("no exclusive gateway has 3 or more outgoing branches (not a multi-way switch)")

    gw, outgoing = multi[0]
    gw_id = attr(gw, "id")
    default_id = attr(gw, "default")
    if not default_id:
        fail(f"switch gateway {gw_id} has no default branch")
    if not any(attr(f, "id") == default_id for f in outgoing):
        fail(f"switch gateway {gw_id} default {default_id} is not one of its outgoing flows")

    conditioned = 0
    for flow in outgoing:
        fid = attr(flow, "id")
        has_condition = flow.find("bpmn:conditionExpression", NS) is not None
        if fid == default_id:
            if has_condition:
                fail(f"default branch {fid} must not carry a condition")
        else:
            if not has_condition:
                fail(f"non-default branch {fid} has no condition")
            conditioned += 1
    if conditioned < 2:
        fail(f"switch needs 2+ conditioned branches, found {conditioned}")

    if not elements(root, "endEvent"):
        fail("no end event")

    require_di_for_visible_elements(root)
    require_sequence_integrity(root)

    print(f"OK: {path} switches on one gateway with {len(outgoing)} branches "
          f"({conditioned} conditioned + 1 default)")


if __name__ == "__main__":
    main()
