#!/usr/bin/env python3
"""Assert Build it replaced every outline box and left no script step as bpmn:task.

A draft skeleton validates as well as a built process, so `validate` alone cannot
tell that *Build it* did anything. Two shapes fail:

- An outline box: a `bpmn:task` whose only UiPath data is a `BPMN.Variables` type
  with no output. Studio Web reads a `bpmn:task` with no service type that way
  (PO.Frontend `src/services/serialization/bpmn-moddle.ts:1058`), and a skeleton
  takes no `set` (draft-skeleton.md rule 1). A `.task(id, { set })` step writes a
  `uipath:output` and counts as built; so does a `bpmn:task` carrying a
  `uipath:activity` or another service type (`bpmn-moddle.ts:38`).
- A script step left as `bpmn:task`: `uip maestro bpmn merge` keeps the target's
  tag when the edit changes a box's type. Studio Web parses with stock
  `bpmn-moddle` (`bpmn-moddle-instance.ts:8`), where only `bpmn:ScriptTask` has a
  `script`, so the `<bpmn:script>` is dropped as unparsable content. The canvas
  writes `bpmn:scriptTask` for the same step.

Usage: check_no_outline_boxes.py <Name>
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import NS, fail, parse_bpmn  # noqa: E402

VARIABLES_ONLY = "BPMN.Variables"


def lost_script_type(task) -> bool:
    """A script step that kept the outline's `bpmn:task` tag."""
    return (
        bool(task.get("scriptFormat"))
        or task.find("bpmn:script", NS) is not None
        or task.find(".//uipath:scriptVersion", NS) is not None
    )


def is_outline_box(task) -> bool:
    if lost_script_type(task) or task.find(".//uipath:activity", NS) is not None:
        return False
    types = {t.get("value") for t in task.iterfind(".//uipath:type", NS)}
    return types <= {VARIABLES_ONLY} and task.find(".//uipath:output", NS) is None


def findings(root) -> tuple[list[str], list[str]]:
    """Labels of script steps left as bpmn:task, and of outline boxes."""
    tasks = list(root.iter(f"{{{NS['bpmn']}}}task"))
    label = lambda t: t.get("name") or t.get("id")  # noqa: E731
    return [label(t) for t in tasks if lost_script_type(t)], [label(t) for t in tasks if is_outline_box(t)]


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: check_no_outline_boxes.py <Name>")
    path, root = parse_bpmn(sys.argv[1])
    lost, left = findings(root)
    if lost:
        fail(f"{path} has script steps left as bpmn:task (merge kept the outline tag): {', '.join(lost)}")
    if left:
        fail(f"{path} still has outline boxes: {', '.join(left)}")
    print(f"OK: {path} has no outline box left")


if __name__ == "__main__":
    main()
