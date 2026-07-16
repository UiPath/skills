#!/usr/bin/env python3
"""Structural check for the terminate-end authoring task.

Verifies the agent authored a process that forks at a parallel gateway into a
branch ending in a bpmn:endEvent with a bpmn:terminateEventDefinition and a branch
ending in a normal end event, with an integral, fully shaped diagram. Reuses the
shared uipath-maestro-bpmn check helpers (stdlib ET, same trust boundary as the
rest of the fixture corpus — input is locally authored, not untrusted).
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
)


def main() -> None:
    path, root = parse_bpmn("TerminateProcess")

    ends = elements(root, "endEvent")
    if not ends:
        fail("no end event")
    terminating = [e for e in ends if e.find("bpmn:terminateEventDefinition", NS) is not None]
    normal = [e for e in ends if e.find("bpmn:terminateEventDefinition", NS) is None]
    if not terminating:
        fail("no end event carries a bpmn:terminateEventDefinition")
    if not normal:
        fail("no normal (non-terminate) end event on the surviving branch")

    if not elements(root, "parallelGateway"):
        fail("no parallel gateway forking the branches")

    require_di_for_visible_elements(root)
    require_sequence_integrity(root)

    print(f"OK: {path} forks to a terminate end event and a normal end event")


if __name__ == "__main__":
    main()
