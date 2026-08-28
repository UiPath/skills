#!/usr/bin/env python3
"""Grades external-wait: reply, reminder and deadline raced on one event-based
gateway, with the reminder resuming that same wait."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from bpmn_assertions import BPMN_NS, elements, fail, load_bpmn  # noqa: E402
from graph import reachable  # noqa: E402

DI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
BPMN = "VendorDocs/VendorDocs.bpmn"


def flows(root):
    return root.findall(f".//{{{BPMN_NS}}}sequenceFlow")


def main() -> None:
    root = load_bpmn(BPMN)
    waits = elements(root, "eventBasedGateway")
    if not waits:
        fail("no bpmn:eventBasedGateway — the outcomes were not modelled as a race")

    wait_id = waits[0].attrib.get("id")
    out = [f for f in flows(root) if f.attrib.get("sourceRef") == wait_id]
    if len(out) < 3:
        fail(f"wait gateway has {len(out)} outgoing flows, expected reply, reminder and deadline")

    timers = root.findall(f".//{{{BPMN_NS}}}timerEventDefinition")
    if len(timers) < 2:
        fail(f"expected a reminder timer and an SLA timer, found {len(timers)}")

    # Any incoming edge is not proof: a reply-validation path or an unrelated
    # cycle would satisfy it. Follow the gateway's own timer branches instead.
    timer_ids = {
        e.attrib.get("id")
        for e in root.findall(f".//{{{BPMN_NS}}}intermediateCatchEvent")
        if e.find(f"./{{{BPMN_NS}}}timerEventDefinition") is not None
    }
    timer_branches = {f.attrib.get("targetRef") for f in out} & timer_ids
    if not timer_branches:
        fail("no timer hangs off the wait gateway — there is no reminder or deadline branch")

    resuming = [t for t in timer_branches if wait_id in reachable(root, t)]
    if not resuming:
        fail(
            f"no timer branch off the gateway returns to it (branches: {sorted(timer_branches)}) "
            "— the reminder does not resume the wait"
        )

    ends = elements(root, "endEvent")
    if len(ends) < 2:
        fail(f"expected separate received and escalated outcomes, found {len(ends)} end events")

    MSG = f"PASS: event-based gateway with {len(out)} branches, {len(timers)} timers, reminder loops back, {len(ends)} outcomes"

    if not root.findall(f".//{{{DI_NS}}}BPMNDiagram"):
        fail("no bpmndi:BPMNDiagram — the file will not import")

    print(MSG)


if __name__ == "__main__":
    main()
