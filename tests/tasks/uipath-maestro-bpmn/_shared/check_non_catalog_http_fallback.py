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
  F check_non_catalog_http_fallback.py:_is_http_connector_fallback (node type)          -> sendTask carrying Intsvc.ActivityExecution or Intsvc.HttpExecution
  F check_non_catalog_http_fallback.py:_is_http_connector_fallback (auth=="connector")  -> a context `connectorKey` input is present on the node (connector-backed auth, not a raw literal request)
  F check_non_catalog_http_fallback.py:_is_http_connector_fallback (uses_http_connector)-> connectorKey == "uipath-uipath-http"
  F check_non_catalog_http_fallback.py:_connection_bound                                -> `connection` (or `connectionId`) context value is non-empty and not the literal "ImplicitConnection" sentinel
  F check_non_catalog_http_fallback.py:_targets_me_endpoint                             -> a `path`/`url` context field, or a `path`/`url` key inside the single `target="body"` JSON payload, ends with "/me"
  I                locate/parse .bpmn                                                   -> parse_bpmn("SpotifyProfileTest")
  T                curated (Intsvc.ActivityExecution) OR the connector-authenticated     -> is_http_connector_node() classifies by connectorKey + bound
                   form of Intsvc.HttpExecution -- accept either wrapper tag                connection, not by which wrapper tag hosts them (see GUESS below)
  T                collect uipath:input elements at any depth under the node            -> context_inputs() uses `.//uipath:input`
  T                endpoint value found in either a sibling context field or inside      -> target_paths()
                   the body CDATA JSON (the skill does not pin where it lands)

GUESS (flag for reviewer): registry-workflow.md documents `Intsvc.HttpExecution`'s
`mode` context field as hardcoded to "manual" (hidden, defaultValue "manual") with
no documented connector-authenticated alternative -- the skill's own contract
splits connector-mode HTTP as `Intsvc.ActivityExecution` (connectorKey=
uipath-uipath-http) and reserves `Intsvc.HttpExecution` for connectionless/manual
calls only. The "connector-authenticated Intsvc.HttpExecution" form named in the
porting brief was not found documented anywhere under skills/uipath-maestro-bpmn;
it echoes a same-named but distinct JSON API-workflow concept
(skills/uipath-troubleshoot/.../connection-auth-failure.md: bodyParameters
`authentication: "connector"` + `targetConnector`), not a BPMN registry field.
To stay faithful to both instructions without inventing a hard requirement on
one tag name, this checker classifies purely by `connectorKey` + a bound
connection, and accepts either wrapper tag carrying them -- the skill-documented
`Intsvc.ActivityExecution` shape passes squarely; a hypothetical
`Intsvc.HttpExecution` node carrying the same fields would also pass, but no
skill reference was found describing agents actually authoring it that way.

No Flow assertions were dropped -- all five of Flow's structural checks (node
type, connector-backed auth, HTTP connector key, connection bound, "/me"
endpoint) have a BPMN counterpart above.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_non_catalog_http_fallback.py check_fallback
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import NS, elements, fail, parse_bpmn  # noqa: E402

PROJECT_NAME_HINT = "SpotifyProfileTest"
# The generic HTTP connector -- the only managed path to a service with no
# catalog connector of its own.
HTTP_CONNECTOR_KEY = "uipath-uipath-http"
# Spotify "Get Current User's Profile" endpoint.
ME_ENDPOINT = "/me"
ACTIVITY_TYPES = ("Intsvc.ActivityExecution", "Intsvc.HttpExecution")
_IMPLICIT_CONNECTION = "implicitconnection"


def has_type(el: ET.Element, token: str) -> bool:
    return token in ET.tostring(el, encoding="unicode")


def context_inputs(task: ET.Element) -> list[ET.Element]:
    # `.//` walks every uipath:input under the node at any depth -- agents
    # sometimes nest body/query/path inputs inside uipath:context.
    return task.findall(".//uipath:input", NS)


def context_value(task: ET.Element, name: str) -> str:
    for inp in context_inputs(task):
        if inp.attrib.get("name") == name:
            return (inp.attrib.get("value") or inp.text or "").strip()
    return ""


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
                context_value(t, "connectorKey")
                for t in send_tasks
                if any(has_type(t, token) for token in ACTIVITY_TYPES)
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
