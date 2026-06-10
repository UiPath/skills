#!/usr/bin/env python3
"""SlackTriggerButtonClickedTest: verify the flow contains a configured Slack BUTTON_CLICKED
webhook trigger node and at least one downstream node.

Checks:
  1. Flow file exists and is valid JSON.
  2. Slack connector referenced.
  3. BUTTON_CLICKED trigger node present.
  4. eventMode is 'webhook' on the trigger node config (when present).
  5. Trigger has at least one downstream edge.
"""

from __future__ import annotations

import glob
import json
import sys
from typing import Any, NoReturn

FLOW_GLOB = "**/SlackTriggerButtonClickedTest*.flow"
SLACK_KEY = "uipath-salesforce-slack"
TRIGGER_NAME = "BUTTON_CLICKED"


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


def main() -> None:
    flow, path = _load_flow()
    if "nodes" not in flow or "edges" not in flow:
        _fail("Flow missing 'nodes' or 'edges'")

    raw = open(path, encoding="utf-8").read()
    raw_lower = raw.lower()

    if SLACK_KEY not in raw and "slack" not in raw_lower:
        _fail(f"{SLACK_KEY} connector not referenced")

    trigger_nodes = [n for n in flow["nodes"] if TRIGGER_NAME.lower() in json.dumps(n).lower()]
    if not trigger_nodes:
        _fail(f"Trigger node {TRIGGER_NAME!r} not found")
    trig = trigger_nodes[0]

    detail = trig.get("inputs", {}).get("detail", {}) if isinstance(trig.get("inputs"), dict) else {}
    event_mode = detail.get("eventMode")
    if event_mode and event_mode != "webhook":
        _fail(f"Expected eventMode 'webhook', got {event_mode!r}")

    trig_id = trig.get("id")
    if not trig_id:
        _fail("Trigger node missing 'id'")
    downstream = [e for e in flow["edges"] if e.get("source") == trig_id]
    if not downstream:
        _fail("Trigger has no downstream edge — must wire to at least one action")

    print(f"OK: {len(flow['nodes'])} nodes, {len(flow['edges'])} edges; trigger + downstream wired")


if __name__ == "__main__":
    main()
