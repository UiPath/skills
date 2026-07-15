#!/usr/bin/env python3
"""Remove-node edit check.

Task_Enrich must be deleted, the sequence flow healed (Task_Fetch -> Task_Route),
orphaned DI removed, and the surrounding nodes / preserve-only payloads kept.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared.bpmn_check import parse_bpmn, require_di_for_visible_elements, require_sequence_integrity  # noqa: E402
from _shared.edit_check import (  # noqa: E402
    assert_config_preserved,
    assert_id_absent,
    assert_no_orphan_di,
    assert_uipath_preserved,
    fail,
    flows,
    has_flow,
    load_original,
)


def main() -> None:
    _path, edited = parse_bpmn("ShipmentReview")
    original = load_original(__file__, "ShipmentReview.bpmn")

    assert_id_absent(edited, "Task_Enrich")
    for fid, source, target in flows(edited):
        if "Task_Enrich" in (source, target):
            fail(f"sequence flow {fid!r} still references the removed Task_Enrich")

    if not has_flow(edited, "Task_Fetch", "Task_Route"):
        fail("flow not healed: expected a direct Task_Fetch -> Task_Route flow")

    assert_config_preserved(original, edited, ["Start_1", "Task_Fetch", "Task_Route", "End_1"])
    assert_uipath_preserved(original, edited, "migrationVersion")
    assert_uipath_preserved(original, edited, "caseManagement")
    assert_uipath_preserved(original, edited, "variables")

    require_sequence_integrity(edited)
    require_di_for_visible_elements(edited)
    assert_no_orphan_di(edited)
    print("OK: Task_Enrich removed, flow healed, DI clean, untouched content preserved")


if __name__ == "__main__":
    main()
