#!/usr/bin/env python3
"""Group-to-subflow edit check.

Pick + Pack must be extracted into an embedded bpmn:subProcess (with a diagram
shape and nested script logic), while Task_Ship stays in the main flow and the
preserve-only payloads round-trip untouched.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared.bpmn_assertions import assert_has_shape  # noqa: E402
from _shared.bpmn_check import parse_bpmn, require_di_for_visible_elements, require_sequence_integrity  # noqa: E402
from _shared.edit_check import (  # noqa: E402
    assert_config_preserved,
    assert_no_orphan_di,
    assert_uipath_preserved,
    elements_local,
    fail,
    has_flow,
    load_original,
    local,
)


def main() -> None:
    _path, edited = parse_bpmn("Fulfillment")
    original = load_original(__file__, "Fulfillment.bpmn")

    subs = elements_local(edited, "subProcess")
    if not subs:
        fail("no bpmn:subProcess was created — the group was not extracted")

    # Script logic must live inside a subprocess now.
    nested_scripts = [
        el for sub in subs for el in sub.iter()
        if local(el.tag) == "scriptTask" and el is not sub
    ]
    if not nested_scripts:
        fail("the subprocess contains no nested script task — no logic was moved in")

    # Task_Ship must remain, outside any subprocess, still reaching the end.
    nested_ids = {el.attrib.get("id") for sub in subs for el in sub.iter() if el is not sub}
    if "Task_Ship" in nested_ids:
        fail("Task_Ship must stay in the main flow, not move into the subprocess")
    if not has_flow(edited, "Task_Ship", "End_1"):
        fail("Task_Ship no longer flows to End_1")

    # The subprocess must be importable (has a diagram shape).
    sub_id = subs[0].attrib.get("id")
    if not sub_id:
        fail("subprocess has no id")
    assert_has_shape(edited, sub_id)

    assert_config_preserved(original, edited, ["Task_Ship"])
    assert_uipath_preserved(original, edited, "migrationVersion")
    assert_uipath_preserved(original, edited, "caseManagement")

    require_sequence_integrity(edited)
    require_di_for_visible_elements(edited)
    assert_no_orphan_di(edited)
    print("OK: Pick/Pack extracted into a subprocess, Task_Ship preserved in main flow")


if __name__ == "__main__":
    main()
