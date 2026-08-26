#!/usr/bin/env python3
"""Grades queue-distribution performer: a queue-triggered start, one item per
instance with no loop, and a distinct transaction status on every path."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from bpmn_assertions import BPMN_NS, elements, fail, load_bpmn  # noqa: E402

DI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
BPMN = "ClaimWorker/ClaimWorker.bpmn"


def flows(root):
    return root.findall(f".//{{{BPMN_NS}}}sequenceFlow")


def main() -> None:
    root = load_bpmn(BPMN)
    starts = elements(root, "startEvent")
    if len(starts) != 1:
        fail(f"expected exactly one start event as the queue trigger, found {len(starts)}")

    start_id = starts[0].attrib.get("id")
    if any(f.attrib.get("targetRef") == start_id for f in flows(root)):
        fail("something flows back into the start event — the performer loops instead of one item per instance")

    gateways = elements(root, "exclusiveGateway")
    if not gateways:
        fail("no exclusive gateway — the item outcome is never branched on")

    branched = max(
        len([f for f in flows(root) if f.attrib.get("sourceRef") == g.attrib.get("id")])
        for g in gateways
    )
    if branched < 3:
        fail(f"outcome gateway has {branched} branches, expected succeeded, failed and retry-later")

    ends = elements(root, "endEvent")
    if len(ends) < 3:
        fail(f"expected a distinct ending per outcome, found {len(ends)} end events")

    MSG = f"PASS: single queue-triggered start, {branched} outcome branches, {len(ends)} endings, no loop"

    if not root.findall(f".//{{{DI_NS}}}BPMNDiagram"):
        fail("no bpmndi:BPMNDiagram — the file will not import")

    print(MSG)


if __name__ == "__main__":
    main()
