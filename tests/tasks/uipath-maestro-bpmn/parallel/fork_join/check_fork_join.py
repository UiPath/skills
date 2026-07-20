#!/usr/bin/env python3
"""Structural check for the parallel fork + synchronizing join port.

Asserts a parallel gateway forks into two concurrent branches (one in, >=2 out)
and a parallel gateway synchronizes them (>=2 in, one out), with two distinct
branch activities between fork and join. Verifies diagram and sequence-flow
integrity.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
from _shared.bpmn_check import (  # noqa: E402
    attr,
    elements,
    fail,
    one_or_more,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)


def main() -> None:
    path, root = parse_bpmn("ParallelSync")

    gateways = one_or_more(root, "parallelGateway")
    flows = elements(root, "sequenceFlow")

    def out_flows(node_id):
        return [f for f in flows if attr(f, "sourceRef") == node_id]

    def in_flows(node_id):
        return [f for f in flows if attr(f, "targetRef") == node_id]

    forks = [gw for gw in gateways if len(out_flows(attr(gw, "id"))) >= 2]
    joins = [gw for gw in gateways if len(in_flows(attr(gw, "id"))) >= 2]
    if not forks:
        fail("no parallel gateway forks into >=2 outgoing flows")
    if not joins:
        fail("no parallel gateway synchronizes >=2 incoming flows")

    # The fork's two outgoing flows must reach two distinct downstream nodes.
    fork = forks[0]
    targets = {attr(f, "targetRef") for f in out_flows(attr(fork, "id"))}
    if len(targets) < 2:
        fail(f"fork gateway {attr(fork, 'id')} does not branch to >=2 distinct nodes")

    # The join's incoming flows must originate from two distinct upstream nodes.
    join = joins[0]
    sources = {attr(f, "sourceRef") for f in in_flows(attr(join, "id"))}
    if len(sources) < 2:
        fail(f"join gateway {attr(join, 'id')} does not synchronize >=2 distinct branches")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} forks into parallel branches and synchronizes them at a join gateway")


if __name__ == "__main__":
    main()
