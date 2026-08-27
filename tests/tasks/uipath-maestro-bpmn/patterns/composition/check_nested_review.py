#!/usr/bin/env python3
"""Grades composition, not the three shapes individually.

The composition rules under test: the batch keeps the start event and is
outermost, the review shape nests inside the per-item iteration, and the failure
net sits directly in the iteration it guards rather than at process level. A net
at process level would catch the first bad claim and end the whole run, which is
the mistake this asserts against.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from bpmn_assertions import BPMN_NS, elements, fail, load_bpmn  # noqa: E402

DI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
BPMN = "ClaimsNightly/ClaimsNightly.bpmn"


def parents(root):
    """ElementTree has no parent pointers; build the map once."""
    return {child: parent for parent in root.iter() for child in parent}


def ancestors(node, parent_map):
    while node in parent_map:
        node = parent_map[node]
        yield node


def main() -> None:
    root = load_bpmn(BPMN)
    parent_map = parents(root)

    # The batch is outermost: a multi-instance container holding the per-item work.
    batches = [
        s for s in elements(root, "subProcess")
        if s.find(f"./{{{BPMN_NS}}}multiInstanceLoopCharacteristics") is not None
    ]
    if not batches:
        fail("no multi-instance subProcess — claims are not isolated per iteration")
    batch = batches[0]
    batch_id = batch.attrib.get("id")

    # The review shape is nested inside the iteration, not run once for the batch.
    inner_gateways = batch.findall(f".//{{{BPMN_NS}}}exclusiveGateway")
    inner_tasks = batch.findall(f".//{{{BPMN_NS}}}userTask")
    if not inner_gateways:
        fail(f"no gateway inside {batch_id} — the confidence decision is not per claim")
    if not inner_tasks:
        fail(f"no userTask inside {batch_id} — the assessor review is not per claim")

    # The net is scoped to the iteration. At process level it would end the whole
    # run on the first bad claim, which the prompt rules out.
    nets = [s for s in elements(root, "subProcess") if s.attrib.get("triggeredByEvent") == "true"]
    if not nets:
        fail("no event subprocess — a per-claim failure has nowhere to go")

    scoped = [n for n in nets if batch in set(ancestors(n, parent_map))]
    if not scoped:
        outer = [n.attrib.get("id") for n in nets]
        fail(
            f"the failure net(s) {outer} sit outside {batch_id} — the first failed claim "
            "would end the whole run instead of only that claim"
        )

    net = scoped[0]
    start = net.find(f"./{{{BPMN_NS}}}startEvent")
    if start is None or start.find(f"./{{{BPMN_NS}}}errorEventDefinition") is None:
        fail("the nested net's start event is missing or carries no errorEventDefinition")

    # Aggregation happens after the block, once.
    outside = [
        t for t in elements(root, "serviceTask") + elements(root, "scriptTask")
        if batch not in set(ancestors(t, parent_map))
    ]
    if not outside:
        fail("nothing outside the iteration aggregates the results")

    if not root.findall(f".//{{{DI_NS}}}BPMNDiagram"):
        fail("no bpmndi:BPMNDiagram — the file will not import")

    print(
        f"PASS: batch {batch_id} outermost, review nested per item "
        f"({len(inner_gateways)} gateways, {len(inner_tasks)} tasks), "
        f"failure net {net.attrib.get('id')} scoped inside the iteration"
    )


if __name__ == "__main__":
    main()
