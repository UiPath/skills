#!/usr/bin/env python3
"""Structural check for the event-based gateway (first-catcher-wins) race.

Asserts:
  - a bpmn:eventBasedGateway with >=2 outgoing sequence flows;
  - every outgoing flow targets a bpmn:intermediateCatchEvent (the only valid
    target type for an event-based gateway);
  - among the raced catch events, at least one carries a messageEventDefinition
    and at least one carries a timerEventDefinition;
  - the gateway's outgoing flows all have BPMNEdges.
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
    path, root = parse_bpmn("PaymentRace")

    gateways = elements(root, "eventBasedGateway")
    if not gateways:
        fail("no bpmn:eventBasedGateway")
    flows = elements(root, "sequenceFlow")
    catch_by_id = {attr(c, "id"): c for c in elements(root, "intermediateCatchEvent")}
    edged = {e.attrib.get("bpmnElement") for e in root.findall(".//bpmndi:BPMNEdge", NS)}

    valid = False
    for gw in gateways:
        gw_id = attr(gw, "id")
        outgoing = [f for f in flows if attr(f, "sourceRef") == gw_id]
        if len(outgoing) < 2:
            continue
        targets = [attr(f, "targetRef") for f in outgoing]
        non_catch = [t for t in targets if t not in catch_by_id]
        if non_catch:
            fail(f"event-based gateway {gw_id} routes to non-catch targets {non_catch} (must be intermediateCatchEvents)")
        has_message = any(catch_by_id[t].find("bpmn:messageEventDefinition", NS) is not None for t in targets)
        has_timer = any(catch_by_id[t].find("bpmn:timerEventDefinition", NS) is not None for t in targets)
        if not has_message:
            fail(f"event-based gateway {gw_id} has no message catch among its raced events")
        if not has_timer:
            fail(f"event-based gateway {gw_id} has no timer catch among its raced events")
        for f in outgoing:
            if attr(f, "id") not in edged:
                fail(f"gateway outgoing flow {attr(f, 'id')} has no BPMNEdge")
        valid = True
    if not valid:
        fail("no event-based gateway with >=2 outgoing flows racing a message catch and a timer catch")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} races a message catch and a timer catch behind an event-based gateway")


if __name__ == "__main__":
    main()
