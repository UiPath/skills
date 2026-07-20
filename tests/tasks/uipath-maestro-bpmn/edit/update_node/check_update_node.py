#!/usr/bin/env python3
"""Update-node edit check.

The Task_Score script threshold must change from 500 to 1000, while the sibling
Task_Format and all other content stay byte-for-byte / structurally identical.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared.bpmn_check import parse_bpmn, require_di_for_visible_elements, require_sequence_integrity  # noqa: E402
from _shared.edit_check import (  # noqa: E402
    assert_no_orphan_di,
    assert_preserved,
    assert_uipath_preserved,
    by_id,
    fail,
    local,
    load_original,
)


def _script_text(task) -> str:
    for child in task:
        if local(child.tag) == "script":
            return child.text or ""
    return ""


def main() -> None:
    _path, edited = parse_bpmn("RiskScoring")
    original = load_original(__file__, "RiskScoring.bpmn")

    score = by_id(edited, "Task_Score")
    if score is None:
        fail("Task_Score is missing after the edit")
    body = _script_text(score)
    if "1000" not in body:
        fail("Task_Score script was not updated to the new threshold 1000")
    if "500" in body:
        fail("Task_Score script still contains the old threshold 500")

    # Sibling and endpoints must be untouched.
    assert_preserved(original, edited, ["Task_Format", "Start_1", "End_1"])
    assert_uipath_preserved(original, edited, "migrationVersion")
    assert_uipath_preserved(original, edited, "caseManagement")
    assert_uipath_preserved(original, edited, "variables")

    require_sequence_integrity(edited)
    require_di_for_visible_elements(edited)
    assert_no_orphan_di(edited)
    print("OK: Task_Score threshold updated, siblings untouched")


if __name__ == "__main__":
    main()
