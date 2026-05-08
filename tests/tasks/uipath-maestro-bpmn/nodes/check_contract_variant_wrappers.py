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


def main() -> None:
    path, root = parse_bpmn("Contract")

    expected = [
        ("serviceTask", "activity", "Orchestrator.StartAgentJob"),
        ("serviceTask", "activity", "A2A.AgentExecution"),
        ("serviceTask", "activity", "Orchestrator.ExecuteApiWorkflowAsync"),
        ("businessRuleTask", "activity", "Orchestrator.BusinessRules"),
        ("sendTask", "activity", "Orchestrator.CreateQueueItem"),
        ("serviceTask", "activity", "Orchestrator.CreateAndWaitForQueueItem"),
        ("callActivity", "activity", "Orchestrator.StartAgenticProcess"),
        ("callActivity", "activity", "Orchestrator.StartCaseMgmtProcess"),
        ("receiveTask", "event", "Intsvc.WaitForEvent"),
    ]
    for wrapper, extension_name, type_value in expected:
        require_wrapper(root, wrapper, extension_name, type_value)

    migration_versions = {
        elem.attrib.get("version") for elem in root.findall(".//uipath:migrationVersion", NS)
    }
    for version in {"5", "11", "11.5"}:
        if version not in migration_versions:
            fail(f"missing migration version: {version}")

    script_versions = {
        elem.attrib.get("value") for elem in root.findall(".//uipath:scriptVersion", NS)
    }
    if "v2" not in script_versions:
        fail("missing preserved legacy scriptVersion v2")
    if not root.findall(".//uipath:caseManagement", NS):
        fail("missing preserve-only uipath:caseManagement payload")
    if not root.findall(".//uipath:Activity", NS):
        fail("missing preserve-only generic uipath:Activity payload")

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} contains public-safe Maestro BPMN XML contract variants")


if __name__ == "__main__":
    main()
