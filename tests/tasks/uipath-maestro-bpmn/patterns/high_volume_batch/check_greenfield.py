#!/usr/bin/env python3
"""Grades high-volume-batch: per-item isolation in a multi-instance container,
aggregation once the block completes, and a summary on both outcomes."""

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
from graph import ids, reachable, reaches  # noqa: E402

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

    # Absence of a direct edge proves nothing on its own — a dead-end branch or an
    # unrelated gateway elsewhere would satisfy it. Require a real path from the
    # block to a verdict gateway, through at least two distinct activities.
    gateway_ids = {g.attrib.get("id") for g in gateways}
    downstream = reachable(root, sub_id)
    verdicts = [g for g in gateway_ids & downstream]
    if not verdicts:
        fail(f"no gateway is reachable from {sub_id} — the block never reaches a verdict")

    verdict = verdicts[0]
    # A BPMN message throw is the native way to send a summary. Count it as
    # work on the path alongside task-shaped activities; requiring a sendTask
    # would grade an implementation detail rather than the requested behavior.
    message_throws = [
        event
        for event in elements(root, "intermediateThrowEvent")
        if event.find(f"./{{{BPMN_NS}}}messageEventDefinition") is not None
    ]
    work_ids = ids(
        elements(root, "serviceTask")
        + elements(root, "scriptTask")
        + elements(root, "sendTask")
        + message_throws
    )
    on_path = {
        n for n in downstream & work_ids
        if n != verdict and reaches(root, n, verdict)
    }
    if len(on_path) < 2:
        fail(
            f"only {len(on_path)} activity between the block and the verdict "
            f"({sorted(on_path)}) — aggregation and the summary do not both happen first"
        )

    ends = elements(root, "endEvent")
    if len(ends) < 2:
        fail(f"expected completed and failed outcomes, found {len(ends)} end events")

    MSG = f"PASS: multi-instance block {sub_id}, aggregation before the verdict, {len(ends)} outcomes"

    if not root.findall(f".//{{{DI_NS}}}BPMNDiagram"):
        fail("no bpmndi:BPMNDiagram — the file will not import")

    print(MSG)


if __name__ == "__main__":
    main()
