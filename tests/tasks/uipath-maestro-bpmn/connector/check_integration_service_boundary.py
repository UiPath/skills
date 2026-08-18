#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_assertions import assert_generated_project_scaffold  # noqa: E402
from _shared.bpmn_check import (  # noqa: E402
    NS,
    elements,
    fail,
    has_uipath_extension,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

PROJECT = Path("SlackDigestBoundaryBpmnSolution/SlackDigestBoundaryBpmn")
BPMN_NAME = "SlackDigestBoundaryBpmn.bpmn"


def main() -> None:
    path, root = parse_bpmn("SlackDigestBoundaryBpmn")
    if Path(path) != PROJECT / BPMN_NAME:
        fail(f"BPMN source must be created at {PROJECT / BPMN_NAME}")
    wrappers = [*elements(root, "sendTask"), *elements(root, "serviceTask")]
    if not any(has_uipath_extension(task, "Intsvc.") for task in wrappers):
        fail("missing draft Integration Service uipath:activity shell")
    require_no_private_connector_values(root)
    starts = elements(root, "startEvent")
    if len(starts) != 1:
        fail(f"expected exactly one manual start event, found {len(starts)}")
    entry_point = starts[0].find("bpmn:extensionElements/uipath:entryPointId", NS)
    if entry_point is None or not entry_point.attrib.get("value"):
        fail("manual start must declare uipath:entryPointId")
    assert_generated_project_scaffold(
        PROJECT,
        "SlackDigestBoundaryBpmn",
        BPMN_NAME,
        starts[0].attrib["id"],
        entry_point_id=entry_point.attrib["value"],
        expected_resource_count=0,
    )
    notes = "\n".join(
        p.read_text(encoding="utf-8") for p in PROJECT.rglob("*.md")
    )
    low = notes.lower()
    # Each blocker is satisfied by any reasonable phrasing of the concept, not a
    # single exact bigram. "Dynamic input schema" is as correct as "dynamic
    # schemas"; the check verifies the agent named the blocker, not its wording.
    required = {
        "connection binding": "connection binding" in low,
        "dynamic schema(s)": bool(re.search(r"dynamic\s+(\w+\s+){0,4}schema", low)),
        "bindings_v2.json": "bindings_v2.json" in low,
        "package metadata": "package metadata" in low,
    }
    missing = [name for name, ok in required.items() if not ok]
    if missing:
        fail(f"boundary notes missing CLI-owned blockers: {missing}")
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} keeps Integration Service details in the CLI-owned boundary")


if __name__ == "__main__":
    main()
