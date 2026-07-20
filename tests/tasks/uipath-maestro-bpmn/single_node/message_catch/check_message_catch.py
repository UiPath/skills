#!/usr/bin/env python3
"""Structural check for the mid-flow receive-message (wait-for-event) eval.

Grades the Flow wait-for-email port: a bpmn:intermediateCatchEvent carries the
registry Maestro.ReceiveMessageEvent wrapper and a bpmn:messageEventDefinition,
sits genuinely mid-flow (both an inbound and an outbound sequence flow), and the
process start event is preserved (the wait was added, not swapped for the start).
Reuses the shared uipath-maestro-bpmn check helpers (stdlib ET, locally authored
input — same trust boundary as the rest of the fixture corpus).
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.bpmn_check import (  # noqa: E402
    attr,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
TYPE_TOKEN = "Maestro.ReceiveMessageEvent"


def has_type(el: ET.Element, token: str) -> bool:
    return token in ET.tostring(el, encoding="unicode")


def main() -> None:
    path, root = parse_bpmn("AwaitApprovalMessage")

    if not elements(root, "startEvent"):
        fail("no start event (the manual start must be preserved)")
    if not elements(root, "endEvent"):
        fail("no end event")

    catches = [
        c
        for c in elements(root, "intermediateCatchEvent")
        if has_type(c, TYPE_TOKEN)
        and c.find(f"{{{BPMN_NS}}}messageEventDefinition") is not None
    ]
    if not catches:
        fail(
            "missing bpmn:intermediateCatchEvent with Maestro.ReceiveMessageEvent "
            "and a messageEventDefinition"
        )
    catch = catches[0]

    # Wrong-host guard: the receive-message wait must not be modeled as a start
    # event (which would replace, not preserve, the process start).
    if any(has_type(s, TYPE_TOKEN) for s in elements(root, "startEvent")):
        fail("receive-message must be a mid-flow catch event, not the start event")

    catch_id = attr(catch, "id")
    flows = elements(root, "sequenceFlow")
    inbound = [f for f in flows if attr(f, "targetRef") == catch_id]
    outbound = [f for f in flows if attr(f, "sourceRef") == catch_id]
    if not inbound:
        fail("catch event has no inbound sequence flow (not mid-flow)")
    if not outbound:
        fail("catch event has no outbound sequence flow (not mid-flow)")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} waits mid-flow on a receive-message catch event with the start preserved")


if __name__ == "__main__":
    main()
