#!/usr/bin/env python3
"""Structural check for the terminate-end-event port.

Asserts one branch ends in a terminate end event (bare terminateEventDefinition)
while another branch reaches a normal end event, both fanned out from a fork
gateway. Terminate is authorable only on end events, so a terminate definition on
any other element is a failure. Verifies diagram and sequence-flow integrity.
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
    path, root = parse_bpmn("TerminateParallel")

    end_events = elements(root, "endEvent")
    if len(end_events) < 2:
        fail(f"expected >=2 end events (one terminate branch + one normal), found {len(end_events)}")

    terminating = [e for e in end_events if e.find("bpmn:terminateEventDefinition", NS) is not None]
    normal = [e for e in end_events if e.find("bpmn:terminateEventDefinition", NS) is None]
    if not terminating:
        fail("no end event carries a bpmn:terminateEventDefinition")
    if not normal:
        fail("no plain (non-terminate) end event — the other branch must end normally")

    # Terminate must live only on end events.
    for kind in ("startEvent", "intermediateCatchEvent", "intermediateThrowEvent", "boundaryEvent"):
        for ev in elements(root, kind):
            if ev.find("bpmn:terminateEventDefinition", NS) is not None:
                fail(f"terminateEventDefinition on a {kind} — only valid on end events")

    # A fork gateway (parallel or exclusive) drives the two branches.
    flows = elements(root, "sequenceFlow")
    forks = []
    for kind in ("parallelGateway", "exclusiveGateway", "inclusiveGateway"):
        for gw in elements(root, kind):
            out = [f for f in flows if attr(f, "sourceRef") == attr(gw, "id")]
            if len(out) >= 2:
                forks.append(gw)
    if not forks:
        fail("no fork gateway with >=2 outgoing flows to split the terminate and normal branches")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} has a terminate end event on one branch and a normal end on another")


if __name__ == "__main__":
    main()
