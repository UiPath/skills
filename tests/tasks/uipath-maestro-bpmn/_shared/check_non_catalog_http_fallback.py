#!/usr/bin/env python3
"""NonCatalogHttpFallback (BPMN): connector-mode HTTP request to a non-catalog
service (Spotify), through the generic HTTP connector.

Spotify has no ``uipath-spotify`` IS connector; the only managed path is a
connection of the generic HTTP connector ``uipath-uipath-http``, which holds
Spotify's base URL + OAuth. Every HTTP request is ``Intsvc.UnifiedHttpRequest``
(skills/uipath-maestro-bpmn/references/v2-connector-nodes.md, "HTTP requests"),
so the node must be one in connector mode through that connection.

Checks:
  - a bpmn:sendTask carries Intsvc.UnifiedHttpRequest;
  - its body is ``authentication: "connector"`` with ``targetConnector``
    ``uipath-uipath-http``;
  - its ``connection`` is bound (not the manual ``ImplicitConnection``);
  - a ``path``/``url`` (context field or body key) ends with ``/me``.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_non_catalog_http_fallback.py check_fallback
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    context_inputs,
    context_value,
    elements,
    fail,
    has_type,
    parse_bpmn,
)

PROJECT_NAME_HINT = "SpotifyProfileTest"
# The generic HTTP connector -- the only managed path to a service with no
# catalog connector of its own.
HTTP_CONNECTOR_KEY = "uipath-uipath-http"
# Spotify "Get Current User's Profile" endpoint.
ME_ENDPOINT = "/me"
ACTIVITY_TYPES = ("Intsvc.UnifiedHttpRequest",)
_IMPLICIT_CONNECTION = "implicitconnection"


def body_input(task: ET.Element) -> ET.Element | None:
    for inp in context_inputs(task):
        if inp.attrib.get("target") == "body" or inp.attrib.get("name") == "body":
            return inp
    return None


def body_json(task: ET.Element) -> dict | None:
    inp = body_input(task)
    if inp is None:
        return None
    raw = (inp.text or inp.attrib.get("value") or "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(
            f"body input on node {task.attrib.get('id', '?')!r} is not valid "
            f"JSON: {exc}"
        )
    return parsed if isinstance(parsed, dict) else None


def is_bound_connection(value: str) -> bool:
    value = value.strip()
    return bool(value) and value.lower() != _IMPLICIT_CONNECTION


def is_http_connector_node(task: ET.Element) -> bool:
    """True when ``task`` is a connector-mode node backed by the generic
    ``uipath-uipath-http`` connector with a real (non-implicit) connection
    bound -- the non-catalog fallback shape."""
    if not any(has_type(task, token) for token in ACTIVITY_TYPES):
        return False
    body = body_json(task) or {}
    if body.get("authentication") != "connector":
        return False
    if str(body.get("targetConnector", "")).lower() != HTTP_CONNECTOR_KEY:
        return False
    connection_val = context_value(task, "connection") or context_value(task, "connectionId")
    return is_bound_connection(connection_val)


def target_paths(task: ET.Element) -> list[str]:
    candidates: list[str] = []
    for field in ("path", "url"):
        value = context_value(task, field)
        if value:
            candidates.append(value)
    body = body_json(task)
    if isinstance(body, dict):
        for key in ("path", "url"):
            value = body.get(key)
            if isinstance(value, str):
                candidates.append(value)
    return candidates


def targets_me_endpoint(task: ET.Element) -> bool:
    """True when the node's path/url is Spotify's ``/me`` endpoint. Matches
    the explicit field value (not a blob substring) so '/me' cannot
    spuriously match inside an unrelated path like '/members'."""
    for value in target_paths(task):
        if value.strip().rstrip("/").lower().endswith("/me"):
            return True
    return False


# ── subcommand: check_fallback ──────────────────────────────────────────────
def check_fallback() -> None:
    path, root = parse_bpmn(PROJECT_NAME_HINT)

    send_tasks = elements(root, "sendTask")
    fallback_nodes = [t for t in send_tasks if is_http_connector_node(t)]
    if not fallback_nodes:
        seen = sorted(
            {
                f"{context_value(t, 'connectorKey')} ({'Unified' if has_type(t, 'Intsvc.UnifiedHttpRequest') else 'other'})"
                for t in send_tasks
                if context_value(t, "connectorKey")
            }
        )
        fail(
            "No Intsvc.UnifiedHttpRequest in connector mode through a "
            f"{HTTP_CONNECTOR_KEY!r} connection was found. Spotify is not a "
            "catalog connector, so the process must send a connector-mode "
            f"HTTP request (targetConnector {HTTP_CONNECTOR_KEY!r}) bound to "
            f"that connection. Connector nodes seen: {seen}"
        )
    print(
        f"OK: {len(fallback_nodes)} managed-HTTP node(s) bound to "
        f"{HTTP_CONNECTOR_KEY!r} with a connection present"
    )

    if not any(targets_me_endpoint(t) for t in fallback_nodes):
        fail(
            f"No {HTTP_CONNECTOR_KEY!r} node targets the {ME_ENDPOINT!r} "
            "endpoint (expected the Spotify '/me' path, which returns the "
            "current user's profile)."
        )
    print(f"OK: fallback node targets Spotify's '{ME_ENDPOINT}' endpoint")
    print(f"OK: {path} -- all Spotify HTTP-fallback structural checks passed")


DISPATCH = {
    "check_fallback": check_fallback,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        fail(f"usage: {os.path.basename(sys.argv[0])} {{{'|'.join(DISPATCH)}}}")
    DISPATCH[sys.argv[1]]()


if __name__ == "__main__":
    main()
