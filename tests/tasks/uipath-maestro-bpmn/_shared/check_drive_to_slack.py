#!/usr/bin/env python3
"""DriveToSlack (BPMN): cross-connector structural and wiring checks.

Ported from Flow `connector_features/drive_to_slack.yaml`'s
``check_drive_to_slack.py``: same scenario (download a file from Google Drive,
send it into a Slack channel), translated from a JSON node/edge walk to an XML
walk over the registry-driven ``Intsvc.ActivityExecution`` connector shell
(see skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4).

Assertion map (Flow → BPMN):
  F check_drive_to_slack.py:51-53  uipath-google-drive connector key referenced → connector_task(root, DRIVE_KEY) present
  F check_drive_to_slack.py:55-57  uipath-salesforce-slack connector key referenced → connector_task(root, SLACK_KEY) present
  F check_drive_to_slack.py:59-61  Send File to channel operation referenced   → SEND_FILE_RE match on Slack node objectName
  F check_drive_to_slack.py:63-71  Slack node references Drive node id (data binding) → Slack node consumes vars.<DriveOutputVar>
  I                locate/parse .bpmn (file exists, well-formed XML)          → parse_bpmn()
  T                vars.<VarId> reference in place of Flow node-id reference  → output_vars()/has_variable_reference()
  DROPPED          require_no_private_connector_values                        (not in Flow)
  DROPPED          require_sequence_integrity                                 (not in Flow; `bpmn validate` criterion covers structure)
  DROPPED          require_di_for_visible_elements                            (not in Flow; `bpmn validate` criterion covers structure)
  DROPPED          connection-binding check (=bindings.<id> resolves to a declared Connection binding) (Flow never checked connections)
  DROPPED          Drive-precedes-Slack sequence-flow reaches() check         (Flow only checked a data reference, not order)

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. A bpmn:sendTask carries Intsvc.ActivityExecution with connectorKey
     uipath-google-drive.
  3. A bpmn:sendTask carries Intsvc.ActivityExecution with connectorKey
     uipath-salesforce-slack.
  4. The Slack node's objectName names the Send File(s) to channel operation.
  5. The Slack node consumes a variable the Drive node's <uipath:output>
     produces (data binding wired).
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import NS, elements, fail, parse_bpmn  # noqa: E402

DRIVE_KEY = "uipath-google-drive"
SLACK_KEY = "uipath-salesforce-slack"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"

# GUESS: the registry (registry-workflow.md §3) does not publish a fixed
# objectName vocabulary for "Send File to channel" -- it says take objectName
# from `uip is resources describe`. Grounded in
# skills/uipath-agents/references/coded/capabilities/integration-service.md,
# which names the live uipath-salesforce-slack object `send_files_to_channel`
# (plural "files"). Match loosely on the concept rather than one exact
# spelling so either "file" or "files", and any separator, passes.
SEND_FILE_RE = re.compile(r"send[\s_-]*files?[\s_-]*to[\s_-]*channel", re.IGNORECASE)


def has_type(el: ET.Element, token: str) -> bool:
    return token in ET.tostring(el, encoding="unicode")


def context_inputs(task: ET.Element) -> list[ET.Element]:
    return task.findall(".//uipath:input", NS)


def context_value(task: ET.Element, name: str) -> str:
    for inp in context_inputs(task):
        if inp.attrib.get("name") == name:
            return inp.attrib.get("value") or (inp.text or "")
    return ""


def output_vars(task: ET.Element) -> list[str]:
    return [
        out.attrib["var"]
        for out in task.findall(".//uipath:output", NS)
        if out.attrib.get("var")
    ]


def connector_task(root: ET.Element, connector_key: str) -> ET.Element | None:
    for task in elements(root, "sendTask"):
        if has_type(task, ACTIVITY_TYPE) and context_value(task, "connectorKey") == connector_key:
            return task
    return None


def has_variable_reference(task: ET.Element, var_id: str) -> bool:
    needle = f"vars.{var_id}"
    for inp in context_inputs(task):
        value = inp.attrib.get("value") or ""
        text = inp.text or ""
        if needle in value or needle in text:
            return True
    return False


def main() -> None:
    path, root = parse_bpmn("DriveToSlackTest")

    drive_task = connector_task(root, DRIVE_KEY)
    if drive_task is None:
        fail(f"no bpmn:sendTask carrying {ACTIVITY_TYPE} for connector key {DRIVE_KEY!r}")
    print(f"OK: {DRIVE_KEY} sendTask present")

    slack_task = connector_task(root, SLACK_KEY)
    if slack_task is None:
        fail(f"no bpmn:sendTask carrying {ACTIVITY_TYPE} for connector key {SLACK_KEY!r}")
    print(f"OK: {SLACK_KEY} sendTask present")

    object_name = context_value(slack_task, "objectName")
    if not SEND_FILE_RE.search(object_name):
        fail(f"Slack node objectName does not name Send File(s) to channel; found {object_name!r}")
    print(f"OK: Slack node objectName {object_name!r} is Send File to channel")

    drive_vars = output_vars(drive_task)
    if not drive_vars:
        fail("Drive node has no <uipath:output var=...> to wire downstream")

    wired = [v for v in drive_vars if has_variable_reference(slack_task, v)]
    if not wired:
        fail(
            f"Slack node does not consume any Drive output variable "
            f"(vars.{{{', '.join(drive_vars)}}}) -- no data binding wired"
        )
    print(f"OK: Slack node consumes Drive output variable vars.{wired[0]}")

    print(f"OK: {path} wires Drive -> Slack via Intsvc.ActivityExecution connector nodes")


if __name__ == "__main__":
    main()
