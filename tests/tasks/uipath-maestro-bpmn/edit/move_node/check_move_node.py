#!/usr/bin/env python3
"""Move/reorder edit check.

Task_Welcome must be reordered ahead of Task_Create, so the sequence becomes
Start -> Task_Welcome -> Task_Create -> End, with both tasks' payloads preserved.
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
    fail,
    has_flow,
    load_original,
)


def main() -> None:
    _path, edited = parse_bpmn("Onboarding")
    original = load_original(__file__, "Onboarding.bpmn")

    if not has_flow(edited, "Start_1", "Task_Welcome"):
        fail("expected reordered flow Start_1 -> Task_Welcome")
    if not has_flow(edited, "Task_Welcome", "Task_Create"):
        fail("expected reordered flow Task_Welcome -> Task_Create")
    if not has_flow(edited, "Task_Create", "End_1"):
        fail("expected reordered flow Task_Create -> End_1")
    if has_flow(edited, "Start_1", "Task_Create"):
        fail("flow still starts with Task_Create; nodes were not reordered")

    assert_config_preserved(original, edited, ["Start_1", "Task_Create", "Task_Welcome", "End_1"])
    assert_uipath_preserved(original, edited, "migrationVersion")
    assert_uipath_preserved(original, edited, "caseManagement")
    assert_uipath_preserved(original, edited, "variables")

    require_sequence_integrity(edited)
    require_di_for_visible_elements(edited)
    assert_no_orphan_di(edited)
    print("OK: nodes reordered, flows rewired, payloads preserved")


if __name__ == "__main__":
    main()
