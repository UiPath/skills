#!/usr/bin/env python3
"""SlackPaginatedUserLookup: verify the flow wires List Users → Send Message to User
with the send-message node referencing the list-users node id (data binding).

Checks:
  1. Flow file exists and is valid JSON.
  2. Slack connector referenced.
  3. Both list-users and send-message-to-user operations referenced.
  4. Send-message node references list-users node id (data binding).
  5. Decision + Terminate nodes present.
"""

from __future__ import annotations

import glob
import json
import re
import sys
from typing import Any, NoReturn

FLOW_GLOB = "**/SlackPaginatedUserLookupTest*.flow"
SLACK_KEY = "uipath-salesforce-slack"


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

    if not re.search(r"list[\s_-]?all[\s_-]?users|users\.list|listusers|users_list", raw_lower):
        _fail("List All Users operation not referenced")

    if not re.search(r"send[\s_-]?message[\s_-]?to[\s_-]?user|sendmessagetouser|send_message_to_user", raw_lower):
        _fail("Send Message to User operation not referenced")

    list_nodes = [n for n in flow["nodes"]
                  if re.search(r"list.*user|users_?list|listusers", json.dumps(n).lower())]
    send_nodes = [n for n in flow["nodes"]
                  if re.search(r"send.*message.*user|sendmessagetouser|send_message_to_user",
                               json.dumps(n).lower())]
    if not list_nodes:
        _fail("List Users node not found")
    if not send_nodes:
        _fail("Send Message to User node not found")

    list_ids = {n.get("id") for n in list_nodes if n.get("id")}
    send_blob = json.dumps(send_nodes)
    if not any(lid in send_blob for lid in list_ids):
        _fail("Send-message node does not reference list-users node id (no data binding)")

    _check_flow_controls(flow)

    print(f"OK: {len(flow['nodes'])} nodes, {len(flow['edges'])} edges; all checks passed")


if __name__ == "__main__":
    main()
