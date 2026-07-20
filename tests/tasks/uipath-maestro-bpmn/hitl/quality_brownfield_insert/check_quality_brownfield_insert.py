#!/usr/bin/env python3
"""Brownfield HITL-insert check.

Asserts the agent spliced an Actions.HITL user task between Task_ComputeTotal and
End_1 surgically: every original element ID and script body preserved, the
original Compute->End edge removed, and Compute->HITL->End wired. Reuses shared
stdlib-ET helpers.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared.bpmn_check import (  # noqa: E402
    attr,
    elements,
    fail,
    has_uipath_extension,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

ORIGINAL_IDS = [
    "Process_OrderFulfillment",
    "Start_1",
    "Task_ValidateOrder",
    "Task_ComputeTotal",
    "End_1",
    "Flow_Start_Validate",
    "Flow_Validate_Compute",
    "Var_OrderId",
    "Var_Category",
    "Var_OrderTotal",
]
SCRIPT_MARKERS = ["validateOrder", "computeTotal"]


def main() -> None:
    path, root = parse_bpmn("OrderFulfillmentBpmn")

    ids = {attr(e, "id") for e in root.iter() if attr(e, "id")}
    dropped = [i for i in ORIGINAL_IDS if i not in ids]
    if dropped:
        fail(f"surgical edit dropped original element IDs: {dropped}")

    blob = ET.tostring(root, encoding="unicode")
    lost = [m for m in SCRIPT_MARKERS if m not in blob]
    if lost:
        fail(f"original script content not preserved (missing markers): {lost}")

    hitl = [t for t in elements(root, "userTask") if has_uipath_extension(t, "Actions.HITL")]
    if not hitl:
        fail("no Actions.HITL bpmn:userTask was inserted")
    hid = attr(hitl[0], "id")

    flows = elements(root, "sequenceFlow")
    if any(
        attr(f, "sourceRef") == "Task_ComputeTotal" and attr(f, "targetRef") == "End_1"
        for f in flows
    ):
        fail("original Task_ComputeTotal->End_1 edge still present; HITL was not spliced in")

    if not any(
        attr(f, "sourceRef") == "Task_ComputeTotal" and attr(f, "targetRef") == hid for f in flows
    ):
        fail("no sequence flow from Task_ComputeTotal into the inserted HITL task")

    if not any(attr(f, "sourceRef") == hid and attr(f, "targetRef") == "End_1" for f in flows):
        fail("inserted HITL task does not flow to the original End_1 event")

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} spliced the HITL gate in surgically, preserving original structure")


if __name__ == "__main__":
    main()
