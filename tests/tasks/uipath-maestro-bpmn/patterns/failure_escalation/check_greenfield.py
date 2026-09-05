#!/usr/bin/env python3
"""Grades failure-escalation: an event subprocess that catches centrally,
classifies on the engine-seeded error context, and names every outcome."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-maestro-bpmn", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else str(Path(__file__).resolve().parents[2] / "_shared")
)
sys.path.insert(0, _shared_root)

from bpmn_assertions import BPMN_NS, elements, fail, load_bpmn  # noqa: E402

DI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
BPMN = "PayrollRun/PayrollRun.bpmn"


def flows(root):
    return root.findall(f".//{{{BPMN_NS}}}sequenceFlow")


def main() -> None:
    root = load_bpmn(BPMN)
    nets = [s for s in elements(root, "subProcess") if s.attrib.get("triggeredByEvent") == "true"]
    if not nets:
        fail("no event subprocess (triggeredByEvent) — failures are not caught centrally")

    net = nets[0]
    starts = net.findall(f"./{{{BPMN_NS}}}startEvent")
    if len(starts) != 1:
        fail(f"the net has {len(starts)} start events, expected exactly one")
    if starts[0].find(f"./{{{BPMN_NS}}}errorEventDefinition") is None:
        fail("the net's start event carries no errorEventDefinition")

    # Nothing may be attached to individual steps: that is the point of the net.
    if elements(root, "boundaryEvent"):
        fail("error handling was wired onto individual steps as well as centrally")

    conditions = [c.text or "" for c in net.findall(f".//{{{BPMN_NS}}}conditionExpression")]
    if not any("Error" in c for c in conditions):
        fail(f"no branch reads the engine-seeded error context (conditions: {conditions})")

    net_ends = net.findall(f".//{{{BPMN_NS}}}endEvent")
    if len(net_ends) < 2:
        fail(f"the net has {len(net_ends)} end events, expected one per response")
    unnamed = [e.attrib.get("id") for e in net_ends if not e.attrib.get("name")]
    if unnamed:
        fail(f"unnamed end events in the net {unnamed} — a handled failure reads as a clean run")

    MSG = f"PASS: event subprocess with an error start, classification on vars.Error, {len(net_ends)} named outcomes"

    if not root.findall(f".//{{{DI_NS}}}BPMNDiagram"):
        fail("no bpmndi:BPMNDiagram — the file will not import")

    print(MSG)


if __name__ == "__main__":
    main()
