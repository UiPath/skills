#!/usr/bin/env python3
"""Assert the pattern layer did not fire on work that does not need it.

The request is three steps with no decisions. Anything that shows up here —
a review task, a branch, an escalation net — was retrofitted, which is the
failure mode the router's negative gate exists to prevent.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from bpmn_assertions import (  # noqa: E402
    BPMN_NS,
    elements,
    fail,
    load_bpmn,
)
from graph import ids, reachable  # noqa: E402

BPMN = "NightlyExport/NightlyExport.bpmn"
FLOW_NODE_KINDS = (
    "startEvent",
    "endEvent",
    "task",
    "serviceTask",
    "scriptTask",
    "sendTask",
    "receiveTask",
    "userTask",
    "businessRuleTask",
    "subProcess",
    "callActivity",
    "exclusiveGateway",
    "parallelGateway",
    "inclusiveGateway",
    "eventBasedGateway",
    "intermediateCatchEvent",
    "intermediateThrowEvent",
    "boundaryEvent",
)


def main() -> None:
    root = load_bpmn(BPMN)

    # Only constructs that indicate a pattern fired. An error boundary event is
    # node-level recovery rather than a pattern shape, so it is not graded here
    # — failing it would red an agent for defensible error handling.
    unwanted = {
        "userTask": "a human review step",
        "exclusiveGateway": "a decision branch",
        "parallelGateway": "a parallel split",
        "inclusiveGateway": "a decision branch",
        "eventBasedGateway": "an event race",
    }
    for kind, what in unwanted.items():
        found = elements(root, kind)
        if found:
            names = [e.attrib.get("name") or e.attrib.get("id") for e in found]
            fail(f"retrofitted {what}: {len(found)} bpmn:{kind} {names} in a process with no decisions")

    # An event subprocess is the escalation net; a plain subprocess is
    # acceptable structure, so only the triggered kind is a finding.
    for sub in elements(root, "subProcess"):
        if sub.attrib.get("triggeredByEvent") == "true":
            fail("retrofitted an error event subprocess into a three-step linear process")

    ends = elements(root, "endEvent")
    if len(ends) != 1:
        fail(f"expected exactly one end event for a process with one outcome, found {len(ends)}")

    work = sum(len(elements(root, k)) for k in ("task", "serviceTask", "scriptTask", "sendTask"))
    if work < 3:
        fail(f"{work} work activities — the requested read, reshape and write steps are not all present")

    total = sum(len(elements(root, kind)) for kind in FLOW_NODE_KINDS)
    if total > 7:
        fail(f"{total} flow nodes for a three-step process — scaffolding was added")

    start = elements(root, "startEvent")[0].attrib.get("id")
    if not (reachable(root, start) & ids(elements(root, "endEvent"))):
        fail("the end event is not reachable from the start — the steps are not connected")

    if not root.findall(".//{http://www.omg.org/spec/BPMN/20100524/DI}BPMNDiagram"):
        fail("no bpmndi:BPMNDiagram — the file will not import")

    if not root.findall(f".//{{{BPMN_NS}}}sequenceFlow"):
        fail("no sequence flows — the steps are not connected")

    print(f"PASS: linear process, {total} flow nodes, one exit, no retrofitted pattern scaffolding")


if __name__ == "__main__":
    main()
