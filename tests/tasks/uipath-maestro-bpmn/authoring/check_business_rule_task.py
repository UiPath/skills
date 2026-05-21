#!/usr/bin/env python3
"""Assert the generated BPMN uses a real businessRuleTask wrapper."""

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
    variable_ids,
)

PROJECT = Path("BusinessRuleDecision/BusinessRuleDecision")
BPMN_NAME = "BusinessRuleDecision.bpmn"


def main() -> None:
    root = load_bpmn(str(PROJECT / BPMN_NAME))
    task = one_element(root, "businessRuleTask")

    if activity_type(task) != "Orchestrator.BusinessRules":
        fail(
            "businessRuleTask must contain uipath:activity type Orchestrator.BusinessRules"
        )
    for service_task in elements(root, "serviceTask"):
        if activity_type(service_task) == "Orchestrator.BusinessRules":
            fail("Orchestrator.BusinessRules must not be modeled as bpmn:serviceTask")

    if len(mapping_inputs(task)) < 1:
        fail("businessRuleTask should map declared fact inputs")
    outputs = mapping_outputs(task)
    if len(outputs) < 1:
        fail("businessRuleTask should map rule outputs")

    declared = variable_ids(root)
    output_targets = {
        out.attrib.get("var") or out.attrib.get("target") for out in outputs
    }
    missing = sorted(
        target for target in output_targets if target and target not in declared
    )
    if missing:
        fail(f"rule outputs target undeclared variables: {missing}")

    if not elements(root, "exclusiveGateway"):
        fail("business rule outcome should route through an exclusive gateway")
    assert_has_shape(root, task.attrib["id"])

    start = one_element(root, "startEvent")
    assert_package_lifecycle(PROJECT, BPMN_NAME, start.attrib["id"])
    print("OK: businessRuleTask wrapper and package lifecycle are present")


if __name__ == "__main__":
    main()
