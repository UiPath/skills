#!/usr/bin/env python3
"""ComplexArray (BPMN): locate/parse the process file, and the advisory
resolved-user-id check.

Ported from Flow `connector_features/complex_array.yaml`. The core "Slack
group-DM node has its users complex array populated" assertion (Flow
criterion 2) lives in the shared `_shared/check_slack_multiselect.py`, used
identically by `multiselect.yaml`; this script covers this task's other two
criteria, which are project-name-specific (Flow's task fixes the project name
"ComplexArrayTest", unlike multiselect's name-agnostic port).

Assertion map (Flow -> BPMN):
  F criterion 1  flow_contains.py --flow-name ComplexArrayTest '"nodes"'
                 '"edges"' (file exists and is valid JSON)
                     -> parse_bpmn("ComplexArrayTest") locates and parses the .bpmn
  I              locate/parse .bpmn with the ComplexArrayTest name hint -> parse_bpmn("ComplexArrayTest")
  F criterion 3  flow_contains.py --flow-name ComplexArrayTest
                 'U0B7Y855WGG' 'U05Q882RHFZ' (advisory, threshold 0)
                     -> check_ids(): same two literals searched in the located .bpmn's raw text (same weight/threshold)
  F criterion 4  flow_contains.py --flow-name ComplexArrayTest --regex
                 '"connectionId": "2bbc2253-..."' (connection pin)
                     -> check_connection(): the Slack task's `connection` input,
                        followed through `=bindings.<id>`, is SHARED_CONNECTION_ID

Usage:
    python3 check_complex_array.py               # criterion 1: locate + parse
    python3 check_complex_array.py --ids         # criterion 3: advisory id search
    python3 check_complex_array.py --connection  # criterion 4: connection pin
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import NS, context_value, fail, parse_bpmn  # noqa: E402
from _shared.check_slack_multiselect import slack_tasks  # noqa: E402

PROJECT_HINT = "ComplexArrayTest"
RECIPIENT_IDS = ("U0B7Y855WGG", "U05Q882RHFZ")
SHARED_CONNECTION_ID = "2bbc2253-29a4-4952-a436-6705d74e5943"

_BINDING_REF_RE = re.compile(r"=bindings\.(\S+)")


def check_parse() -> None:
    path, _root = parse_bpmn(PROJECT_HINT)
    print(f"OK: {path} exists and parses")


def check_ids() -> None:
    path, _root = parse_bpmn(PROJECT_HINT)
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    missing = [uid for uid in RECIPIENT_IDS if uid not in text]
    for uid in RECIPIENT_IDS:
        print(f"{'OK     ' if uid not in missing else 'MISSING'} {uid}")
    if missing:
        fail(f"resolved Slack user id(s) not found in {path}: {missing}")
    print(f"OK: {path} references both resolved Slack user ids")


def _connection_id(root: ET.Element, task: ET.Element) -> str:
    value = context_value(task, "connection")
    match = _BINDING_REF_RE.fullmatch(value)
    if not match:
        return value

    for binding in root.findall(".//uipath:binding", NS):
        if binding.attrib.get("id") != match.group(1):
            continue
        return binding.attrib.get("default") or binding.attrib.get("resourceKey") or ""
    return ""


def check_connection() -> None:
    path, root = parse_bpmn(PROJECT_HINT)
    tasks = slack_tasks(root)
    if not tasks:
        fail(f"no Slack connector task in {path}")

    bound = {_connection_id(root, task) for task in tasks}
    if bound != {SHARED_CONNECTION_ID}:
        fail(f"Slack task bound to {sorted(bound)}, expected {SHARED_CONNECTION_ID}")
    print(f"OK: {path} Slack task bound to {SHARED_CONNECTION_ID}")


def main() -> None:
    if "--ids" in sys.argv[1:]:
        check_ids()
    elif "--connection" in sys.argv[1:]:
        check_connection()
    else:
        check_parse()


if __name__ == "__main__":
    main()
