#!/usr/bin/env python3
"""Assert Build it replaced every outline box: no bare `bpmn:task` is left.

A draft skeleton validates as well as a built process, so `validate` alone cannot
tell that *Build it* did anything. A skeleton box is a `bpmn:task` whose only UiPath
data is variable plumbing: Studio Web reads a `bpmn:task` with no service type as
`BPMN.Variables` (PO.Frontend `src/services/serialization/bpmn-moddle.ts:1058`), and
`refresh` writes that `uipath:mapping`. A built step is a typed task, or a
`bpmn:task` carrying a `uipath:activity` or another service type (Studio Web
serializes some Integration Service activities as `bpmn:Task`, `bpmn-moddle.ts:38`).

Usage: check_no_outline_boxes.py <Name>
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import NS, fail, parse_bpmn  # noqa: E402

VARIABLES_ONLY = "BPMN.Variables"


def is_outline_box(task) -> bool:
    if task.find(".//uipath:activity", NS) is not None:
        return False
    types = {t.get("value") for t in task.iterfind(".//uipath:type", NS)}
    return types <= {VARIABLES_ONLY}


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: check_no_outline_boxes.py <Name>")
    path, root = parse_bpmn(sys.argv[1])
    left = [t.get("name") or t.get("id") for t in root.iter(f"{{{NS['bpmn']}}}task") if is_outline_box(t)]
    if left:
        fail(f"{path} still has outline boxes with no payload: {', '.join(left)}")
    print(f"OK: {path} has no outline box left")


if __name__ == "__main__":
    main()
