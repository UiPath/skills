#!/usr/bin/env python3
"""Structural check for the add-output edit task.

Verifies the agent added a second BPMN.Variables output named `category` to the
classifyOrder task while preserving the existing `risk` output, without adding or
removing nodes and while keeping every id and the diagram intact. Reuses the
shared uipath-maestro-bpmn check helpers (stdlib ET, same trust boundary as the
rest of the fixture corpus — input is locally authored, not untrusted).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)

EXPECTED_IDS = {
    "Event_start",
    "Activity_Classify",
    "Gateway_Route",
    "Activity_Review",
    "Activity_Approve",
    "Event_end",
}


def main() -> None:
    path, root = parse_bpmn("OrderTriage")

    ids = {attr(e, "id") for e in root.iter() if attr(e, "id")}
    if not EXPECTED_IDS.issubset(ids):
        fail(f"edit changed the node id set; missing: {sorted(EXPECTED_IDS - ids)}")

    # No nodes added or removed: the original three script tasks remain.
    script_tasks = elements(root, "scriptTask")
    if len(script_tasks) != 3:
        fail(f"expected the original 3 script tasks, found {len(script_tasks)}")

    classify = next((t for t in script_tasks if attr(t, "id") == "Activity_Classify"), None)
    if classify is None:
        fail("classifyOrder task (Activity_Classify) not found")

    outputs = classify.findall(".//uipath:output", NS)
    names = {attr(o, "name") for o in outputs}
    if "risk" not in names:
        fail(f"existing 'risk' output was not preserved on classifyOrder; outputs={sorted(names)}")
    if "category" not in names:
        fail(f"no 'category' output added to classifyOrder; outputs={sorted(names)}")

    # Diagram + reference integrity (importable on the canvas).
    require_di_for_visible_elements(root)
    require_sequence_integrity(root)

    print(f"OK: {path} classifyOrder now outputs risk + category")


if __name__ == "__main__":
    main()
