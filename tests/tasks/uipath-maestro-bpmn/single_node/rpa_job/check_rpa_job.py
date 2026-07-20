#!/usr/bin/env python3
"""Structural check for the RPA-job resource-node eval.

Grades the differentiator over the wrapper-presence eval: the RPA invocation is a
bpmn:serviceTask carrying the registry Orchestrator.StartJob wrapper, it binds a
request input, and it captures the job response into a *declared* process
variable. Reuses the shared uipath-maestro-bpmn check helpers (stdlib ET, same
trust boundary as the rest of the fixture corpus — locally authored input).
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.bpmn_assertions import mapping_inputs, mapping_outputs, variable_ids  # noqa: E402
from _shared.bpmn_check import (  # noqa: E402
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

TYPE_TOKEN = "Orchestrator.StartJob"


def has_type(task: ET.Element, token: str) -> bool:
    return token in ET.tostring(task, encoding="unicode")


def main() -> None:
    path, root = parse_bpmn("InvoiceExtractionRpa")

    if not elements(root, "startEvent"):
        fail("no start event")
    if not elements(root, "endEvent"):
        fail("no end event")

    rpa_tasks = [t for t in elements(root, "serviceTask") if has_type(t, TYPE_TOKEN)]
    if not rpa_tasks:
        fail(f"missing bpmn:serviceTask with {TYPE_TOKEN} wrapper")
    task = rpa_tasks[0]

    # Wrong-wrapper guard: StartJob must not ride a non-serviceTask host.
    for kind in ("userTask", "sendTask", "scriptTask", "businessRuleTask", "callActivity", "task"):
        if any(has_type(e, TYPE_TOKEN) for e in elements(root, kind)):
            fail(f"{TYPE_TOKEN} used on wrong BPMN wrapper: bpmn:{kind}")

    if len(mapping_inputs(task)) < 1:
        fail("RPA job task should bind at least one request input (JobArguments)")

    outputs = mapping_outputs(task)
    if not outputs:
        fail("RPA job task should capture the job response as an output")
    declared = variable_ids(root)
    if not declared:
        fail("no process variables declared (expected a BPMN.Variables mapping)")
    output_targets = {o.attrib.get("var") or o.attrib.get("target") for o in outputs}
    bound = [t for t in output_targets if t and t in declared]
    if not bound:
        fail(
            f"RPA job output must bind to a declared variable; "
            f"outputs={sorted(t for t in output_targets if t)} declared={sorted(declared)}"
        )

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} wires Orchestrator.StartJob with bound input and output variable")


if __name__ == "__main__":
    main()
