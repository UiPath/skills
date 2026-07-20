#!/usr/bin/env python3
"""Structural check for the multi-way exclusive-gateway (switch) port.

Asserts a single exclusive gateway routes 3+ conditioned branches plus exactly
one default flow — the BPMN analogue of a Flow Switch node. Verifies diagram
and sequence-flow integrity so the file is importable on the canvas.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    one_or_more,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)


def main() -> None:
    path, root = parse_bpmn("SeasonLookup")

    if not elements(root, "startEvent"):
        fail("no start event")
    if not elements(root, "endEvent"):
        fail("no end event")

    gateways = one_or_more(root, "exclusiveGateway")
    flows = elements(root, "sequenceFlow")
    flows_by_source: dict[str, list] = {}
    for flow in flows:
        flows_by_source.setdefault(attr(flow, "sourceRef"), []).append(flow)

    # Find the multi-way gateway: one exclusive gateway with >=4 outgoing flows
    # (>=3 conditioned branches + exactly one default).
    multiway = None
    for gw in gateways:
        outgoing = flows_by_source.get(attr(gw, "id"), [])
        if len(outgoing) >= 4:
            multiway = gw
            break
    if multiway is None:
        counts = {attr(gw, "id"): len(flows_by_source.get(attr(gw, "id"), [])) for gw in gateways}
        fail(f"no exclusive gateway with >=4 outgoing flows (a multi-way switch); found {counts}")

    gw_id = attr(multiway, "id")
    outgoing = flows_by_source.get(gw_id, [])
    default_id = attr(multiway, "default")
    if not default_id:
        fail(f"multi-way gateway {gw_id} has no default flow")

    conditioned = [
        f for f in outgoing
        if attr(f, "id") != default_id
        and f.find("bpmn:conditionExpression", NS) is not None
    ]
    if len(conditioned) < 3:
        fail(f"multi-way gateway {gw_id} has {len(conditioned)} conditioned branches; need >=3")

    non_default = [f for f in outgoing if attr(f, "id") != default_id]
    uncondition = [f for f in non_default if f.find("bpmn:conditionExpression", NS) is None]
    if uncondition:
        fail(f"non-default flows without a condition: {[attr(f, 'id') for f in uncondition]}")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} has a multi-way exclusive gateway ({len(conditioned)} conditioned + 1 default)")


if __name__ == "__main__":
    main()
