#!/usr/bin/env python3
"""SlackEmojiList: verify the agent falls back to an HTTP-request node when a
catalog connector has no native activity for the requested operation.

The Slack catalog connector (``uipath-salesforce-slack``) exposes activities for
channels, messages, files and users — but NONE for "list a team's custom emoji"
(the Slack ``emoji.list`` endpoint). The maestro-flow skill must therefore fall
back to a connector-mode HTTP request that reuses the existing Slack
connection's managed auth, rather than giving up or inventing a native activity
that does not exist.

Two checks (subcommand-dispatched, like the outlook_trigger_inbox checker):

  check_fallback   Structural — the emoji list is built as an HTTP-request node
                   bound to the Slack connector (NOT a native connector
                   activity), and it targets the Slack ``emoji.list`` endpoint.
  check_debug      Runtime — ``uip maestro flow debug`` finishes with
                   finalStatus "Completed" against the live Slack connection.

``inputs.detail`` may be a dict (CLI-authored) or a ``=jsonString:``-prefixed
JSON envelope (hand-authored). Both shapes are normalised before inspection.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from typing import Any, NoReturn

# Climb to the uipath-maestro-flow task root that holds _shared/, regardless of
# how deeply this task directory is nested under connector_features/.
_ROOT = os.path.dirname(os.path.abspath(__file__))
for _ in range(6):
    if os.path.isdir(os.path.join(_ROOT, "_shared")):
        break
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)
from _shared.flow_check import run_debug  # noqa: E402

FLOW_GLOB = "**/SlackEmojiListTest*.flow"
SLACK_KEY = "uipath-salesforce-slack"
# Slack endpoint that lists a team's custom emoji. The CLI stores the path both
# as `path` and `url` in bodyParameters, optionally with a leading slash — match
# the bare token so either form satisfies the check.
EMOJI_ENDPOINT = "emoji.list"
_JSONSTRING_PREFIX = "=jsonString:"


def _fail(message: str) -> NoReturn:
    sys.exit(f"FAIL: {message}")


def _read_flow() -> dict[str, Any]:
    flows = sorted(glob.glob(FLOW_GLOB, recursive=True))
    if not flows:
        _fail(f"No flow file matching {FLOW_GLOB}")
    if len(flows) > 1:
        _fail(f"Multiple flows match {FLOW_GLOB}: {flows}")
    with open(flows[0], encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            _fail(f"{flows[0]} is not valid JSON: {e}")


def _normalise_detail(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.startswith(_JSONSTRING_PREFIX):
        try:
            parsed = json.loads(raw[len(_JSONSTRING_PREFIX):])
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _is_slack_http_fallback(node: dict[str, Any]) -> bool:
    """True when ``node`` is an HTTP-request node bound to the Slack connector.

    Accepts both fallback shapes the skill may produce:
      1. The generic managed-HTTP node ``core.action.http.v2`` configured in
         connector mode (``bodyParameters.authentication == "connector"`` and
         ``targetConnector`` == the Slack key).
      2. The connector-scoped ``…uipath-salesforce-slack.slack-http-request``
         activity node.
    A native Slack activity node (send-message, get-user-by-email, …) is NOT an
    HTTP fallback and must not satisfy this check.
    """
    node_type = str(node.get("type") or "").lower()
    blob = json.dumps(node).lower()

    # Shape 2: connector-scoped Slack HTTP request activity.
    if "http-request" in node_type and SLACK_KEY in node_type:
        return True

    # Shape 1: generic managed-HTTP node bound to the Slack connector.
    if "core.action.http" in node_type:
        detail = _normalise_detail((node.get("inputs") or {}).get("detail"))
        body = detail.get("bodyParameters") or {}
        if isinstance(body, dict):
            target = str(body.get("targetConnector") or body.get("connectorKey") or "").lower()
            auth = str(body.get("authentication") or "").lower()
            if auth == "connector" and SLACK_KEY in target:
                return True
        # Be lenient on key placement: any http node whose detail references the
        # Slack connector key still counts as a connector-bound fallback.
        if SLACK_KEY in json.dumps(detail).lower():
            return True
    return False


# ── subcommand: check_fallback ──────────────────────────────────────────────
def check_fallback() -> None:
    flow = _read_flow()
    if "nodes" not in flow or "edges" not in flow:
        _fail("Flow missing 'nodes' or 'edges'")
    nodes = flow["nodes"]
    print(f"OK: {len(nodes)} nodes, {len(flow['edges'])} edges")

    fallback_nodes = [n for n in nodes if _is_slack_http_fallback(n)]
    if not fallback_nodes:
        types = sorted({str(n.get("type") or "") for n in nodes})
        _fail(
            "No HTTP-request fallback node bound to the Slack connector "
            f"({SLACK_KEY!r}) found. The catalog connector has no native "
            "'list custom emoji' activity, so the flow must fall back to a "
            "connector-mode HTTP request (core.action.http.v2 with "
            "authentication=connector, or the slack-http-request activity). "
            f"Node types seen: {types}"
        )
    print(f"OK: {len(fallback_nodes)} Slack HTTP-request fallback node(s) present")

    blob = json.dumps(fallback_nodes).lower()
    if EMOJI_ENDPOINT not in blob:
        _fail(
            f"Slack HTTP fallback node does not target the {EMOJI_ENDPOINT!r} "
            "endpoint (expected the '/emoji.list' path, which lists a team's "
            "custom emoji)."
        )
    print(f"OK: fallback node targets the Slack '/{EMOJI_ENDPOINT}' endpoint")
    print("OK: all Slack HTTP-fallback structural checks passed")


# ── subcommand: check_debug ──────────────────────────────────────────────────
def check_debug() -> None:
    run_debug(timeout=300)
    print("OK: uip maestro flow debug finished with finalStatus=Completed")


DISPATCH = {
    "check_fallback": check_fallback,
    "check_debug": check_debug,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        _fail(f"usage: {os.path.basename(sys.argv[0])} {{{'|'.join(DISPATCH)}}}")
    DISPATCH[sys.argv[1]]()


if __name__ == "__main__":
    main()
