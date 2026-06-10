#!/usr/bin/env python3
"""SlackUploadFile: verify the SlackUploadFileTest flow wires Slack's
"Send File to Channel" activity with the target channel and filename.

Checks:
  1. Flow file exists and is valid JSON.
  2. Slack connector referenced.
  3. Send-file / upload operation referenced.
  4. Target channel and filename appear in the flow.
  5. Decision + Terminate nodes present.
"""

from __future__ import annotations

import glob
import json
import re
import sys
from typing import Any, NoReturn

FLOW_GLOB = "**/SlackUploadFileTest*.flow"
SLACK_KEY = "uipath-salesforce-slack"
TARGET_CHANNEL = "coding-agent-testing"
TARGET_FILENAME = "eval-upload.txt"


def _fail(msg: str) -> NoReturn:
    sys.exit(f"FAIL: {msg}")


def _load_flow() -> tuple[dict[str, Any], str]:
    flows = glob.glob(FLOW_GLOB, recursive=True)
    if not flows:
        _fail(f"No flow file matching {FLOW_GLOB!r}")
    path = flows[0]
    try:
        return json.loads(open(path, encoding="utf-8").read()), path
    except json.JSONDecodeError as e:
        _fail(f"{path} is not valid JSON: {e}")


def _check_flow_controls(flow: dict) -> None:
    types = [n.get("type", "").lower() for n in flow.get("nodes", [])]
    if not any("decision" in t for t in types):
        _fail("No Decision node found")
    if not any("terminate" in t for t in types):
        _fail("No Terminate node found")


def main() -> None:
    flow, path = _load_flow()
    if "nodes" not in flow or "edges" not in flow:
        _fail("Flow missing 'nodes' or 'edges'")

    raw = open(path, encoding="utf-8").read()
    raw_lower = raw.lower()

    if SLACK_KEY not in raw and "slack" not in raw_lower:
        _fail(f"{SLACK_KEY} connector not referenced")

    if not re.search(r"send[\s_-]?file[\s_-]?to[\s_-]?channel|files\.upload|uploadfile|send_files_to_channel",
                     raw_lower):
        _fail("Send File / upload operation not referenced")

    if TARGET_CHANNEL not in raw:
        _fail(f"Target channel {TARGET_CHANNEL!r} not wired into flow")

    if TARGET_FILENAME not in raw:
        _fail(f"Target filename {TARGET_FILENAME!r} not wired into flow")

    _check_flow_controls(flow)

    print(f"OK: {len(flow['nodes'])} nodes, {len(flow['edges'])} edges; all checks passed")


if __name__ == "__main__":
    main()
