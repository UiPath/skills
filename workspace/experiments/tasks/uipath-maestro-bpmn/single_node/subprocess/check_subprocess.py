#!/usr/bin/env python3
"""Structural check for the subprocess / call-activity port (Flow Subflow analogue).

Asserts the logic is encapsulated in a container: either an embedded
bpmn:subProcess with its own nested start event, end event, and at least one
inner activity, or a bpmn:callActivity. Verifies the container (and its inner
nodes) carry diagram shapes and that all sequence flows resolve.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)

INNER_ACTIVITY = ("task", "scriptTask", "serviceTask", "userTask", "businessRuleTask", "sendTask", "receiveTask")


def main() -> None:
    path, root = parse_bpmn("SubflowDemo")

    subprocesses = elements(root, "subProcess")
    call_activities = elements(root, "callActivity")
    if not subprocesses and not call_activities:
        fail("no bpmn:subProcess or bpmn:callActivity — logic is not encapsulated in a subflow")

    shaped = {s.attrib.get("bpmnElement") for s in root.findall(".//bpmndi:BPMNShape", NS)}

    if subprocesses:
        sp = subprocesses[0]
        sp_id = attr(sp, "id")
        if sp_id not in shaped:
            fail(f"subProcess {sp_id} has no BPMNShape (invisible on the canvas)")
        nested_start = sp.findall("bpmn:startEvent", NS)
        nested_end = sp.findall("bpmn:endEvent", NS)
        nested_acts = [a for k in INNER_ACTIVITY for a in sp.findall(f"bpmn:{k}", NS)]
        if not nested_start:
            fail(f"subProcess {sp_id} has no nested start event")
        if not nested_end:
            fail(f"subProcess {sp_id} has no nested end event")
        if not nested_acts:
            fail(f"subProcess {sp_id} has no inner activity (nothing encapsulated)")
    else:
        ca_id = attr(call_activities[0], "id")
        if ca_id not in shaped:
            fail(f"callActivity {ca_id} has no BPMNShape (invisible on the canvas)")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    kind = "subProcess" if subprocesses else "callActivity"
    print(f"OK: {path} encapsulates logic in a {kind} with a diagram shape")


if __name__ == "__main__":
    main()
