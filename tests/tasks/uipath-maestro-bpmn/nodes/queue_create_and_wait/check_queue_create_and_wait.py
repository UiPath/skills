#!/usr/bin/env python3
"""Structural check for the dedicated CreateAndWaitForQueueItem node eval.

Grades that the synchronous queue wrapper `Orchestrator.CreateAndWaitForQueueItem`
is hosted on a bpmn:serviceTask (NOT the fire-and-forget sendTask that carries
`Orchestrator.CreateQueueItem`), binds a request input, and captures an output.
Uses the shared bpmn_assertions activity-type / mapping helpers (stdlib ET).
"""

from __future__ import annotations

import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from _shared.bpmn_assertions import activity_type, mapping_inputs, mapping_outputs  # noqa: E402
from _shared.bpmn_check import (  # noqa: E402
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

TYPE = "Orchestrator.CreateAndWaitForQueueItem"


def main() -> None:
    path, root = parse_bpmn("QueueCreateAndWaitBpmn")

    hosts = [t for t in elements(root, "serviceTask") if activity_type(t) == TYPE]
    if not hosts:
        fail(f"missing bpmn:serviceTask with {TYPE}")

    # Wrong-host guard: the synchronous wait wrapper must not sit on a
    # fire-and-forget sendTask or any other host.
    for kind in (
        "sendTask",
        "task",
        "callActivity",
        "userTask",
        "businessRuleTask",
        "receiveTask",
        "scriptTask",
    ):
        offenders = [e for e in elements(root, kind) if activity_type(e) == TYPE]
        if offenders:
            fail(f"{TYPE} must be on bpmn:serviceTask (synchronous wait), found on bpmn:{kind}")

    task = hosts[0]
    if not mapping_inputs(task):
        fail(f"{TYPE} serviceTask must bind at least one request input (queue item payload)")
    if not mapping_outputs(task):
        fail(f"{TYPE} serviceTask must capture at least one output (processed item)")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} hosts {TYPE} on a serviceTask with bound input and captured output")


if __name__ == "__main__":
    main()
