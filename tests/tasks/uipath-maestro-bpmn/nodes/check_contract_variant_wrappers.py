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

    # Each node must use its registry `bpmnElement` and carry a registry-template
    # `uipath:*` payload whose `uipath:type value` matches the extension type.
    # Every (wrapper, extension, type) tuple below is grounded in the registry
    # bpmn-spec (maestro-sdk/src/manifest/bpmn-spec.json); no preserve-only,
    # migration, or non-registry types are asserted.
    expected_registry_wrappers = [
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
        ("serviceTask", "activity", "Maestro.CaseManagerGuardrails"),
        ("serviceTask", "activity", "Maestro.CaseRulesEvaluator"),
        ("receiveTask", "event", "Intsvc.WaitForEvent"),
    ]
    for wrapper, extension_name, type_value in expected_registry_wrappers:
        require_wrapper(root, wrapper, extension_name, type_value)

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} nodes use registry bpmnElement + registry-template payloads")


if __name__ == "__main__":
    main()
