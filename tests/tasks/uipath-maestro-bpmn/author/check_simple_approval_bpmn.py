#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    has_uipath_extension,
    one_or_more,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)


def main() -> None:
    path, root = parse_bpmn("ExpenseApprovalBpmn")

    agent_jobs = [
        task
        for task in elements(root, "serviceTask")
        if has_uipath_extension(task, "Orchestrator.StartAgentJob")
    ]
    if not agent_jobs:
        fail("missing bpmn:serviceTask with Orchestrator.StartAgentJob uipath:activity shell")

    queue_sends = [
        task
        for task in elements(root, "sendTask")
        if has_uipath_extension(task, "Orchestrator.CreateQueueItem")
    ]
    if not queue_sends:
        fail("missing bpmn:sendTask with Orchestrator.CreateQueueItem uipath:activity shell")

    exclusive = one_or_more(root, "exclusiveGateway")
    if not any(attr(gateway, "default") for gateway in exclusive):
        fail("exclusive gateway missing a default sequence-flow reference")

    flows = one_or_more(root, "sequenceFlow")
    if not any(flow.find("bpmn:conditionExpression", NS) is not None for flow in flows):
        fail("missing conditional sequence flow on the gateway branches")

    scripts = elements(root, "scriptTask")
    if not scripts:
        fail("missing bpmn:scriptTask")
    script_task = scripts[0]
    # The script payload must come from the BPMN.ScriptTask registry template:
    # a uipath:mapping carrying uipath:type value="BPMN.ScriptTask". Do NOT
    # assert hand-made scriptFormat / uipath:scriptVersion attributes — those
    # are not part of the registry template.
    if not has_uipath_extension(script_task, "BPMN.ScriptTask"):
        fail("script task must use the BPMN.ScriptTask registry template (uipath:mapping/uipath:type)")

    process = root.find("bpmn:process", NS)
    if process is None:
        fail("missing bpmn:process element")
    variable_names = {
        var.attrib.get("name")
        for var in process.findall("bpmn:extensionElements/uipath:variables/*", NS)
        if var.attrib.get("name")
    }
    for required in ("expenseId", "amount", "decision"):
        if required not in variable_names:
            fail(f"missing root variable named {required!r}")

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} contains the documented simple approval BPMN shape")


if __name__ == "__main__":
    main()
