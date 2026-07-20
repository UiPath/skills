#!/usr/bin/env python3
"""Structural check for the interrupting error boundary event + recovery path.

Asserts:
  - an interrupting error boundary event (cancelActivity="true") whose
    attachedToRef resolves to a task-like activity (serviceTask, sendTask,
    userTask, scriptTask, ... — registry templates host service calls on
    different task kinds, e.g. Intsvc.UnifiedHttpRequest on bpmn:sendTask);
  - its errorEventDefinition errorRef resolves to a bpmn:error with a non-empty
    errorCode (the ERROR_BOUNDARY_EVENT_REQUIRES_ERROR_CODE rule is satisfied);
  - the boundary routes to a downstream recovery node (outgoing flow);
  - at most one catch-all (no errorRef) error boundary event per task, guarding
    against MULTIPLE_CATCH_ALL_BOUNDARY_EVENTS_ON_TASK.

Element lookups are case-insensitive on the BPMN local name: registry
xmlTemplates emit capitalized element names (bpmn:SendTask,
bpmn:IntermediateCatchEvent, ...) while hand-authored structural BPMN uses the
lowercase-camel spec names. Reuses the shared uipath-maestro-bpmn check helpers.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)

BPMN_NS = NS["bpmn"]

ACTIVITY_KINDS = {
    "task", "servicetask", "sendtask", "receivetask", "scripttask",
    "usertask", "businessruletask", "callactivity", "subprocess",
}


def els(root: ET.Element, kind: str) -> list[ET.Element]:
    """Case-insensitive BPMN element lookup by local name."""
    prefix = "{" + BPMN_NS + "}"
    kl = kind.lower()
    return [
        el for el in root.iter()
        if el.tag.startswith(prefix) and el.tag[len(prefix):].lower() == kl
    ]


def child(el: ET.Element, kind: str) -> ET.Element | None:
    prefix = "{" + BPMN_NS + "}"
    kl = kind.lower()
    for c in el:
        if c.tag.startswith(prefix) and c.tag[len(prefix):].lower() == kl:
            return c
    return None


def main() -> None:
    path, root = parse_bpmn("InvoiceServiceRecovery")

    codes = {attr(e, "id"): attr(e, "errorCode") for e in els(root, "error")}
    activity_ids = set()
    for kind in ACTIVITY_KINDS:
        for t in els(root, kind):
            activity_ids.add(attr(t, "id"))
    flows = els(root, "sequenceFlow")

    error_boundaries = [be for be in els(root, "boundaryEvent") if child(be, "errorEventDefinition") is not None]
    if not error_boundaries:
        fail("no error boundary event (boundaryEvent with a bpmn:errorEventDefinition)")

    # Guard against multiple catch-all error boundaries on the same task.
    catch_all_by_task = {}
    for be in error_boundaries:
        edef = child(be, "errorEventDefinition")
        if not attr(edef, "errorRef"):
            task = attr(be, "attachedToRef")
            catch_all_by_task[task] = catch_all_by_task.get(task, 0) + 1
    for task, n in catch_all_by_task.items():
        if n > 1:
            fail(f"task {task!r} has {n} catch-all error boundary events (MULTIPLE_CATCH_ALL_BOUNDARY_EVENTS_ON_TASK)")

    valid = False
    for be in error_boundaries:
        be_id = attr(be, "id")
        edef = child(be, "errorEventDefinition")
        ref = attr(edef, "errorRef")
        # Batch scenario: an interrupting boundary with a configured error code.
        if attr(be, "cancelActivity") != "true":
            continue
        if not ref:
            continue  # this scenario wants a configured (non catch-all) error
        attached = attr(be, "attachedToRef")
        if attached not in activity_ids:
            fail(f"error boundary {be_id} attachedToRef {attached!r} is not a task-like activity")
        if ref not in codes:
            fail(f"error boundary {be_id} errorRef {ref!r} does not resolve to a declared bpmn:error")
        if not codes[ref].strip():
            fail(f"bpmn:error {ref!r} on boundary {be_id} has no errorCode (ERROR_BOUNDARY_EVENT_REQUIRES_ERROR_CODE)")
        outgoing = [f for f in flows if attr(f, "sourceRef") == be_id]
        if not outgoing:
            fail(f"error boundary {be_id} has no outgoing flow to a recovery path")
        shaped = {s.attrib.get("bpmnElement") for s in root.findall(".//bpmndi:BPMNShape", NS)}
        if be_id not in shaped:
            fail(f"error boundary {be_id} has no BPMNShape")
        valid = True
    if not valid:
        fail('no interrupting (cancelActivity="true") error boundary with a configured errorCode on an activity routing to recovery')

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} has an interrupting error boundary with a configured code on an activity routing to recovery")


if __name__ == "__main__":
    main()
