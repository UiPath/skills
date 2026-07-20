#!/usr/bin/env python3
"""Add-node edit check.

A new script task must be inserted between Task_Validate and Task_Notify, the old
direct flow rewired, and everything the agent did not author preserved.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared.bpmn_check import parse_bpmn, require_di_for_visible_elements, require_sequence_integrity  # noqa: E402
from _shared.edit_check import (  # noqa: E402
    assert_config_preserved,
    assert_no_orphan_di,
    assert_uipath_preserved,
    elements_local,
    fail,
    flow_node_ids,
    has_flow,
    load_original,
)


def main() -> None:
    _path, edited = parse_bpmn("OrderIntake")
    original = load_original(__file__, "OrderIntake.bpmn")

    added = flow_node_ids(edited) - flow_node_ids(original)
    inserted = [
        i for i in added
        if has_flow(edited, "Task_Validate", i) and has_flow(edited, i, "Task_Notify")
    ]
    if not inserted:
        fail("no new node wired between Task_Validate and Task_Notify")

    script_ids = {el.attrib.get("id") for el in elements_local(edited, "scriptTask")}
    if not any(i in script_ids for i in inserted):
        fail("the inserted node is not a bpmn:scriptTask")

    if has_flow(edited, "Task_Validate", "Task_Notify"):
        fail("original direct flow Task_Validate -> Task_Notify was not rewired")

    # Preserve what the agent did not author.
    assert_config_preserved(original, edited, ["Start_1", "Task_Validate", "Task_Notify", "End_1"])
    assert_uipath_preserved(original, edited, "migrationVersion")
    assert_uipath_preserved(original, edited, "caseManagement")
    assert_uipath_preserved(original, edited, "variables")

    require_sequence_integrity(edited)
    require_di_for_visible_elements(edited)
    assert_no_orphan_di(edited)
    print("OK: script node inserted, flow rewired, untouched content preserved")


if __name__ == "__main__":
    main()
