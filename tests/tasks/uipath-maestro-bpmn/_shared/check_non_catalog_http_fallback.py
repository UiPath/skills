#!/usr/bin/env python3
"""NonCatalogHttpFallback (BPMN): connector-mode HTTP request to a non-catalog
service (Spotify), through the generic HTTP connector.

Ported from Flow `connector_features/non-catalog-http-fallback/
check_non_catalog_http_fallback.py`: same scenario (Spotify has no
``uipath-spotify`` IS connector; the only managed path is the generic HTTP
connector ``uipath-uipath-http``, whose own connection instance holds
Spotify's base URL + OAuth), translated from a JSON node/``inputs.detail``
walk to an XML walk over the registry-driven ``Intsvc.ActivityExecution``
connector shell (skills/uipath-maestro-bpmn/references/registry-workflow.md
§"Connectionless vs connector HTTP").

Assertion map (Flow -> BPMN):
  F check_non_catalog_http_fallback.py:_is_http_connector_fallback (node type)          -> sendTask carrying Intsvc.ActivityExecution (only -- see WRAPPER below)
  F check_non_catalog_http_fallback.py:_is_http_connector_fallback (auth=="connector")  -> a context `connectorKey` input is present on the node (connector-backed auth, not a raw literal request)
  F check_non_catalog_http_fallback.py:_is_http_connector_fallback (uses_http_connector)-> connectorKey == "uipath-uipath-http"
  F check_non_catalog_http_fallback.py:_connection_bound                                -> `connection` (or `connectionId`) context value is non-empty and not the literal "ImplicitConnection" sentinel
  F check_non_catalog_http_fallback.py:_targets_me_endpoint                             -> a `path`/`url` context field, or a `path`/`url` key in the request body decoded by bpmn_check.body_object(), ends with "/me"
  I                locate/parse .bpmn                                                   -> parse_bpmn("SpotifyProfileTest")
  T                connector-mode wrapper is Intsvc.ActivityExecution                   -> is_http_connector_node() requires ACTIVITY_TYPE, then
                                                                                            connectorKey + a bound connection (see WRAPPER below)
  T                collect uipath:input elements at any depth under the node            -> context_value()/body_object() walk `.//uipath:input`
  T                endpoint value found in either a sibling context field or inside      -> target_paths()
                   the request body (the skill does not pin where it lands)
  T                body must be one target="body" JSON object → bpmn_check.body_object() -> several inputs fail that node (the runtime does not merge them)

WRAPPER: only `Intsvc.ActivityExecution` is accepted. registry-workflow.md
§"Connectionless vs connector HTTP" (line 342) reserves `Intsvc.HttpExecution`
for connectionless/manual calls -- its `mode` context field is hardcoded to
"manual" with no connector-authenticated alternative -- so connector-mode HTTP
never validates under that wrapper. The CI-passing artifact from run
35500726138 confirms the shape: `Intsvc.ActivityExecution` with connectorKey
`uipath-uipath-http`, a bound `=bindings.<id>` connection, and the Spotify
path inside the `target="body"` JSON. An earlier version of this grader also
accepted `Intsvc.HttpExecution` on the strength of a porting-brief guess that
no skill reference supported; that alternative is withdrawn.

No Flow assertions were dropped -- all five of Flow's structural checks (node
type, connector-backed auth, HTTP connector key, connection bound, "/me"
endpoint) have a BPMN counterpart above.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_non_catalog_http_fallback.py check_fallback
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    BodyShapeError,
    body_object,
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
# Connector-mode wrapper only; Intsvc.HttpExecution is connectionless/manual
# (registry-workflow.md:342), see WRAPPER in the module docstring.
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
_IMPLICIT_CONNECTION = "implicitconnection"


def is_bound_connection(value: str) -> bool:
    value = value.strip()
    return bool(value) and value.lower() != _IMPLICIT_CONNECTION


def is_http_connector_node(task: ET.Element) -> bool:
    """True when ``task`` is a connector-mode node backed by the generic
    ``uipath-uipath-http`` connector with a real (non-implicit) connection
    bound -- the non-catalog fallback shape."""
    if not has_type(task, ACTIVITY_TYPE):
        return False
    connector_key = context_value(task, "connectorKey").lower()
    if connector_key != HTTP_CONNECTOR_KEY:
        return False
    connection_val = context_value(task, "connection") or context_value(task, "connectionId")
    return is_bound_connection(connection_val)


def target_paths(task: ET.Element) -> list[str]:
    candidates: list[str] = []
    for field in ("path", "url"):
        value = context_value(task, field)
        if value:
            candidates.append(value)
    body = body_object(task)
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
                context_value(t, "connectorKey")
                for t in send_tasks
                if has_type(t, ACTIVITY_TYPE)
            }
        )
        fail(
            "No managed HTTP-request node using the generic "
            f"{HTTP_CONNECTOR_KEY!r} connector with a bound connection was "
            "found. Spotify is not a catalog connector, so the process must "
            "issue a connector-mode Intsvc.ActivityExecution request bound "
            f"to a {HTTP_CONNECTOR_KEY!r} connection. connectorKey values "
            f"seen: {seen}"
        )
    print(
        f"OK: {len(fallback_nodes)} managed-HTTP node(s) bound to "
        f"{HTTP_CONNECTOR_KEY!r} with a connection present"
    )

    body_errors: list[str] = []
    targets_me = False
    for t in fallback_nodes:
        try:
            if targets_me_endpoint(t):
                targets_me = True
                break
        except BodyShapeError as exc:
            body_errors.append(f"{t.attrib.get('id', '?')}: {exc}")
    if not targets_me:
        fail(
            f"No {HTTP_CONNECTOR_KEY!r} node targets the {ME_ENDPOINT!r} "
            "endpoint (expected the Spotify '/me' path, which returns the "
            f"current user's profile). Body errors: {body_errors}"
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
