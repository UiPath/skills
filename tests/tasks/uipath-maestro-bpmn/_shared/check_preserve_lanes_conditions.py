#!/usr/bin/env python3
"""Fill missing gateway conditions on a pooled, laned, colored process.

Every outgoing flow of each exclusive gateway must carry a condition (or be the
gateway's default), and the diagram the user arranged must survive: pool and lane
shapes, the plane's collaboration target, colors, box sizes and placement.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import parse_bpmn, require_di_for_visible_elements, require_sequence_integrity  # noqa: E402
from _shared.edit_check import (  # noqa: E402
    assert_diagram_preserved,
    assert_no_orphan_di,
    elements_local,
    fail,
    flow_node_ids,
    load_original,
    local,
)


def main() -> None:
    _path, edited = parse_bpmn("ExpenseClaim")
    original = load_original("edit/preserve_lanes_conditions", "ExpenseClaim.bpmn")

    if flow_node_ids(edited) != flow_node_ids(original):
        fail("nodes were added or removed; the request only asked for conditions")

    for gateway in elements_local(edited, "exclusiveGateway"):
        default = gateway.attrib.get("default")
        for flow in elements_local(edited, "sequenceFlow"):
            if flow.attrib.get("sourceRef") != gateway.attrib.get("id") or flow.attrib.get("id") == default:
                continue
            if not any(local(c.tag) == "conditionExpression" and (c.text or "").strip() for c in flow):
                fail(f"flow {flow.attrib.get('id')!r} out of {gateway.attrib.get('id')!r} still has no condition")

    assert_diagram_preserved(original, edited)
    require_sequence_integrity(edited)
    require_di_for_visible_elements(edited)
    assert_no_orphan_di(edited)
    print("OK: gateway conditions filled, user diagram preserved")


if __name__ == "__main__":
    main()
