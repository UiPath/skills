#!/usr/bin/env python3
"""DriveToSlack: structural and runtime checks for the cross-connector flow.

Runs every check in sequence. Exits non-zero on the first failure with a
``FAIL: ...`` message; prints ``OK: ...`` per check and a final summary on
success.

Checks performed:
  1. Flow file exists and is valid JSON with ``nodes`` and ``edges``.
  2. Flow references the ``uipath-google-drive`` connector.
  3. Flow references the ``uipath-salesforce-slack`` connector.
  4. Flow references the Slack "Send File to channel" operation.
  5. Slack node references a Google Drive node id (data binding wired).
  6. The Drive download node is compiled as a file response:
     ``responseAsFile: true`` and a ``file`` definition output type.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _shared.flow_check import find_flow_file  # noqa: E402

FLOW_GLOB = "**/DriveToSlackTest*.flow"
DRIVE_KEY = "uipath-google-drive"
SLACK_KEY = "uipath-salesforce-slack"


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _flow_path() -> str:
    return find_flow_file(flow_glob=os.path.basename(FLOW_GLOB))


def _essential_configuration(node: dict) -> dict:
    raw = ((node.get("inputs") or {}).get("detail") or {}).get("configuration")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw.split("=jsonString:", 1)[-1])
        except json.JSONDecodeError:
            return {}
    essential = raw.get("essentialConfiguration") if isinstance(raw, dict) else None
    return essential if isinstance(essential, dict) else {}


def _definition_output_type(flow: dict, node: dict) -> str | None:
    for definition in flow.get("definitions") or []:
        if definition.get("nodeType") == node.get("type"):
            return ((definition.get("outputDefinition") or {}).get("output") or {}).get("type")
    return None


def main() -> None:
    path = _flow_path()
    raw = open(path, encoding="utf-8").read()
    try:
        flow = json.loads(raw)
    except json.JSONDecodeError as e:
        _fail(f"{path} is not valid JSON: {e}")

    if "nodes" not in flow or "edges" not in flow:
        _fail("Flow missing 'nodes' or 'edges'")
    print(f"OK: {len(flow['nodes'])} nodes, {len(flow['edges'])} edges")

    if DRIVE_KEY not in raw:
        _fail(f"{DRIVE_KEY} connector key not found")
    print(f"OK: {DRIVE_KEY} connector key present")

    if SLACK_KEY not in raw:
        _fail(f"{SLACK_KEY} connector key not found")
    print(f"OK: {SLACK_KEY} connector key present")

    if not re.search(r"send[\s_-]?file[\s_-]?to[\s_-]?channel", raw.lower()):
        _fail("Send File to channel operation not referenced")
    print("OK: Send File to channel operation present")

    drive_nodes = [n for n in flow["nodes"] if DRIVE_KEY in json.dumps(n)]
    slack_nodes = [n for n in flow["nodes"] if SLACK_KEY in json.dumps(n)]
    if not drive_nodes or not slack_nodes:
        _fail("Missing drive or slack node")
    drive_ids = {n.get("id") for n in drive_nodes if n.get("id")}
    slack_blob = json.dumps(slack_nodes)
    if not any(did in slack_blob for did in drive_ids):
        _fail("Slack node does not reference Google Drive node id (no data binding)")
    print("OK: Slack node references Google Drive node output")

    # Without these Studio Web compiles the download as JSON and the run fails with
    # "File reference required to host a file in Data Fabric".
    downloads = [n for n in drive_nodes if "download" in str(n.get("type", "")).lower()]
    if not downloads:
        _fail("No Google Drive download node found")
    for node in downloads:
        if _essential_configuration(node).get("responseAsFile") is not True:
            _fail(f"Drive download node {node.get('id')!r}: essentialConfiguration.responseAsFile is not true")
        out_type = _definition_output_type(flow, node)
        if out_type != "file":
            _fail(f"Drive download node {node.get('id')!r}: definition output type is {out_type!r}, expected 'file'")
    print("OK: Drive download node is compiled as a file response")

    print("OK: all DriveToSlack checks passed")


if __name__ == "__main__":
    main()
