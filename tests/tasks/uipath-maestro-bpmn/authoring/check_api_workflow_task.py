#!/usr/bin/env python3
"""Assert the generated BPMN uses the API workflow service-task contract."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_assertions import (  # noqa: E402
    activity_type,
    assert_has_shape,
    assert_package_lifecycle,
    elements,
    fail,
    load_bpmn,
    mapping_inputs,
    mapping_outputs,
    one_element,
    variable_names,
)

PROJECT = Path("ApiWorkflowDispatch/ApiWorkflowDispatch")
BPMN_NAME = "ApiWorkflowDispatch.bpmn"
EXPECTED_TYPE = "Orchestrator.ExecuteApiWorkflowAsync"


def main() -> None:
    root = load_bpmn(str(PROJECT / BPMN_NAME))
    service_tasks = [
        task for task in elements(root, "serviceTask") if activity_type(task) == EXPECTED_TYPE
    ]
    if len(service_tasks) != 1:
        fail(f"expected exactly one serviceTask with {EXPECTED_TYPE}, found {len(service_tasks)}")
    task = service_tasks[0]

    wrong_wrappers = []
    for kind in ("businessRuleTask", "callActivity", "scriptTask", "task"):
        wrong_wrappers.extend(
            elem.attrib.get("id", kind)
            for elem in elements(root, kind)
            if activity_type(elem) == EXPECTED_TYPE
        )
    if wrong_wrappers:
        fail(f"{EXPECTED_TYPE} used on wrong BPMN wrapper(s): {wrong_wrappers}")

    if len(mapping_inputs(task)) < 1:
        fail("API workflow task should map a request input")
    outputs = mapping_outputs(task)
    if len(outputs) < 2:
        fail("API workflow task should map invocation/status/result outputs")

    declared = variable_names(root)
    output_targets = {out.attrib.get("var") or out.attrib.get("target") for out in outputs}
    missing = sorted(target for target in output_targets if target and target not in declared)
    if missing:
        fail(f"API workflow outputs target undeclared variables: {missing}")

    boundary_events = elements(root, "boundaryEvent")
    if not any(event.attrib.get("attachedToRef") == task.attrib["id"] for event in boundary_events):
        fail("API workflow serviceTask should have an attached boundary error path")
    assert_has_shape(root, task.attrib["id"])

    start = one_element(root, "startEvent")
    assert_package_lifecycle(PROJECT, BPMN_NAME, start.attrib["id"])
    print("OK: API workflow serviceTask wrapper and package lifecycle are present")


if __name__ == "__main__":
    main()
