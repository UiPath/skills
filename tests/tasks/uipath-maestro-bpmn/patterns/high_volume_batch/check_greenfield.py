#!/usr/bin/env python3
"""Grades high-volume-batch: per-item isolation in a multi-instance container,
aggregation once the block completes, and a summary on both outcomes."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from bpmn_assertions import BPMN_NS, elements, fail, load_bpmn  # noqa: E402

DI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
BPMN = "InvoiceBatch/InvoiceBatch.bpmn"


def flows(root):
    return root.findall(f".//{{{BPMN_NS}}}sequenceFlow")


def main() -> None:
    root = load_bpmn(BPMN)
    subs = [
        s for s in elements(root, "subProcess")
        if s.find(f"./{{{BPMN_NS}}}multiInstanceLoopCharacteristics") is not None
    ]
    if not subs:
        fail("no subProcess carries multiInstanceLoopCharacteristics — items are not isolated per instance")

    sub_id = subs[0].attrib.get("id")
    gateways = elements(root, "exclusiveGateway")
    if not gateways:
        fail("no exclusive gateway — the run has no policy verdict")

    # Aggregation and the summary both sit between the block and the verdict:
    # the gateway must not be the container's immediate successor.
    after = {f.attrib.get("targetRef") for f in flows(root) if f.attrib.get("sourceRef") == sub_id}
    gateway_ids = {g.attrib.get("id") for g in gateways}
    if after & gateway_ids:
        fail("the policy gateway directly follows the multi-instance block — nothing aggregates or reports first")

    ends = elements(root, "endEvent")
    if len(ends) < 2:
        fail(f"expected completed and failed outcomes, found {len(ends)} end events")

    MSG = f"PASS: multi-instance block {sub_id}, aggregation before the verdict, {len(ends)} outcomes"

    if not root.findall(f".//{{{DI_NS}}}BPMNDiagram"):
        fail("no bpmndi:BPMNDiagram — the file will not import")

    print(MSG)


if __name__ == "__main__":
    main()
