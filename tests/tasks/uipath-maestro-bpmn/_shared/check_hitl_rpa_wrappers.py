#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    elements,
    fail,
    has_uipath_extension,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
    tag_case_hint,
)


def main() -> None:
    path, root = parse_bpmn("EmployeeAccessBpmn")
    hitl = [
        task for task in elements(root, "userTask") if has_uipath_extension(task, "Actions.HITL")
    ]
    rpa = [
        task
        for task in elements(root, "serviceTask")
        if has_uipath_extension(task, "Orchestrator.StartJob")
    ]
    if not hitl:
        fail("missing bpmn:userTask with Actions.HITL uipath:activity shell" + tag_case_hint(root, "userTask"))
    if not rpa:
        fail(
            "missing bpmn:serviceTask with Orchestrator.StartJob uipath:activity shell"
            + tag_case_hint(root, "serviceTask")
        )
    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} contains documented HITL and RPA wrappers")


if __name__ == "__main__":
    main()
