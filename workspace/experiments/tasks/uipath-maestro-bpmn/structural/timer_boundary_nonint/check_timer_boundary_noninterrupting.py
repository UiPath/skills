#!/usr/bin/env python3
"""Structural check for the non-interrupting timer boundary event.

Asserts a timer boundary event that reminds/escalates WITHOUT cancelling the
host task:
  - a boundaryEvent with a bpmn:timerEventDefinition;
  - cancelActivity="false" (non-interrupting);
  - attachedToRef resolves to a userTask;
  - a valid non-week ISO-8601 timer duration (or an expression);
  - a DI shape for the boundary event and an outgoing flow.

Element lookups are case-insensitive on the BPMN local name: registry
xmlTemplates emit capitalized element names (e.g. bpmn:UserTask for
Actions.HITL) while hand-authored structural BPMN uses the lowercase-camel
spec names. Reuses the shared uipath-maestro-bpmn check helpers.
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)

BPMN_NS = NS["bpmn"]


def els(root: ET.Element, kind: str) -> list[ET.Element]:
    """Case-insensitive BPMN element lookup by local name."""
    prefix = "{" + BPMN_NS + "}"
    kl = kind.lower()
    return [
        el for el in root.iter()
        if el.tag.startswith(prefix) and el.tag[len(prefix):].lower() == kl
    ]


def child(el: ET.Element, kind: str) -> ET.Element | None:
    prefix = "{" + BPMN_NS + "}"
    kl = kind.lower()
    for c in el:
        if c.tag.startswith(prefix) and c.tag[len(prefix):].lower() == kl:
            return c
    return None


def main() -> None:
    path, root = parse_bpmn("ApprovalReminder")

    user_task_ids = {attr(t, "id") for t in els(root, "userTask")}
    if not user_task_ids:
        fail("no userTask to attach a reminder timer to")
    flows = els(root, "sequenceFlow")

    timer_boundaries = [
        be for be in els(root, "boundaryEvent")
        if child(be, "timerEventDefinition") is not None
    ]
    if not timer_boundaries:
        fail("no timer boundary event (boundaryEvent with a bpmn:timerEventDefinition)")

    valid = False
    for be in timer_boundaries:
        be_id = attr(be, "id")
        # Non-interrupting: cancelActivity MUST be explicitly "false".
        if attr(be, "cancelActivity") != "false":
            continue
        attached = attr(be, "attachedToRef")
        if attached not in user_task_ids:
            fail(f"non-interrupting timer boundary {be_id} attachedToRef {attached!r} is not a userTask")
        tdef = child(be, "timerEventDefinition")
        spec = None
        for kind in ("timeDuration", "timeDate", "timeCycle"):
            el = child(tdef, kind)
            if el is not None and (el.text or "").strip():
                spec = el.text.strip()
                break
        if spec is None:
            fail(f"timer boundary {be_id} has no timeDuration/timeDate/timeCycle value")
        if not (spec.startswith("=") or spec.startswith("@")):
            if re.search(r"\dW", spec, re.IGNORECASE) or "P" in spec and re.search(r"W", spec):
                fail(f"timer boundary {be_id} uses an unsupported ISO-8601 week designator: {spec!r}")
            if not spec.startswith("P"):
                fail(f"timer boundary {be_id} duration {spec!r} is not a valid ISO-8601 duration/date")
        if not [f for f in flows if attr(f, "sourceRef") == be_id]:
            fail(f"timer boundary {be_id} has no outgoing flow (nothing happens on the reminder)")
        shaped = {s.attrib.get("bpmnElement") for s in root.findall(".//bpmndi:BPMNShape", NS)}
        if be_id not in shaped:
            fail(f"timer boundary {be_id} has no BPMNShape")
        valid = True
    if not valid:
        fail('no non-interrupting (cancelActivity="false") timer boundary attached to a userTask')

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} has a non-interrupting timer boundary on a userTask that does not cancel it")


if __name__ == "__main__":
    main()
