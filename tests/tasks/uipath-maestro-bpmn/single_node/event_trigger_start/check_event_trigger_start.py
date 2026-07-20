#!/usr/bin/env python3
"""Structural check for the connector event-trigger start-event eval.

Grades the Flow connector-trigger port: the process start is a bpmn:startEvent
carrying the registry Intsvc.EventTrigger wrapper and a messageEventDefinition,
it is genuinely the process entry (no inbound flow, no manual start), it stays a
public-safe draft (no leaked tenant/cloud endpoint, no hand-authored generated
package files), and the diagram is complete. Reuses the shared uipath-maestro-bpmn
check helpers (stdlib ET, locally authored input — same trust boundary as the
rest of the fixture corpus).
"""

from __future__ import annotations

import glob
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
    require_no_private_connector_values,
    require_sequence_integrity,
)

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
TYPE_TOKEN = "Intsvc.EventTrigger"


def has_type(el: ET.Element, token: str) -> bool:
    return token in ET.tostring(el, encoding="unicode")


def main() -> None:
    path, root = parse_bpmn("InboxTriggerBpmn")

    starts = elements(root, "startEvent")
    if not starts:
        fail("no start event")
    if not elements(root, "endEvent"):
        fail("no end event")

    trigger_starts = [
        s
        for s in starts
        if has_type(s, TYPE_TOKEN)
        and s.find(f"{{{BPMN_NS}}}messageEventDefinition") is not None
    ]
    if not trigger_starts:
        fail("no bpmn:startEvent with Intsvc.EventTrigger + messageEventDefinition")
    start = trigger_starts[0]

    # No manual start: the connector trigger must be the sole start (replaced,
    # not coexisting with a manual entry).
    non_trigger = [s for s in starts if s not in trigger_starts]
    if non_trigger:
        fail(f"a non-trigger (manual) start event remains: {[attr(s, 'id') for s in non_trigger]}")

    start_id = attr(start, "id")
    if any(attr(f, "targetRef") == start_id for f in elements(root, "sequenceFlow")):
        fail("trigger start event must be the process entry (no inbound sequence flow)")
    if not any(attr(f, "sourceRef") == start_id for f in elements(root, "sequenceFlow")):
        fail("trigger start event must have an outgoing sequence flow")

    # Draft boundary: connection binding + package metadata are CLI-owned; the
    # agent must not hand-author the generated package files.
    generated = [
        name
        for name in (
            "bindings_v2.json",
            "entry-points.json",
            "operate.json",
            "package-descriptor.json",
        )
        if glob.glob(f"**/{name}", recursive=True)
    ]
    if generated:
        fail(f"draft trigger should not hand-author generated package files: {generated}")

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} starts on a public-safe connector event-trigger draft")


if __name__ == "__main__":
    main()
