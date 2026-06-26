#!/usr/bin/env python3
"""Structural check for the timer-start authoring task.

Verifies the agent authored a process whose single start event carries a
bpmn:timerEventDefinition with a recurring timeCycle, wired to the rest of the
process, with a fully shaped, integral diagram. Reuses the shared
uipath-maestro-bpmn check helpers (stdlib ET, same trust boundary as the rest of
the fixture corpus — input is locally authored, not untrusted).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))

from bpmn_check import (  # noqa: E402
    NS,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
    text_content,
)


def main() -> None:
    path, root = parse_bpmn("ScheduledReport")

    starts = elements(root, "startEvent")
    if len(starts) != 1:
        fail(f"expected exactly one start event, found {len(starts)}")

    timer = starts[0].find("bpmn:timerEventDefinition", NS)
    if timer is None:
        fail("start event has no bpmn:timerEventDefinition (not a timer start)")
    cycle = timer.find("bpmn:timeCycle", NS)
    if cycle is None or not (text_content(timer)).strip():
        fail("timer start event has no timeCycle expression")

    if not elements(root, "endEvent"):
        fail("no end event")

    require_di_for_visible_elements(root)
    require_sequence_integrity(root)

    print(f"OK: {path} is started by a recurring timer start event")


if __name__ == "__main__":
    main()
