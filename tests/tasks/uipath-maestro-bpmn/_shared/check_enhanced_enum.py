#!/usr/bin/env python3
"""EnhancedEnumTest (BPMN): WooCommerce connector node presence.

Ported from Flow `connector_features/enhanced_enum.yaml`'s ``flow_contains.py``
criteria: same scenario (a WooCommerce "get product reviews" node exposes an
enhanced-enum sort-order field with friendly display labels rather than raw
codes), translated from a JSON node/edge substring search to an XML walk over
the registry-driven ``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3). This is an
offline authoring task -- Flow's own grader never asserted a live connection,
a specific sort value, or a validate pass, and neither does this port.

Two subcommands (subcommand-dispatched, matching the sibling connector
graders in this suite):

  check_exists     Flow's ``flow_contains.py --flow-name EnhancedEnumTest
                     '"nodes"' '"edges"'`` -- the .bpmn exists and is
                     well-formed XML.
  check_connector   Flow's ``flow_contains.py --flow-name EnhancedEnumTest
                     'uipath-automattic-woocommerce'`` -- a connector node
                     references the WooCommerce connector key.

Assertion map (Flow → BPMN):
  F criterion 1  flow_contains --flow-name EnhancedEnumTest '"nodes"' '"edges"'
                  (Flow file exists and is valid JSON)
                  → check_exists(): parse_bpmn("EnhancedEnumTest") (well-formed
                    XML is the BPMN analog of valid JSON)
  F criterion 2  flow_contains --flow-name EnhancedEnumTest
                  'uipath-automattic-woocommerce'
                  → check_connector(): an Intsvc.ActivityExecution
                    bpmn:sendTask with connectorKey uipath-automattic-woocommerce
  I              locate/parse .bpmn (file exists, well-formed XML)
                  → parse_bpmn()
  DROPPED        require_no_private_connector_values / require_sequence_integrity
                  / require_di_for_visible_elements / connection-binding checks
                  (not in Flow; Flow has no `validate` criterion on this task
                  either, so none is added here)

Note: the task's tag list keeps Flow's misspelled connector tag
`uipath-automaticc-woocommerce` verbatim (per the porting brief, tags are
carried unchanged); this grader checks the REAL connector key
`uipath-automattic-woocommerce`, matching what Flow's own grader checked.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import context_value, elements, fail, has_type, parse_bpmn  # noqa: E402

NAME_HINT = "EnhancedEnumTest"
CONNECTOR_KEY = "uipath-automattic-woocommerce"
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
