#!/usr/bin/env python3
"""WebhookSelfTest (BPMN): structural check for a two-branch self-testing process.

Ported from Flow `connector_trigger/webhook_waitfor_parallel.yaml`'s
`check_webhook_waitfor_parallel.py`. The process must be:

  manual start (bpmn:startEvent, no event definition)
    -> fan-out into TWO branches
         |-- branch 1: bpmn:receiveTask carrying the registry Intsvc.WaitForEvent
         |   wrapper, bound to the HTTP Webhook connector (connectorKey
         |   uipath-http-webhook) -> end
         `-- branch 2: bpmn:sendTask carrying the registry Intsvc.HttpExecution
             wrapper, manual (connectionless) GET whose url is that connection's
             webhook URL, with nothing in headers or query parameters -> end

Branch 2's GET hits the webhook URL, which delivers the event that completes
branch 1's wait -- so the process self-triggers at runtime. This checker
validates the static two-branch shape only; it does not run `bpmn debug`.

Assertion map (Flow -> BPMN):
  F check_webhook_waitfor_parallel.py:74-85   start trigger fans out into >=2 branches    -> fan_out_point()
  F check_webhook_waitfor_parallel.py:87-98   HTTP Webhook Wait-for-event node exists     -> wait_for_event_nodes()
  F check_webhook_waitfor_parallel.py:100-144 manual GET to webhook URL, no headers/query -> http_get_nodes()
  F check_webhook_waitfor_parallel.py:146-157 both branch tails reach an End node         -> reachable() vs end_ids
  I                                            locate/parse .bpmn                          -> parse_bpmn()
  T  Flow's `core.trigger.*` marker for "start trigger preserved" -> a manual bpmn:startEvent
     (no event definition) -- the fan-out must originate downstream of it, not replace it.
  T  Flow's raw start-trigger fan-out (>=2 outgoing edges straight off the trigger node) ->
     the documented BPMN construct for a parallel fork (structural-bpmn.md "Parallel (AND):
     fork = one in, many out"): accept either (a) the manual start itself carrying >=2
     outgoing sequence flows, or (b) a bpmn:parallelGateway downstream of the manual start
     with >=2 outgoing sequence flows -- whichever the skill's authoring produces, mirroring
     the same curated-or-generic dual tolerance the batch's connector checks use elsewhere.
  T  Flow's node-`type` substring match (`uipath.connector.event` + `uipath-http-webhook`) ->
     bpmn:receiveTask carrying the registry Intsvc.WaitForEvent wrapper (uipath:event, per
     references/registry-workflow.md's OOTB extension-type table) with context connectorKey
     == "uipath-http-webhook" -- the same connector-key literal Flow's own node-type marker
     embeds.
  T  Flow's `core.action.http` / `core.action.http.v2` manual-GET-to-webhook-URL node shape ->
     bpmn:sendTask carrying the registry Intsvc.HttpExecution wrapper (uipath:activity, per
     the registry's own xmlTemplate: context fields mode/method/url/headers/parameters/body)
     with mode=manual, method=GET, url containing "webhook", and no populated "headers" or
     "parameters" context field -- the same "nothing in headers or query" rule Flow enforced,
     read from the BPMN context fields instead of a JSON body dict.
  DROPPED  require_no_private_connector_values / require_sequence_integrity /
           require_di_for_visible_elements / connection-binding check (not in Flow; the
           `bpmn validate` criterion in the task YAML covers structure, and this connector has
           no real tenant connection id to leak in a draft-authoring eval)
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    context_value,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
)
from _shared.graph import reachable  # noqa: E402

BPMN_NS = NS["bpmn"]
WAIT_TYPE = "Intsvc.WaitForEvent"
HTTP_TYPE = "Intsvc.HttpExecution"
# registry-workflow.md lists both wrappers for the managed HTTP sendTask; the
# eval agent emitted UnifiedHttpRequest on CI run 35538279757.
HTTP_TYPES = (HTTP_TYPE, "Intsvc.UnifiedHttpRequest")
CONNECTOR_KEY = "uipath-http-webhook"


def manual_start_events(root: ET.Element) -> list[ET.Element]:
    """bpmn:startEvent with no event-definition child -- the closest BPMN analog
    of Flow's `core.trigger.*` marker: a plain, non-connector manual start."""
    out = []
    for s in elements(root, "startEvent"):
        if not any(
            child.tag.startswith(f"{{{BPMN_NS}}}") and child.tag.endswith("EventDefinition")
            for child in s
        ):
            out.append(s)
    return out


def _is_empty_json_field(value: str) -> bool:
    """True when a headers/parameters context field carries nothing -- absent,
    blank, `{}`/`[]`, or `null` (an unfilled registry template placeholder is
    not the same as a populated one)."""
    text = (value or "").strip()
    if not text:
        return True
    if text.lower() == "null":
        return True
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return False  # non-empty, non-JSON text is a populated value
    if isinstance(parsed, dict):
        return not parsed
    if isinstance(parsed, list):
        return not parsed
    return False


