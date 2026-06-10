#!/usr/bin/env python3
"""SlackSendMessage: verify the agent's SlackSendMessageTest flow wires the
Slack "Send Message to Channel" connector node end-to-end.

Checks:
  1. Flow file exists and is valid JSON with nodes + edges.
  2. Slack connector referenced (or managed HTTP fallback hitting slack.com).
  3. Target channel "coding-agent-testing" appears in node config.
  4. Message text "Hello from the Slack eval" appears in node config.
  5. Decision + Terminate nodes present.
"""

from __future__ import annotations

import glob
import json
import sys
from typing import Any, NoReturn

FLOW_GLOB = "**/SlackSendMessageTest*.flow"
SLACK_KEY = "uipath-salesforce-slack"
TARGET_CHANNEL = "coding-agent-testing"
TARGET_MESSAGE = "Hello from the Slack eval"


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

    if "send" not in raw_lower or "message" not in raw_lower:
        _fail("Send-message operation not referenced")

    if TARGET_CHANNEL not in raw:
        _fail(f"Target channel {TARGET_CHANNEL!r} not wired into flow")

    if TARGET_MESSAGE not in raw:
        _fail(f"Target message text {TARGET_MESSAGE!r} not wired into flow")

    _check_flow_controls(flow)

    print(f"OK: {len(flow['nodes'])} nodes, {len(flow['edges'])} edges; all checks passed")


if __name__ == "__main__":
    main()
