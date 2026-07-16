#!/usr/bin/env python3
"""Structural check for the interrupting error boundary event + recovery path.

Asserts:
  - an interrupting error boundary event (cancelActivity="true") whose
    attachedToRef resolves to a serviceTask;
  - its errorEventDefinition errorRef resolves to a bpmn:error with a non-empty
    errorCode (the ERROR_BOUNDARY_EVENT_REQUIRES_ERROR_CODE rule is satisfied);
  - the boundary routes to a downstream recovery node (outgoing flow);
  - at most one catch-all (no errorRef) error boundary event per task, guarding
    against MULTIPLE_CATCH_ALL_BOUNDARY_EVENTS_ON_TASK.
Reuses the shared uipath-maestro-bpmn check helpers.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)


def main() -> None:
    path, root = parse_bpmn("InvoiceServiceRecovery")

    codes = {attr(e, "id"): attr(e, "errorCode") for e in root.findall("bpmn:error", NS)}
    service_task_ids = {attr(t, "id") for t in elements(root, "serviceTask")}
    flows = elements(root, "sequenceFlow")

    error_boundaries = []
    for be in elements(root, "boundaryEvent"):
        if be.find("bpmn:errorEventDefinition", NS) is not None:
            error_boundaries.append(be)
    if not error_boundaries:
        fail("no error boundary event (boundaryEvent with a bpmn:errorEventDefinition)")

    # Guard against multiple catch-all error boundaries on the same task.
    catch_all_by_task = {}
    for be in error_boundaries:
        edef = be.find("bpmn:errorEventDefinition", NS)
        if not attr(edef, "errorRef"):
            task = attr(be, "attachedToRef")
            catch_all_by_task[task] = catch_all_by_task.get(task, 0) + 1
    for task, n in catch_all_by_task.items():
        if n > 1:
            fail(f"task {task!r} has {n} catch-all error boundary events (MULTIPLE_CATCH_ALL_BOUNDARY_EVENTS_ON_TASK)")

    valid = False
    for be in error_boundaries:
        be_id = attr(be, "id")
        edef = be.find("bpmn:errorEventDefinition", NS)
        ref = attr(edef, "errorRef")
        # Batch scenario: an interrupting boundary with a configured error code.
        if attr(be, "cancelActivity") != "true":
            continue
        if not ref:
            continue  # this scenario wants a configured (non catch-all) error
        attached = attr(be, "attachedToRef")
        if attached not in service_task_ids:
            fail(f"error boundary {be_id} attachedToRef {attached!r} is not a serviceTask")
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
        fail('no interrupting (cancelActivity="true") error boundary with a configured errorCode on a serviceTask routing to recovery')

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} has an interrupting error boundary with a configured code on a serviceTask routing to recovery")


if __name__ == "__main__":
    main()
