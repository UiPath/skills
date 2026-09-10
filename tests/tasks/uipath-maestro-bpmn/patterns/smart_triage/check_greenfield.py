#!/usr/bin/env python3
"""Grades smart-triage: a confidence floor whose human fallback rejoins the same
routing point, not a second dispatch path."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from bpmn_assertions import BPMN_NS, elements, fail, load_bpmn  # noqa: E402
from graph import ids, reachable, reaches  # noqa: E402

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

    # The fallback must converge on the routing gateway, but not necessarily in
    # one hop — applying the human's chosen category first is a fair adaptation.
    # Walk downstream instead of asserting a direct edge.
    manual_ids = ids(manual)
    gateway_ids = ids(gateways)
    downstream_of_manual = reachable(root, manual_ids)

    from_manual = downstream_of_manual & gateway_ids
    if not from_manual:
        fail(
            "the human fallback never reaches a gateway "
            f"(it reaches {sorted(n for n in downstream_of_manual if n)}) — routing was duplicated"
        )

    # One dispatch point means the confident path converges on the SAME gateway.
    # Without this a human-only routing gateway satisfies the check while the
    # confident items dispatch somewhere else entirely.
    conf_gates = [g for g in gateway_ids if g not in from_manual]
    if not conf_gates:
        fail("could not identify a confidence gate distinct from the routing gateway")

    # The confident branch must reach the router WITHOUT passing through the
    # human task. Plain reachability is satisfied by the fallback's own path,
    # which would let a human-only router pass as the shared dispatch point.
    route_candidates = [
        g for g in from_manual
        if len([f for f in flows(root) if f.attrib.get("sourceRef") == g]) >= 3
        and any(g in reachable(root, c, blocked=manual_ids) for c in conf_gates)
    ]
    if not route_candidates:
        fail(
            "no three-way gateway is reached from both the confidence gate and the "
            "human fallback — routing was duplicated rather than shared"
        )

    route_gate = route_candidates[0]
    out = [f for f in flows(root) if f.attrib.get("sourceRef") == route_gate]

    ends = elements(root, "endEvent")
    if len(ends) < 3:
        fail(f"expected a recorded outcome per category, found {len(ends)} end events")

    MSG = f"PASS: {len(gateways)} gateways, fallback rejoins {route_gate}, {len(out)} category routes, {len(ends)} outcomes"

    if not root.findall(f".//{{{DI_NS}}}BPMNDiagram"):
        fail("no bpmndi:BPMNDiagram — the file will not import")

    print(MSG)


if __name__ == "__main__":
    main()
