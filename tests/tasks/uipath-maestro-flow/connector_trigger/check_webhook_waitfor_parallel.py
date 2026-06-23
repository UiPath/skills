#!/usr/bin/env python3
"""WebhookSelfTest: structural + runtime check for a two-branch self-testing flow.

The flow must be:

  manual start trigger
    ├─ branch 1: Wait-for-event node (HTTP Webhook, uipath-http-webhook) -> End
    └─ branch 2: Managed HTTP Request (core.action.http.v2, manual GET to the
                 HTTP Webhook connection's webhook URL, no headers / no query) -> End

Branch 2's GET hits the webhook URL, which delivers the event that completes
branch 1's wait — so the flow self-triggers at runtime. This checker validates
the static two-branch shape only; it does not run `flow debug`.

Static assertions (read from the `.flow` source):
  1. The start trigger is preserved (`core.trigger.*`) and fans out to >=2
     branches (the event wait and the HTTP request).
  2. A Wait-for-event node of the HTTP Webhook connector event exists
     (`uipath.connector.event.uipath-http-webhook.http-webhook`).
  3. A `core.action.http.v2` node is a MANUAL `GET` whose `url` is the webhook
     URL, with NOTHING in headers or query (per the prompt).
  4. Both branch tails reach an End node (`core.control.end`).
"""

from __future__ import annotations

import glob
import json
import sys

FLOW_GLOB = "**/WebhookSelfTest*.flow"
EVENT_MARKERS = ("uipath.connector.event", "uipath-http-webhook")
HTTP_TYPE = "core.action.http.v2"
END_TYPE = "core.control.end"
TRIGGER_PREFIX = "core.trigger."


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _read_flow() -> dict:
    flows = glob.glob(FLOW_GLOB, recursive=True)
    if not flows:
        _fail(f"no flow file matching {FLOW_GLOB} under cwd")
    with open(flows[0], encoding="utf-8") as f:
        return json.load(f)


def _reachable(start_id: str, edges: list) -> set:
    """Node ids reachable from start_id following edges (sourceNodeId -> targetNodeId)."""
    adj: dict[str, list[str]] = {}
    for e in edges:
        adj.setdefault(e.get("sourceNodeId"), []).append(e.get("targetNodeId"))
    seen, stack = set(), [start_id]
    while stack:
        n = stack.pop()
        for t in adj.get(n, []):
            if t and t not in seen:
                seen.add(t)
                stack.append(t)
    return seen


def main() -> None:
    flow = _read_flow()
    nodes = flow.get("nodes") or []
    edges = flow.get("edges") or []
    types_seen = sorted({str(n.get("type", "")) for n in nodes})

    # 1. Start trigger preserved + fans out into >=2 branches.
    triggers = [n for n in nodes if str(n.get("type", "")).startswith(TRIGGER_PREFIX)]
    if not triggers:
        _fail(f"no start trigger (core.trigger.*). Types seen: {types_seen}")
    start_id = triggers[0].get("id")
    out_edges = [e for e in edges if e.get("sourceNodeId") == start_id]
    if len(out_edges) < 2:
        _fail(
            f"start trigger {start_id!r} must fan out into >=2 branches; "
            f"found {len(out_edges)} outgoing edge(s)"
        )
    print(f"OK: start trigger {start_id!r} fans out into {len(out_edges)} branches")

    # 2. HTTP Webhook Wait-for-event node present.
    event_nodes = [
        n for n in nodes
        if all(m in str(n.get("type", "")).lower() for m in EVENT_MARKERS)
    ]
    if not event_nodes:
        _fail(
            "no HTTP Webhook Wait-for-event node (type containing "
            f"{' + '.join(EVENT_MARKERS)}). Types seen: {types_seen}"
        )
    print("OK: HTTP Webhook wait-for-event node present")

    # 3. Manual GET HTTP node to the webhook URL, no headers / no query.
    http_nodes = [n for n in nodes if str(n.get("type", "")) == HTTP_TYPE]
    if not http_nodes:
        _fail(f"no {HTTP_TYPE} node. Types seen: {types_seen}")

    good_http = None
    for n in http_nodes:
        body = ((n.get("inputs") or {}).get("detail") or {}).get("bodyParameters") or {}
        if not isinstance(body, dict):
            continue
        auth = str(body.get("authentication", "")).lower()
        method = str(body.get("method", "")).lower()
        url = str(body.get("url", ""))
        headers = body.get("headers")
        query = body.get("query") or body.get("queryParameters")
        if auth != "manual" or method != "get":
            continue
        if "webhook" not in url.lower():
            continue
        if headers:  # any non-empty headers fails the "nothing in header" rule
            _fail(f"HTTP node must not set headers; found: {headers}")
        if query:  # any non-empty query fails the "nothing in query" rule
            _fail(f"HTTP node must not set query parameters; found: {query}")
        good_http = n
        break

    if good_http is None:
        _fail(
            "no core.action.http.v2 node configured as a manual GET to the "
            "webhook URL (authentication=manual, method=GET, url contains 'webhook')"
        )
    print("OK: manual GET HTTP node to webhook URL, no headers / no query")

    # 4. Both the event wait and the HTTP node reach an End node.
    end_ids = {n.get("id") for n in nodes if str(n.get("type", "")) == END_TYPE}
    if not end_ids:
        _fail(f"no End node ({END_TYPE}). Types seen: {types_seen}")
    for label, node in (("wait-for-event", event_nodes[0]), ("http-request", good_http)):
        reach = _reachable(node.get("id"), edges)
        if not (reach & end_ids):
            _fail(f"{label} branch does not reach an End node")
    print("OK: both branches terminate at an End node")

    print("OK: all WebhookSelfTest checks passed")


if __name__ == "__main__":
    main()