def fan_out_point(root: ET.Element, start_id: str) -> str | None:
    """Id of the node from which >=2 independent branches originate: either the
    manual start itself, or a bpmn:parallelGateway downstream of it (the
    documented parallel-fork construct)."""
    downstream = reachable(root, start_id)
    candidates = [start_id, *(attr(gw, "id") for gw in elements(root, "parallelGateway"))]
    for node_id in candidates:
        if node_id != start_id and node_id not in downstream:
            continue
        out_flows = [f for f in elements(root, "sequenceFlow") if attr(f, "sourceRef") == node_id]
        if len(out_flows) >= 2:
            return node_id
    return None


def wait_for_event_nodes(root: ET.Element) -> list[ET.Element]:
    """Element carrying the registry Intsvc.WaitForEvent wrapper, bound to the
    HTTP Webhook connector. Classified by the wrapper type, not the BPMN tag:
    the skill teaches ``bpmn:receiveTask``, but the eval agent also emits a
    validating ``bpmn:intermediateCatchEvent`` + messageEventDefinition with
    the same wrapper (CI run 35538279757), as it did for Intsvc.EventTrigger
    in trigger_lifecycle."""
    out = []
    for task in list(elements(root, "receiveTask")) + list(elements(root, "intermediateCatchEvent")):
        if not has_typed_uipath_extension(task, "event", WAIT_TYPE):
            continue
        if context_value(task, "connectorKey") != CONNECTOR_KEY:
            continue
        out.append(task)
    return out


def http_get_nodes(root: ET.Element) -> list[ET.Element]:
    """bpmn:sendTask carrying Intsvc.HttpExecution, manual GET to a webhook
    URL, with nothing in headers or query parameters."""
    good = []
    for task in elements(root, "sendTask"):
        if not any(has_typed_uipath_extension(task, "activity", t) for t in HTTP_TYPES):
            continue
        mode = context_value(task, "mode").lower()
        method = context_value(task, "method").upper()
        url = context_value(task, "url")
        if mode != "manual" or method != "GET":
            continue
        if "webhook" not in url.lower():
            continue
        headers = context_value(task, "headers")
        params = context_value(task, "parameters")
        if not _is_empty_json_field(headers):
            fail(f"HTTP node must not set headers; found: {headers!r}")
        if not _is_empty_json_field(params):
            fail(f"HTTP node must not set query parameters; found: {params!r}")
        good.append(task)
    return good


def main() -> None:
    path, root = parse_bpmn("WebhookSelfTest")

    starts = manual_start_events(root)
    if not starts:
        fail(
            "no manual bpmn:startEvent (no event definition) -- the wait-for-event and "
            "HTTP-request branches must fan out from the manual start, not replace it"
        )
    start_id = attr(starts[0], "id")

    if fan_out_point(root, start_id) is None:
        fail(
            "manual start does not fan out into >=2 branches -- expected either the start "
            "event itself or a downstream bpmn:parallelGateway to carry >=2 outgoing "
            "sequence flows for the wait-for-event and HTTP-request branches"
        )
    print(f"OK: manual start {start_id!r} fans out into >=2 branches")

    event_nodes = wait_for_event_nodes(root)
    if not event_nodes:
        fail(
            f"no bpmn:receiveTask or intermediateCatchEvent carrying {WAIT_TYPE} bound to connectorKey "
            f"{CONNECTOR_KEY!r} (HTTP Webhook wait-for-event)"
        )
    print("OK: HTTP Webhook wait-for-event receiveTask present")

    http_nodes = http_get_nodes(root)
    if not http_nodes:
        fail(
            f"no bpmn:sendTask carrying {' or '.join(HTTP_TYPES)} configured as a manual GET to the "
            "webhook URL (mode=manual, method=GET, url containing 'webhook', "
            "no populated headers/parameters context field)"
        )
    print("OK: manual GET HttpExecution sendTask to webhook URL, no headers/query")

    end_ids = {attr(e, "id") for e in elements(root, "endEvent")}
    if not end_ids:
        fail("no end event")

    for label, node in (("wait-for-event", event_nodes[0]), ("http-request", http_nodes[0])):
        node_id = attr(node, "id")
        reach = reachable(root, node_id)
        if not (reach & end_ids):
            fail(f"{label} branch does not reach an end event")
    print("OK: both branches terminate at an end event")

    print(
        f"OK: {path} fans a manual start into an HTTP Webhook wait-for-event branch "
        "and a manual-GET-to-webhook-URL branch, both terminating at an end event"
    )


if __name__ == "__main__":
    main()
