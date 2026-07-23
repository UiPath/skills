#!/usr/bin/env python3
"""Structural check for the low-code agent-job resource-node eval.

Grades that the published Agent Builder invocation is a bpmn:serviceTask carrying
the registry Orchestrator.StartAgentJob wrapper (not StartJob / not an IS
execution wrapper), binds a request input, and captures the agent response into a
declared process variable. Type/input/output are matched by uipath subtree search
so the check is robust to both wrapper styles the registry template and the skill
rules permit. Reuses the shared uipath-maestro-bpmn check helpers (stdlib ET).
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.bpmn_check import (  # noqa: E402
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

UIPATH_NS = "http://uipath.org/schema/bpmn"
TYPE_TOKEN = "Orchestrator.StartAgentJob"


def has_type(el: ET.Element, token: str) -> bool:
    return token in ET.tostring(el, encoding="unicode")


def uipath_children(task: ET.Element, local: str) -> list[ET.Element]:
    return task.findall(f".//{{{UIPATH_NS}}}{local}")


def variable_ids(root: ET.Element) -> set[str]:
    ids: set[str] = set()
    for var in root.findall(f".//{{{UIPATH_NS}}}variables/*"):
        vid = var.attrib.get("id")
        if vid:
            ids.add(vid)
    return ids


def main() -> None:
    path, root = parse_bpmn("ApproverCountAgent")

    if not elements(root, "startEvent"):
        fail("no start event")
    if not elements(root, "endEvent"):
        fail("no end event")

    agent_tasks = [t for t in elements(root, "serviceTask") if has_type(t, TYPE_TOKEN)]
    if not agent_tasks:
        fail(f"missing bpmn:serviceTask with {TYPE_TOKEN} wrapper")
    task = agent_tasks[0]

    # The flow port's discipline: a low-code agent must not be modeled as a plain
    # RPA job or an IS execution wrapper. StartJob is not a substring of
    # StartAgentJob, so a whole-token search is a safe wrong-wrapper guard.
    for kind in ("userTask", "sendTask", "scriptTask", "businessRuleTask", "callActivity", "task"):
        if any(has_type(e, TYPE_TOKEN) for e in elements(root, kind)):
            fail(f"{TYPE_TOKEN} used on wrong BPMN wrapper: bpmn:{kind}")

    if not uipath_children(task, "input"):
        fail("agent job task should bind at least one request input (JobArguments)")

    outputs = uipath_children(task, "output")
    if not outputs:
        fail("agent job task should capture the agent response as an output")
    declared = variable_ids(root)
    if not declared:
        fail("no process variables declared (expected a BPMN.Variables mapping)")
    output_targets = {o.attrib.get("var") or o.attrib.get("target") for o in outputs}
    if not any(t and t in declared for t in output_targets):
        fail(
            f"agent job output must bind to a declared variable; "
            f"outputs={sorted(t for t in output_targets if t)} declared={sorted(declared)}"
        )

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} wires Orchestrator.StartAgentJob with bound input and output variable")


if __name__ == "__main__":
    main()
