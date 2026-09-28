#!/usr/bin/env python3
"""OutlookWaitForEmail (BPMN): structural check (no execution).

Ported from Flow
`single_node/outlook_waitfor_email/check_outlook_waitfor_email.py`. The
process must be:

  manual start (bpmn:startEvent, no event definition)
    -> mid-flow bpmn:receiveTask carrying the registry Intsvc.WaitForEvent
       wrapper (Outlook 365 email-received event), filtered to SUBJECT
       CONTAINS "TestWaitFor"
    -> end

`bpmn debug` is intentionally NOT run -- the task only requires the process to
build and validate. Every assertion here is static, read from the `.bpmn`
source (see skills/uipath-maestro-bpmn/references/registry-workflow.md on
`Intsvc.WaitForEvent` / connector-wait enrichment, and its "Wait for connector
event" xmlTemplate in skills/uipath-maestro-bpmn/validator/bpmn-spec.json).

Assertion map (Flow -> BPMN):
  F check_outlook_waitfor_email.py:107      start trigger preserved (core.trigger.*)            -> manual_start_events()
  F check_outlook_waitfor_email.py:114-123  Outlook email-received Wait-for-event node exists    -> wait_for_event_nodes()
  F check_outlook_waitfor_email.py:125-146  subject / Contains / "TestWaitFor" filter           -> has_subject_contains_filter()
  I                                          locate/parse .bpmn                                   -> parse_bpmn()
  T  connectorKey exact match ("uipath-microsoft-outlook365", the same connector-key literal
     Flow's own node-type marker embeds) + a stemmed, case/dash/underscore-insensitive match on
     "email received" across objectName/operation/the node's full input blob. The exact
     enrichment spelling was not confirmed locally -- no Outlook connection exists on this
     machine (see _porting/BATCH1-ADDENDUM.md) -- so this tolerates EMAIL_RECEIVED, email-received, and
     EmailReceived alike; evidence for EMAIL_RECEIVED as the connector's operation code is
     `outlook_trigger_inbox.yaml`'s `uip is triggers describe ... EMAIL_RECEIVED` discovery
     pattern (same connector, sibling Flow task).
  T  filter: a `contains(subject, 'TestWaitFor')` clause in the `target="body"` input's
     `filters.expression`, the only filter the runtime reads (PO.BpmnEngine
     BpmnInputExtensions.GetEventFilters; Studio Web emits the same body). A filter tree or an
     untargeted `filter`/`filterExpression` input is dropped at runtime, so it does not count.
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    all_node_values,
    context_value,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
)

BPMN_NS = NS["bpmn"]
EVENT_TYPE = "Intsvc.WaitForEvent"
CONNECTOR_KEY = "uipath-microsoft-outlook365"
FILTER_VALUE = "TestWaitFor"
_EMAIL_RECEIVED_STEM = "emailreceiv"
_JSONSTRING_PREFIX = "=jsonstring:"
_SUBJECT_CONTAINS_RE = re.compile(
    rf"(?i:contains)\(\s*(?i:subject)\s*,\s*['\"`]{re.escape(FILTER_VALUE)}['\"`]\s*\)"
)
_NEGATED_PREFIX_RE = re.compile(r"(!|\bnot)[\s(]*$", re.IGNORECASE)
_NEGATED_SUFFIX_RE = re.compile(r"^[\s)]*(==\s*false|!=\s*true)\b", re.IGNORECASE)


def _stem(text: str) -> str:
    return re.sub(r"[^a-z]", "", text.lower())


def node_blob(el: ET.Element) -> str:
    return " ".join(all_node_values(el))


def manual_start_events(root: ET.Element) -> list[ET.Element]:
    """bpmn:startEvent with no event-definition child: the closest BPMN analog
    of Flow's `core.trigger.*` marker -- a plain, non-connector start."""
    out = []
    for s in elements(root, "startEvent"):
        if not any(
            child.tag.startswith(f"{{{BPMN_NS}}}") and child.tag.endswith("EventDefinition")
            for child in s
        ):
            out.append(s)
    return out


def wait_for_event_nodes(root: ET.Element) -> list[ET.Element]:
    """bpmn:receiveTask carrying the registry Intsvc.WaitForEvent wrapper,
    bound to the Outlook 365 connector, for its email-received event."""
    out = []
    for task in elements(root, "receiveTask"):
        if not has_typed_uipath_extension(task, "event", EVENT_TYPE):
            continue
        if context_value(task, "connectorKey") != CONNECTOR_KEY:
            continue
        candidates = [
            context_value(task, "objectName"),
            context_value(task, "operation"),
            node_blob(task),
        ]
        if any(_EMAIL_RECEIVED_STEM in _stem(c) for c in candidates if c):
            out.append(task)
    return out


def _parse_json_value(value: str):
    if not isinstance(value, str):
        return None
    text = value[len(_JSONSTRING_PREFIX):] if value.lower().startswith(_JSONSTRING_PREFIX) else value
    text = text.strip()
    if not text.startswith("{"):
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _filter_expression(body: dict) -> str:
    filters = body.get("filters")
    if isinstance(filters, dict):
        filters = filters.get("expression")
    return filters if isinstance(filters, str) else ""


def _has_positive_subject_clause(expression: str) -> bool:
    for m in _SUBJECT_CONTAINS_RE.finditer(expression):
        if _NEGATED_PREFIX_RE.search(expression[: m.start()]):
            continue
        if _NEGATED_SUFFIX_RE.search(expression[m.end():]):
            continue
        return True
    return False


def _is_folder_scoped(body: dict, expression: str) -> bool:
    params = body.get("queryParams")
    folder_id = params.get("parentFolderId") if isinstance(params, dict) else None
    if not isinstance(folder_id, str) or not folder_id.strip():
        return False
    clause = rf"parentFolderId\s*==\s*['\"]{re.escape(folder_id.strip())}['\"]"
    return bool(re.search(clause, expression))


def has_subject_contains_filter(task: ET.Element) -> bool:
    for inp in task.iter(f"{{{NS['uipath']}}}input"):
        if inp.attrib.get("target") != "body":
            continue
        body = _parse_json_value(inp.attrib.get("value") or inp.text or "")
        if not body:
            continue
        expression = _filter_expression(body)
        if _has_positive_subject_clause(expression) and _is_folder_scoped(body, expression):
            return True
    return False


def main() -> None:
    path, root = parse_bpmn("OutlookWaitForEmail")

    if not manual_start_events(root):
        fail(
            "no manual bpmn:startEvent (no event definition) -- the Wait-for-event "
            "node must be added mid-flow as a bpmn:receiveTask, not replace the "
            "process's manual start"
        )

    event_nodes = wait_for_event_nodes(root)
    if not event_nodes:
        fail(
            f"no bpmn:receiveTask carrying {EVENT_TYPE} bound to connectorKey "
            f"{CONNECTOR_KEY!r} for the email-received event"
        )

    if not any(has_subject_contains_filter(task) for task in event_nodes):
        fail(
            "Outlook email-received receiveTask found, but its target=\"body\" input "
            f"lacks a filters.expression clause contains(subject, {FILTER_VALUE!r}) "
            "scoped by queryParams.parentFolderId and its parentFolderId == clause"
        )

    print(
        f"OK: {path} keeps a manual start; mid-flow Outlook email-received "
        f"receiveTask filters subject Contains {FILTER_VALUE!r}"
    )


if __name__ == "__main__":
    main()
