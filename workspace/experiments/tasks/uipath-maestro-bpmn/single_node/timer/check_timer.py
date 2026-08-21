#!/usr/bin/env python3
"""Structural check for the intermediate timer-event port (Flow Delay analogue).

Asserts an intermediate catch event carries a timer event definition with a
valid ISO-8601 duration (or timeDate/timeCycle), sits between the start and end
(one incoming + one outgoing flow), and has a diagram shape. Verifies overall
diagram and sequence-flow integrity.
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

ISO8601_DURATION = re.compile(r"^[=@]?P(?!$)(\d+Y)?(\d+M)?(\d+D)?(T(\d+H)?(\d+M)?(\d+S)?)?$")


def main() -> None:
    path, root = parse_bpmn("TimerWait")

    if not elements(root, "startEvent"):
        fail("no start event")
    if not elements(root, "endEvent"):
        fail("no end event")

    catches = elements(root, "intermediateCatchEvent")
    timer_catch = None
    for ev in catches:
        if ev.find("bpmn:timerEventDefinition", NS) is not None:
            timer_catch = ev
            break
    if timer_catch is None:
        fail("no intermediateCatchEvent with a bpmn:timerEventDefinition")

    timer_def = timer_catch.find("bpmn:timerEventDefinition", NS)
    duration = timer_def.find("bpmn:timeDuration", NS)
    date = timer_def.find("bpmn:timeDate", NS)
    cycle = timer_def.find("bpmn:timeCycle", NS)
    if duration is None and date is None and cycle is None:
        fail("timerEventDefinition has no timeDuration/timeDate/timeCycle child")
    if duration is not None:
        body = (duration.text or "").strip()
        if not ISO8601_DURATION.match(body):
            fail(f"timeDuration {body!r} is not a valid ISO-8601 duration (week designators unsupported)")

    ev_id = attr(timer_catch, "id")
    incoming = [f for f in elements(root, "sequenceFlow") if attr(f, "targetRef") == ev_id]
    outgoing = [f for f in elements(root, "sequenceFlow") if attr(f, "sourceRef") == ev_id]
    if not incoming:
        fail(f"timer event {ev_id} has no incoming sequence flow")
    if not outgoing:
        fail(f"timer event {ev_id} has no outgoing sequence flow")

    shaped = {s.attrib.get("bpmnElement") for s in root.findall(".//bpmndi:BPMNShape", NS)}
    if ev_id not in shaped:
        fail(f"timer event {ev_id} has no BPMNShape (invisible on the canvas)")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} has a wired intermediate timer catch event with a valid definition")


if __name__ == "__main__":
    main()
