#!/usr/bin/env python3

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)


def has_typed_extension(element: ET.Element, extension_name: str, type_value: str) -> bool:
    ext = element.find("bpmn:extensionElements", NS)
    if ext is None:
        return False
    for payload in ext.findall(f"uipath:{extension_name}", NS):
        type_elem = payload.find("uipath:type", NS)
        if type_elem is not None and type_elem.attrib.get("value") == type_value:
            return True
    return False


def require_wrapper(root: ET.Element, wrapper: str, extension_name: str, type_value: str) -> None:
    matches = [
        elem
        for elem in elements(root, wrapper)
        if has_typed_extension(elem, extension_name, type_value)
    ]
    if not matches:
        fail(f"missing bpmn:{wrapper} with {type_value} uipath:{extension_name} shell")


def require_uipath_element(root: ET.Element, local_name: str, description: str) -> None:
    if not root.findall(f".//uipath:{local_name}", NS):
        fail(f"missing {description}")


def require_uipath_attr_value(
    root: ET.Element, local_name: str, attr_name: str, expected_value: str, description: str
) -> None:
    values = {elem.attrib.get(attr_name) for elem in root.findall(f".//uipath:{local_name}", NS)}
    if expected_value not in values:
        fail(f"missing {description}: {expected_value}")


def main() -> None:
    path, root = parse_bpmn("Contract")

    # Representative coverage for public-safe model-authored or preserve-only XML
    # shells. This is intentionally not an exhaustive mirror of
    # supported-elements.md: CLI-owned Intsvc.* enrichment is covered by the
    # integration-service fixture, while this fixture keeps one wait shell to
    # assert the model/CLI boundary stays explicit.
    expected_model_or_preserve_shells = [
        ("serviceTask", "activity", "Orchestrator.StartAgentJob"),
        ("serviceTask", "activity", "A2A.AgentExecution"),
        ("serviceTask", "activity", "Orchestrator.ExecuteApiWorkflowAsync"),
        ("businessRuleTask", "activity", "Orchestrator.BusinessRules"),
        ("sendTask", "activity", "Orchestrator.CreateQueueItem"),
        ("serviceTask", "activity", "Orchestrator.CreateAndWaitForQueueItem"),
        ("callActivity", "activity", "Orchestrator.StartAgenticProcess"),
        ("callActivity", "activity", "Orchestrator.StartAgenticProcessAsync"),
        ("callActivity", "activity", "Orchestrator.StartCaseMgmtProcess"),
        ("callActivity", "activity", "Orchestrator.StartCaseMgmtProcessAsync"),
        ("intermediateThrowEvent", "event", "Maestro.SendMessageEvent"),
        ("serviceTask", "activity", "Maestro.CasePlanScheduler"),
        ("serviceTask", "activity", "Maestro.CaseManagerGuardrails"),
        ("serviceTask", "activity", "Maestro.CaseRulesEvaluator"),
        ("receiveTask", "event", "Intsvc.WaitForEvent"),
    ]
    for wrapper, extension_name, type_value in expected_model_or_preserve_shells:
        require_wrapper(root, wrapper, extension_name, type_value)

    for version in {"5", "11", "11.5"}:
        require_uipath_attr_value(root, "migrationVersion", "version", version, "migration version")

    require_uipath_attr_value(
        root, "scriptVersion", "value", "v2", "preserved legacy scriptVersion"
    )
    require_uipath_element(root, "caseManagement", "preserve-only uipath:caseManagement payload")
    require_uipath_element(root, "Activity", "preserve-only generic uipath:Activity payload")

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} contains public-safe Maestro BPMN XML contract variants")


if __name__ == "__main__":
    main()
