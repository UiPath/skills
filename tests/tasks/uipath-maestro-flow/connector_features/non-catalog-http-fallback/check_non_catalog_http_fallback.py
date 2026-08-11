#!/usr/bin/env python3
"""NonCatalogHttpFallback: verify the agent uses a managed HTTP-request node for
a NON-catalog service that has no IS connector of its own (fixture: Spotify).

Spotify is not a catalog connector — there is no ``uipath-spotify`` connector
key. The only way to reach it through Integration Service's managed auth is the
generic HTTP connector (``uipath-uipath-http``): a connection of that connector
type holds the Spotify base URL + OAuth, and the flow issues a connector-mode
HTTP request against it. The maestro-flow skill must therefore build a
``core.action.http.v2`` node bound to the ``uipath-uipath-http`` connection,
rather than searching for a native Spotify activity that does not exist.

This is the non-catalog counterpart of the slack-http-fallback eval: there the
fallback proxies a catalog connector (``targetConnector`` = the Slack key);
here the connector key IS ``uipath-uipath-http`` because no catalog connector
backs the service.

One check (subcommand-dispatched, like the outlook_trigger_inbox checker):

  check_fallback   Structural — the profile fetch is a connector-mode
                   ``core.action.http.v2`` node whose connector key is
                   ``uipath-uipath-http`` with a bound connection, and it
                   targets Spotify's ``/me`` endpoint.

``inputs.detail`` may be a dict (CLI-authored) or a ``=jsonString:``-prefixed
JSON envelope (hand-authored). Both shapes are normalised before inspection.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from typing import Any, NoReturn

FLOW_GLOB = "**/SpotifyProfileTest*.flow"
# The generic HTTP connector — the only managed path to a service with no
# catalog connector of its own.
HTTP_CONNECTOR_KEY = "uipath-uipath-http"
# Spotify "Get Current User's Profile" endpoint.
ME_ENDPOINT = "/me"
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


def _connection_bound(detail: dict[str, Any]) -> bool:
    body = detail.get("bodyParameters") or {}
    candidates = [
        detail.get("connectionId"),
        detail.get("connectionResourceId"),
        body.get("connection") if isinstance(body, dict) else None,
    ]
    return any(
        isinstance(v, str) and v.strip() and v != "ImplicitConnection"
        for v in candidates
    )


def _is_http_connector_fallback(node: dict[str, Any]) -> bool:
    """True when ``node`` is a connector-mode managed-HTTP node whose connector
    key is the generic ``uipath-uipath-http`` (the non-catalog fallback shape)."""
    node_type = str(node.get("type") or "").lower()
    if "core.action.http" not in node_type:
        return False
    detail = _normalise_detail((node.get("inputs") or {}).get("detail"))
    body = detail.get("bodyParameters") or {}
    auth = str(body.get("authentication") or "").lower() if isinstance(body, dict) else ""
    connector = str(detail.get("connector") or "").lower()
    target = (
        str(body.get("targetConnector") or body.get("connectorKey") or "").lower()
        if isinstance(body, dict)
        else ""
    )
    uses_http_connector = HTTP_CONNECTOR_KEY in (connector, target)
    return auth == "connector" and uses_http_connector and _connection_bound(detail)


def _targets_me_endpoint(node: dict[str, Any]) -> bool:
    """True when the node's path/url is Spotify's ``/me`` endpoint. Matches the
    explicit field value (not a blob substring) so '/me' cannot spuriously match
    inside an unrelated path like '/members'."""
    detail = _normalise_detail((node.get("inputs") or {}).get("detail"))
    body = detail.get("bodyParameters") or {}
    if not isinstance(body, dict):
        return False
    for key in ("path", "url"):
        value = body.get(key)
        if isinstance(value, str) and value.strip().rstrip("/").lower().endswith("/me"):
            return True
    return False


# ── subcommand: check_fallback ──────────────────────────────────────────────
def check_fallback() -> None:
    flow = _read_flow()
    if "nodes" not in flow or "edges" not in flow:
        _fail("Flow missing 'nodes' or 'edges'")
    nodes = flow["nodes"]
    print(f"OK: {len(nodes)} nodes, {len(flow['edges'])} edges")

    fallback_nodes = [n for n in nodes if _is_http_connector_fallback(n)]
    if not fallback_nodes:
        types = sorted({str(n.get("type") or "") for n in nodes})
        _fail(
            "No managed HTTP-request node using the generic "
            f"{HTTP_CONNECTOR_KEY!r} connector found. Spotify is not a catalog "
            "connector, so the flow must issue a connector-mode "
            "core.action.http.v2 request bound to the uipath-uipath-http "
            f"connection. Node types seen: {types}"
        )
    print(
        f"OK: {len(fallback_nodes)} managed-HTTP node(s) bound to "
        f"{HTTP_CONNECTOR_KEY!r} with a connection present"
    )

    if not any(_targets_me_endpoint(n) for n in fallback_nodes):
        _fail(
            f"No {HTTP_CONNECTOR_KEY!r} node targets the {ME_ENDPOINT!r} endpoint "
            "(expected the Spotify '/me' path, which returns the current user's "
            "profile)."
        )
    print(f"OK: fallback node targets Spotify's '{ME_ENDPOINT}' endpoint")
    print("OK: all Spotify HTTP-fallback structural checks passed")


DISPATCH = {
    "check_fallback": check_fallback,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        _fail(f"usage: {os.path.basename(sys.argv[0])} {{{'|'.join(DISPATCH)}}}")
    DISPATCH[sys.argv[1]]()


if __name__ == "__main__":
    main()
