#!/usr/bin/env python3
"""SlackSendButtonResponseTest: verify the flow wires the Slack "Send Button Response" activity.

Checks:
  1. Flow file exists and is valid JSON.
  2. Slack connector referenced.
  3. Send Button Response operation referenced (matches op_regex).
  4. Required markers present in the flow.
  5. Decision + Terminate nodes present.
"""

from __future__ import annotations

import glob
import json
import re
import sys
from typing import Any, NoReturn

FLOW_GLOB = "**/SlackSendButtonResponseTest*.flow"
SLACK_KEY = "uipath-salesforce-slack"
OP_REGEX = re.compile(r"send[\s_-]?button[\s_-]?response", re.IGNORECASE)
MARKERS = ['eval-button-response']


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

    if not OP_REGEX.search(raw_lower):
        _fail(f"Operation pattern {OP_REGEX.pattern!r} not matched in flow")

    for marker in MARKERS:
        if marker not in raw:
            _fail(f"Required marker {marker!r} not present in flow")

    _check_flow_controls(flow)

    print(f"OK: {len(flow['nodes'])} nodes, {len(flow['edges'])} edges; all checks passed")


if __name__ == "__main__":
    main()
