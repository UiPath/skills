#!/usr/bin/env python3
"""Grades smart-triage: a confidence floor whose human fallback rejoins the same
routing point, not a second dispatch path."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from bpmn_assertions import BPMN_NS, elements, fail, load_bpmn  # noqa: E402

DI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
BPMN = "SupportTriage/SupportTriage.bpmn"


def flows(root):
    return root.findall(f".//{{{BPMN_NS}}}sequenceFlow")


def main() -> None:
    root = load_bpmn(BPMN)
    gateways = elements(root, "exclusiveGateway")
    if len(gateways) < 2:
        fail(f"expected a confidence gate and a routing gate, found {len(gateways)} exclusive gateways")

    manual = elements(root, "userTask")
    if not manual:
        fail("no userTask — low-confidence items have no human fallback")

    # The fallback must converge on a gateway that the confident path also
    # reaches, or the process grew two dispatch points instead of one.
    manual_ids = {t.attrib.get("id") for t in manual}
    gateway_ids = {g.attrib.get("id") for g in gateways}
    targets_from_manual = {
        f.attrib.get("targetRef") for f in flows(root) if f.attrib.get("sourceRef") in manual_ids
    }
    shared = targets_from_manual & gateway_ids
    if not shared:
        fail(
            "the human fallback does not rejoin a gateway "
            f"(it targets {sorted(t for t in targets_from_manual if t)}) — routing was duplicated"
        )

    route_gate = next(iter(shared))
    out = [f for f in flows(root) if f.attrib.get("sourceRef") == route_gate]
    if len(out) < 3:
        fail(f"routing gateway has {len(out)} outgoing flows, expected one per category")

    ends = elements(root, "endEvent")
    if len(ends) < 3:
        fail(f"expected a recorded outcome per category, found {len(ends)} end events")

    MSG = f"PASS: {len(gateways)} gateways, fallback rejoins {route_gate}, {len(out)} category routes, {len(ends)} outcomes"

    if not root.findall(f".//{{{DI_NS}}}BPMNDiagram"):
        fail("no bpmndi:BPMNDiagram — the file will not import")

    print(MSG)


if __name__ == "__main__":
    main()
