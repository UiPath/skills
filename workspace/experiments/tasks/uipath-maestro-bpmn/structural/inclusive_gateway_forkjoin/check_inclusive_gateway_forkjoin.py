#!/usr/bin/env python3
"""Structural check for the inclusive (OR) gateway fork + real inclusive join.

Asserts:
  - two distinct bpmn:inclusiveGateway elements: a split (one in, >=2 out) and a
    join (>=2 in, one out);
  - every outgoing branch from the split carries a conditionExpression (OR-fork
    semantics: each branch is independently gated);
  - the join synchronizes >=2 distinct upstream branches;
  - no gateway is superfluous (exactly one-in-one-out) — the join is a real
    inclusive join, not a fake join onto an activity.
Reuses the shared uipath-maestro-bpmn check helpers.
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
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)


def main() -> None:
    path, root = parse_bpmn("NotificationFanout")

    gateways = elements(root, "inclusiveGateway")
    if len(gateways) < 2:
        fail(f"expected >=2 inclusiveGateways (a split and a join), found {len(gateways)}")
    flows = elements(root, "sequenceFlow")

    def out_flows(nid):
        return [f for f in flows if attr(f, "sourceRef") == nid]

    def in_flows(nid):
        return [f for f in flows if attr(f, "targetRef") == nid]

    splits = [g for g in gateways if len(out_flows(attr(g, "id"))) >= 2 and len(in_flows(attr(g, "id"))) == 1]
    joins = [g for g in gateways if len(in_flows(attr(g, "id"))) >= 2 and len(out_flows(attr(g, "id"))) == 1]
    if not splits:
        fail("no inclusive split gateway (one incoming, >=2 outgoing)")
    if not joins:
        fail("no inclusive join gateway (>=2 incoming, one outgoing)")

    split = splits[0]
    join = joins[0]
    if attr(split, "id") == attr(join, "id"):
        fail("split and join are the same gateway; a real fork+join needs two")

    # Every branch out of the split is conditioned (OR-fork).
    for f in out_flows(attr(split, "id")):
        if f.find("bpmn:conditionExpression", NS) is None:
            fail(f"inclusive split branch {attr(f, 'id')} has no conditionExpression")

    # Join synchronizes >=2 distinct upstream branches.
    sources = {attr(f, "sourceRef") for f in in_flows(attr(join, "id"))}
    if len(sources) < 2:
        fail(f"inclusive join {attr(join, 'id')} does not synchronize >=2 distinct branches")

    # No superfluous gateway (one-in-one-out) among any gateway type.
    for kind in ("inclusiveGateway", "exclusiveGateway", "parallelGateway"):
        for g in elements(root, kind):
            gid = attr(g, "id")
            if len(in_flows(gid)) == 1 and len(out_flows(gid)) == 1:
                fail(f"{kind} {gid} has exactly one in and one out (SUPERFLUOUS_GATEWAY)")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} forks on a conditioned inclusive split and rejoins at a real inclusive join")


if __name__ == "__main__":
    main()
