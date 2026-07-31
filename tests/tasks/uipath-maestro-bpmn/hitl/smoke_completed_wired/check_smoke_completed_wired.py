#!/usr/bin/env python3
"""HITL completion wiring check.

Asserts the Actions.HITL user task's completion is wired to a downstream step
(not straight to an end event) and that the step reaches an end event. Reuses
the shared uipath-maestro-bpmn stdlib-ET helpers; input is locally authored.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared.bpmn_check import (  # noqa: E402
    attr,
    elements,
    fail,
    has_uipath_extension,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

DOWNSTREAM = {
    "task",
    "serviceTask",
    "sendTask",
    "receiveTask",
    "scriptTask",
    "businessRuleTask",
    "userTask",
    "callActivity",
}


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def main() -> None:
    path, root = parse_bpmn("PurchaseApprovalBpmn")

    hitl = [t for t in elements(root, "userTask") if has_uipath_extension(t, "Actions.HITL")]
    if not hitl:
        fail("no bpmn:userTask carrying an Actions.HITL uipath:activity shell")
    hid = attr(hitl[0], "id")

    flows = elements(root, "sequenceFlow")
    outgoing = [f for f in flows if attr(f, "sourceRef") == hid]
    if not outgoing:
        fail(f"HITL task {hid} has no outgoing sequence flow (completion not wired)")

    kind = {attr(e, "id"): local(e.tag) for e in root.iter() if attr(e, "id")}
    downstream_targets = [
        attr(f, "targetRef") for f in outgoing if kind.get(attr(f, "targetRef")) in DOWNSTREAM
    ]
    if not downstream_targets:
        seen = [kind.get(attr(f, "targetRef")) for f in outgoing]
        fail(f"HITL completion flows to {seen}, not to a downstream task")

    end_ids = {attr(e, "id") for e in elements(root, "endEvent")}

    def reaches_end(start: str, seen: set[str] | None = None) -> bool:
        seen = seen or set()
        if start in seen:
            return False
        seen.add(start)
        if start in end_ids:
            return True
        return any(
            attr(f, "sourceRef") == start and reaches_end(attr(f, "targetRef"), seen)
            for f in flows
        )

    if not any(reaches_end(t) for t in downstream_targets):
        fail("the downstream step after HITL does not reach an end event")

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} wires HITL completion to a downstream step that reaches an end event")


if __name__ == "__main__":
    main()
