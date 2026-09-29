#!/usr/bin/env python3
"""SearchableJoinsTest (BPMN): Salesforce connector node presence.

Ported from Flow `connector_features/searchable_joins.yaml`'s
``flow_contains.py`` criteria: same scenario (a Salesforce query node joins
in related Opportunities for each Account in the same query, then branches on
whether any opportunities came back), translated from a JSON node/edge
substring search to an XML walk over the registry-driven
``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3). Flow's own
grader never asserted the join/branch shape itself (only that the file
exists, that a Salesforce connector node is present, and that the flow
validates), so this port keeps that same breadth rather than narrowing or
widening it.

Two subcommands (subcommand-dispatched, matching the sibling connector
graders in this suite):

  check_exists     Flow's ``flow_contains.py --flow-name SearchableJoinsTest
                     '"nodes"' '"edges"'`` -- the .bpmn exists and is
                     well-formed XML.
  check_connector   Flow's ``flow_contains.py --flow-name SearchableJoinsTest
                     'uipath-salesforce-sfdc'`` -- a connector node references
                     the Salesforce connector key.

The task's third criterion (the completed process validates) runs
``_shared/validate_bpmn.py`` directly from the YAML and needs no code here.

Assertion map (Flow → BPMN):
  F criterion 1  flow_contains --flow-name SearchableJoinsTest '"nodes"' '"edges"'
                  (Flow file exists and is valid JSON)
                  → check_exists(): parse_bpmn("SearchableJoinsTest")
                    (well-formed XML is the BPMN analog of valid JSON)
  F criterion 2  flow_contains --flow-name SearchableJoinsTest
                  'uipath-salesforce-sfdc'
                  → check_connector(): an Intsvc.ActivityExecution
                    bpmn:sendTask with connectorKey uipath-salesforce-sfdc
  F criterion 3  _shared/validate_flow.py (the completed flow validates)
                  → _shared/validate_bpmn.py, wired directly in the task YAML
  I              locate/parse .bpmn (file exists, well-formed XML)
                  → parse_bpmn()
  DROPPED        require_no_private_connector_values / require_sequence_integrity
                  / require_di_for_visible_elements / connection-binding checks
                  (not in Flow; the `bpmn validate` criterion covers structure)
  DROPPED        join/branch shape check (Flow never asserted the related-object
                  join or the has-opportunities branch structurally -- only the
                  connector key and that the artifact validates)
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import context_value, elements, fail, has_type, parse_bpmn  # noqa: E402

NAME_HINT = "SearchableJoinsTest"
CONNECTOR_KEY = "uipath-salesforce-sfdc"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"


def find_connector_node(root: ET.Element) -> ET.Element | None:
    for task in elements(root, "sendTask"):
        if has_type(task, ACTIVITY_TYPE) and context_value(task, "connectorKey") == CONNECTOR_KEY:
            return task
    return None


def check_exists() -> None:
    path, _root = parse_bpmn(NAME_HINT)
    print(f"OK: {path} exists and is well-formed XML")


def check_connector() -> None:
    _path, root = parse_bpmn(NAME_HINT)

    node = find_connector_node(root)
    if node is None:
        fail(
            f"no bpmn:sendTask carries {ACTIVITY_TYPE} with connectorKey "
            f"{CONNECTOR_KEY!r}"
        )
    print(
        f"OK: {CONNECTOR_KEY} sendTask present "
        f"(objectName={context_value(node, 'objectName')!r})"
    )


DISPATCH = {
    "check_exists": check_exists,
    "check_connector": check_connector,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.exit(f"usage: {sys.argv[0]} {{{'|'.join(DISPATCH)}}}")
    DISPATCH[sys.argv[1]]()


if __name__ == "__main__":
    main()
