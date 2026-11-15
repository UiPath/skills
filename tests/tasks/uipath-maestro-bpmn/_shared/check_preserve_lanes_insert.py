#!/usr/bin/env python3
"""Insert a step into a pooled, laned, colored process without re-laying it out.

A new node must sit between Task_Pay and Task_Archive, belong to a lane, have a
shape inside that lane's bounds that overlaps no other node, and the diagram the
user arranged must survive.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import parse_bpmn, require_di_for_visible_elements, require_sequence_integrity  # noqa: E402
from _shared.edit_check import (  # noqa: E402
    _bounds,
    _shapes,
    assert_diagram_preserved,
    assert_no_orphan_di,
    elements_local,
    fail,
    flow_node_ids,
    has_flow,
    load_original,
    local,
)


def _overlaps(a, b) -> bool:
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def main() -> None:
    _path, edited = parse_bpmn("ExpenseClaim")
    original = load_original("edit/preserve_lanes_insert", "ExpenseClaim.bpmn")

    added = flow_node_ids(edited) - flow_node_ids(original)
    inserted = [i for i in added if has_flow(edited, "Task_Pay", i) and has_flow(edited, i, "Task_Archive")]
    if len(inserted) != 1:
        fail(f"expected one new node between Task_Pay and Task_Archive, found {inserted or 'none'}")
    node = inserted[0]
    if has_flow(edited, "Task_Pay", "Task_Archive"):
        fail("original direct flow Task_Pay -> Task_Archive was not rewired")

    lane = next(
        (l for l in elements_local(edited, "lane")
         if any(local(r.tag) == "flowNodeRef" and (r.text or "").strip() == node for r in l)),
        None,
    )
    if lane is None:
        fail(f"new node {node!r} is not in any lane")

    assert_diagram_preserved(original, edited)
    shapes = _shapes(edited)
    if node not in shapes:
        fail(f"new node {node!r} has no diagram shape")
    box, lane_box = _bounds(shapes[node]), _bounds(shapes[lane.attrib["id"]])
    if not (box[0] >= lane_box[0] and box[1] >= lane_box[1]
            and box[0] + box[2] <= lane_box[0] + lane_box[2] and box[1] + box[3] <= lane_box[1] + lane_box[3]):
        fail(f"new node {node!r} is drawn outside its lane {lane.attrib['id']!r}")
    containers = {e.attrib.get("id") for e in elements_local(edited, "lane") + elements_local(edited, "participant")}
    for other, shape in shapes.items():
        if other not in (node, *containers) and _overlaps(box, _bounds(shape)):
            fail(f"new node {node!r} overlaps {other!r}")

    require_sequence_integrity(edited)
    require_di_for_visible_elements(edited)
    assert_no_orphan_di(edited)
    print(f"OK: {node} inserted in lane {lane.attrib['id']}, user diagram preserved")


if __name__ == "__main__":
    main()
