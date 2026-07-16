#!/usr/bin/env python3
"""Structural check for the timer-intermediate authoring task.

Verifies the agent authored a bpmn:intermediateCatchEvent carrying a
bpmn:timerEventDefinition with a timeDuration, wired between other nodes (incoming
and outgoing flow) and given its own diagram shape, with an integral diagram.
Reuses the shared uipath-maestro-bpmn check helpers (stdlib ET, same trust
boundary as the rest of the fixture corpus — input is locally authored, not
untrusted).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))

from bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)


def main() -> None:
    path, root = parse_bpmn("DelayProcess")

    timers = [
        e for e in elements(root, "intermediateCatchEvent")
        if e.find("bpmn:timerEventDefinition", NS) is not None
    ]
    if not timers:
        fail("no intermediateCatchEvent with a bpmn:timerEventDefinition (no delay)")
    timer = timers[0]
    if timer.find("bpmn:timerEventDefinition/bpmn:timeDuration", NS) is None:
        fail("timer intermediate event has no timeDuration")

    timer_id = attr(timer, "id")
    flows = elements(root, "sequenceFlow")
    if not any(attr(f, "targetRef") == timer_id for f in flows):
        fail("timer event has no incoming sequence flow")
    if not any(attr(f, "sourceRef") == timer_id for f in flows):
        fail("timer event has no outgoing sequence flow")

    # require_di_for_visible_elements does not cover intermediateCatchEvent —
    # assert its diagram shape explicitly.
    shaped = {s.attrib.get("bpmnElement") for s in root.findall(".//bpmndi:BPMNShape", NS)}
    if timer_id not in shaped:
        fail(f"timer intermediate event {timer_id} has no BPMNShape")

    require_di_for_visible_elements(root)
    require_sequence_integrity(root)

    print(f"OK: {path} has a wired, shaped timer intermediate catch event")


if __name__ == "__main__":
    main()
