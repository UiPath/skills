#!/usr/bin/env python3
"""Structural check for the non-interrupting timer boundary event.

Asserts a timer boundary event that reminds/escalates WITHOUT cancelling the
host task:
  - a boundaryEvent with a bpmn:timerEventDefinition;
  - cancelActivity="false" (non-interrupting);
  - attachedToRef resolves to a userTask;
  - a valid non-week ISO-8601 timer duration (or an expression);
  - a DI shape for the boundary event and an outgoing flow.
Reuses the shared uipath-maestro-bpmn check helpers.
"""

from __future__ import annotations

import os
import re
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
    path, root = parse_bpmn("ApprovalReminder")

    user_task_ids = {attr(t, "id") for t in elements(root, "userTask")}
    if not user_task_ids:
        fail("no userTask to attach a reminder timer to")
    flows = elements(root, "sequenceFlow")

    timer_boundaries = [
        be for be in elements(root, "boundaryEvent")
        if be.find("bpmn:timerEventDefinition", NS) is not None
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
        tdef = be.find("bpmn:timerEventDefinition", NS)
        dur = tdef.find("bpmn:timeDuration", NS)
        date = tdef.find("bpmn:timeDate", NS)
        cycle = tdef.find("bpmn:timeCycle", NS)
        spec = None
        for el in (dur, date, cycle):
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
