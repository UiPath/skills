#!/usr/bin/env python3
"""Structural check for the timer start-event (scheduled trigger) eval.

Grades the Flow scheduled-trigger port: the process start is a bpmn:startEvent
carrying the registry Intsvc.TimerTrigger wrapper and a bpmn:timerEventDefinition
configured with a recurring, non-zero ISO-8601 timeCycle; there is no manual
start; and the timer start is genuinely the process entry (no inbound flow).
Reuses the shared uipath-maestro-bpmn check helpers (stdlib ET, locally authored
input — same trust boundary as the rest of the fixture corpus).
"""

from __future__ import annotations

import os
import re
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
# ISO-8601 repeating interval: R[n]/ then a period or start-datetime.
REPEATING = re.compile(r"^R\d*/")


def child(el: ET.Element, local: str) -> ET.Element | None:
    return el.find(f"{{{BPMN_NS}}}{local}")


def main() -> None:
    path, root = parse_bpmn("ScheduledReportBpmn")

    starts = elements(root, "startEvent")
    if not starts:
        fail("no start event")
    if not elements(root, "endEvent"):
        fail("no end event")

    timer_starts = []
    for start in starts:
        xml = ET.tostring(start, encoding="unicode")
        if "Intsvc.TimerTrigger" in xml and child(start, "timerEventDefinition") is not None:
            timer_starts.append(start)
    if not timer_starts:
        fail("no bpmn:startEvent with Intsvc.TimerTrigger + timerEventDefinition")
    start = timer_starts[0]

    # No manual start: every start event must be the timer start (the flow port
    # replaced manual with scheduled — they must not coexist).
    non_timer = [s for s in starts if s not in timer_starts]
    if non_timer:
        fail(f"a non-timer (manual) start event remains: {[attr(s, 'id') for s in non_timer]}")

    timer_def = child(start, "timerEventDefinition")
    cycle = child(timer_def, "timeCycle")
    if cycle is None:
        fail("scheduled trigger must use a bpmn:timeCycle (recurring), not timeDuration/timeDate")
    cycle_text = (cycle.text or "").strip()
    if not REPEATING.match(cycle_text):
        fail(f"timeCycle must be an ISO-8601 repeating interval (R.../...); found {cycle_text!r}")
    if not re.search(r"[1-9]", cycle_text):
        fail(f"timeCycle has no non-zero component (never fires): {cycle_text!r}")

    # The timer start must genuinely be the process entry: nothing flows into it.
    start_id = attr(start, "id")
    if any(attr(f, "targetRef") == start_id for f in elements(root, "sequenceFlow")):
        fail("timer start event must be the process entry (no inbound sequence flow)")
    if not any(attr(f, "sourceRef") == start_id for f in elements(root, "sequenceFlow")):
        fail("timer start event must have an outgoing sequence flow")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} starts on a recurring timer schedule ({cycle_text})")


if __name__ == "__main__":
    main()
