#!/usr/bin/env python3
"""OutlookTriggerInbox (BPMN): regression port of Flow PR #348 — reference-ID reuse.

Ported from Flow `single_node/outlook_trigger_inbox/outlook_trigger_inbox.yaml`'s
``check_outlook_trigger_inbox.py``: same three-check scenario (trigger node
present; connection + MailFolder reference both bound; the bound
``parentFolderId`` is a LIVE MailFolder id on the currently-bound Outlook
connection, not a cached/stale/renamed one), translated from a JSON
``inputs.detail`` walk over a ``.flow`` node to an XML ``uipath:input`` walk
over the registry-driven ``Intsvc.EventTrigger`` startEvent shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md "Integration
Service triggers" and ``validator/bpmn-spec.json``'s ``Intsvc.EventTrigger``
xmlTemplate).

A ``bpmn debug`` step is intentionally omitted, for the same infrastructure
reason as the Flow original: see this task's YAML description.

Re-homing decisions vs the Flow grader:
  - Flow's ``node.type`` suffix match
    (``uipath.connector.trigger.uipath-microsoft-outlook365.email-received``)
    becomes: a ``bpmn:startEvent`` carrying ``Intsvc.EventTrigger`` +
    ``bpmn:messageEventDefinition``, whose context ``connectorKey`` ==
    ``uipath-microsoft-outlook365`` and whose ``objectName``/``operation``
    (or, failing that, any input value on the node) matches
    ``email[-_ ]?receiv`` case-insensitively — the registry's exact
    operation-string spelling for this event is CLI-owned enrichment, not
    pinned by the skill docs.
  - Flow's direct field read ``trigger.inputs.detail.connectionId`` becomes:
    the startEvent's ``connectionId`` context input, resolved through the
    BPMN connection-binding indirection (``=bindings.<id>`` -> process-level
    ``<uipath:binding id="<id>" resource="Connection"
    propertyAttribute="ConnectionId" ...>``, per registry-workflow.md
    section 4 "Bindings") when the value takes that form, or used literally
    when the agent wrote a raw connection id straight into the field.
  - Flow's ``trigger.inputs.detail.eventParameters.parentFolderId`` becomes:
    a ``uipath:input`` named ``parentFolderId`` anywhere under the
    startEvent's ``uipath:event`` payload — the registry's generic
    ``Intsvc.EventTrigger`` schema does not pin where an Outlook-specific
    event field lands once enriched (BATCH1-ADDENDUM.md's "inputs at any
    depth" tolerance) — with a fallback into a JSON-typed ``filter`` or
    ``parameters`` input if the field was folded into one of those instead
    of emitted as its own input.
  - Flow's own CLI-shape checks (verb-tolerant ``resources run``/``execute``,
    PascalCase ``Id`` key, environment-vs-regression failure
    classification, privacy-safe error messages, the folder-default
    fallback via ``Shared/uipath-maestro-flow`` — the tenant fixture folder,
    not the eval suite) are unchanged: they grade a live ``uip`` CLI
    response, not the artifact, so switching from ``.flow`` JSON to
    ``.bpmn`` XML does not touch them.

Assertion map (Flow -> BPMN):
  F check_outlook_trigger_inbox.py:169-176 (Flow) trigger node type match  -> is_email_received_trigger() + _find_email_trigger()
  F check_outlook_trigger_inbox.py:197-209 (Flow) check_folder_binding     -> check_folder_binding()
  F check_outlook_trigger_inbox.py:138-147 (Flow) _bound_connection_id     -> _bound_connection_value() + _resolve_binding()
  F check_outlook_trigger_inbox.py:211-277 (Flow) check_folder_id_fresh   -> check_folder_id_fresh() (CLI classification logic ported verbatim)
  I                                   locate/parse .bpmn                   -> parse_bpmn()
  I                                   resolve `=bindings.<id>` to a live connection id -> _resolve_binding()
  T                                   connectorKey/objectName/operation match at any input depth, case/hyphen-insensitive -> is_email_received_trigger()
  T                                   parentFolderId input at any depth, or inside a JSON filter/parameters blob -> find_parent_folder_id()
  T                                   connectionId as a literal value OR the `=bindings.<id>` indirection -> _bound_connection_value()/_resolve_binding()
  DROPPED  require_no_private_connector_values / require_sequence_integrity / require_di_for_visible_elements  (not in Flow; the `validate` criterion already covers structure)
  DROPPED  "no manual start coexists" / "exactly one trigger start" / "trigger is process entry (no inbound flow)"  (Flow's check_trigger_node only asserts the trigger node exists; it never asserted exclusivity or process-entry position)

Privacy: never logs folder display names, nor the configured reference value
(which may itself be a name). Only counts and lengths — same policy as the
Flow original.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
)

BPMN_NS = NS["bpmn"]
CONNECTOR_KEY = "uipath-microsoft-outlook365"
TRIGGER_TYPE = "Intsvc.EventTrigger"
TEST_FOLDER_PATH = "Shared/uipath-maestro-flow"
EMAIL_RECEIVED_RE = re.compile(r"email[-_ ]?receiv", re.IGNORECASE)


# Credential failures: the tenant's grant, not anything the agent built.
_CONNECTION_DEAD_MARKERS = (
    "invalid_grant",
    "aadsts50173",  # grant revoked
    "aadsts700082",  # refresh token expired
    "reauthorize your account",
)


def _connection_is_dead(blob: str) -> bool:
    lowered = blob.lower()
    return any(marker in lowered for marker in _CONNECTION_DEAD_MARKERS)


def _dead_credential_remedy(args: list[str]) -> str:
    """Which credential to reauthorize. The MailFolder resolve runs on the
    Outlook connection's grant; every other call in this checker (`or folders
    get`, `is connections list`) runs on the CLI's own session. Both are
    environment failures, but they are fixed in different places, so a dead CLI
    login must not be reported as a dead Outlook connection."""
    if "resources" in args:
        return (
            "The tenant's Outlook connection cannot authenticate, so no MailFolder ID "
            "can be resolved and this task's assertion never ran. Reauthorize the "
            f"connection in {TEST_FOLDER_PATH} and re-run"
        )
    return (
        "The CLI's own session cannot authenticate, so this checker never reached the "
        "MailFolder resolve. Re-run `uip login` and re-run this task"
    )


def _parse_uip_stdout(args: list[str], result: subprocess.CompletedProcess) -> dict:
    if result.returncode != 0:
        blob = f"{result.stdout}\n{result.stderr}"
        if _connection_is_dead(blob):
            sys.exit(
                f"FAIL (ENVIRONMENT, not a skill regression): {' '.join(args)} "
                f"exit={result.returncode}. {_dead_credential_remedy(args)}; do not "
                "read this as the agent reusing or inventing an ID.\n"
                f"stderr: {result.stderr}\nstdout: {result.stdout}"
            )
        sys.exit(
            f"FAIL: {' '.join(args)} exit={result.returncode}\n"
            f"stderr: {result.stderr}\nstdout: {result.stdout}"
        )
    # Strip any CLI banner lines preceding the JSON body
    out = result.stdout
    idx = out.find("{")
    if idx < 0:
        sys.exit(f"FAIL: no JSON in stdout of {' '.join(args)}\n{out}")
    try:
        return json.loads(out[idx:])
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: JSON parse error on {' '.join(args)}: {e}\n{out}")


def _uip_json(args: list[str]) -> dict:
    """Run a uip CLI command and return parsed JSON. Fails the test on
    non-zero exit or invalid JSON."""
    return _parse_uip_stdout(args, subprocess.run(args, capture_output=True, text=True, timeout=120))


def _uip_resources_run(tail_args: list[str]) -> dict:
    """Invoke ``uip is resources <verb> <tail...>`` tolerating both the
    post-rename verb (``run``, current) and the legacy verb (``execute``).

    Sandboxes can carry either CLI version depending on which
    @uipath/integrationservice-tool install ranks first in Node's
    parent-walking module resolution. The fallback on
    ``unknown command 'run'`` keeps the checker green across both shapes
    until the sandbox PATH is fully isolated (see coder_eval companion PR).
    """
    primary = ["uip", "is", "resources", "run", *tail_args]
    result = subprocess.run(primary, capture_output=True, text=True, timeout=120)
    needs_fallback = (
        result.returncode != 0
        and "unknown command 'run'" in (result.stdout + result.stderr)
    )
    if needs_fallback:
        legacy = ["uip", "is", "resources", "execute", *tail_args]
        result = subprocess.run(legacy, capture_output=True, text=True, timeout=120)
        return _parse_uip_stdout(legacy, result)
    return _parse_uip_stdout(primary, result)


def _find_test_folder_key() -> str:
    resp = _uip_json(["uip", "or", "folders", "get", TEST_FOLDER_PATH, "--output", "json"])
    key = resp.get("Data", {}).get("Key")
    if not key:
        sys.exit(f"FAIL: no '{TEST_FOLDER_PATH}' folder in Orchestrator")
    return key


def _find_default_outlook_connection() -> tuple[str, str, str]:
    """Return (connection_id, folder_key, connection_name) for the default
    enabled Outlook connection in the test folder."""
    folder_key = _find_test_folder_key()
    conns_raw = _uip_json(
        [
            "uip", "is", "connections", "list", CONNECTOR_KEY,
            "--folder-key", folder_key, "--output", "json",
        ]
    ).get("Data", [])
    if not isinstance(conns_raw, list) or not conns_raw:
        sys.exit(
            f"FAIL: no {CONNECTOR_KEY} connection in folder {TEST_FOLDER_PATH}. "
            f"Provision an Outlook connection in the test tenant first."
        )
    defaults = [c for c in conns_raw if c.get("IsDefault") == "Yes" and c.get("State") == "Enabled"]
    chosen = defaults[0] if defaults else conns_raw[0]
    return chosen["Id"], folder_key, chosen.get("Name", "")


def _extract_list_items(resp: dict) -> list[dict]:
    """resources run list returns Data shaped as either {items: [...], Pagination: ...}
    or a plain list. Handle both."""
    data = resp.get("Data", [])
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        return [x for x in (data.get("items") or data.get("Items") or []) if isinstance(x, dict)]
    return []


# ── XML helpers ──────────────────────────────────────────────────────────
def node_inputs(el: ET.Element) -> list[ET.Element]:
    return el.findall(".//uipath:input", NS)


def all_node_values(el: ET.Element) -> list[str]:
    values: list[str] = []
    for inp in node_inputs(el):
        v = inp.attrib.get("value")
        if v:
            values.append(v)
        if inp.text and inp.text.strip():
            values.append(inp.text.strip())
    return values


def node_blob(el: ET.Element) -> str:
    return " ".join(all_node_values(el)).lower()


def context_value(el: ET.Element, name: str) -> str:
    for inp in node_inputs(el):
        if inp.attrib.get("name", "").lower() == name.lower():
            return inp.attrib.get("value") or (inp.text or "")
    return ""


def trigger_start_events(root: ET.Element) -> list[ET.Element]:
    return [
        s
        for s in elements(root, "startEvent")
        if has_typed_uipath_extension(s, "event", TRIGGER_TYPE)
        and s.find(f"{{{BPMN_NS}}}messageEventDefinition") is not None
    ]


def is_email_received_trigger(start: ET.Element) -> bool:
    if context_value(start, "connectorKey") != CONNECTOR_KEY:
        return False
    for field in ("objectName", "operation"):
        v = context_value(start, field)
        if v and EMAIL_RECEIVED_RE.search(v):
            return True
    # Tolerant fallback: the event name may land under a different context
    # field name once the CLI enriches the trigger.
    return bool(EMAIL_RECEIVED_RE.search(node_blob(start)))


def _find_email_trigger(root: ET.Element) -> ET.Element:
    starts = trigger_start_events(root)
    candidates = [s for s in starts if is_email_received_trigger(s)]
    if not candidates:
        fail(
            f"no bpmn:startEvent carrying {TRIGGER_TYPE} + messageEventDefinition for "
            f"{CONNECTOR_KEY} email-received; trigger starts seen: {[attr(s, 'id') for s in starts]}"
        )
    return candidates[0]


def _bound_connection_value(trigger: ET.Element) -> str:
    """Mirrors Flow's ``_bound_connection_id``: the connection the trigger is
    actually bound to. In BPMN this is the startEvent's ``connectionId``
    context input — either a raw connection id, or the standard
    ``=bindings.<id>`` indirection (registry-workflow.md section 4), which
    ``_resolve_binding`` follows to the process-level ``<uipath:binding>``'s
    real connection id. Unlike Flow (where `node configure` requires the
    field once the flow validates), BPMN's `validate` passes even with an
    unmaterialized connection binding (registry-workflow.md: error 102010 is
    a runtime-only fault) — so falling back to the folder default when this
    is empty is still necessary here, not just defensive."""
    raw = context_value(trigger, "connectionId")
    return raw.strip() if isinstance(raw, str) else ""


def _resolve_binding(root: ET.Element, value: str) -> str:
    """Resolve a ``=bindings.<id>`` reference to its declared connection id.
    A literal (non-indirected) value is returned unchanged — Flow's own
    grader never required the bindings indirection, only a bound connection
    (BATCH1-ADDENDUM.md T: the binding form is CLI/skill plumbing, not a
    Flow-graded fact)."""
    m = re.match(r"^=bindings\.(\S+)$", value.strip())
    if not m:
        return value
    binding_id = m.group(1)
    for binding in root.findall(".//uipath:binding", NS):
        if (
            binding.attrib.get("id") == binding_id
            and binding.attrib.get("propertyAttribute", "").lower() == "connectionid"
        ):
            resolved = binding.attrib.get("resourceKey") or binding.attrib.get("default") or ""
            if resolved:
                return resolved
    sys.exit(
        f"FAIL: trigger connectionId references binding {binding_id!r}, which has no "
        "resolvable Connection binding declared in the process-level uipath:bindings"
    )


def find_parent_folder_id(trigger: ET.Element) -> str:
    """Mirrors Flow's ``eventParameters.parentFolderId`` read. The registry's
    generic Intsvc.EventTrigger schema does not pin where an Outlook-specific
    event field lands once enriched, so search (in order): a same-named
    ``uipath:input`` anywhere under the node, then a ``filter``/``parameters``
    input whose value/text parses as JSON with that key."""
    for inp in node_inputs(trigger):
        if inp.attrib.get("name", "").lower() == "parentfolderid":
            v = inp.attrib.get("value") or (inp.text or "")
            if v.strip():
                return v.strip()
    for inp in node_inputs(trigger):
        if inp.attrib.get("name", "").lower() not in ("filter", "parameters"):
            continue
        raw = inp.attrib.get("value") or (inp.text or "")
        if not raw or not raw.strip():
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            for key, val in parsed.items():
                if key.lower() == "parentfolderid" and isinstance(val, str) and val.strip():
                    return val.strip()
    return ""


# ── subcommand: check_trigger_node ─────────────────────────────────────
def check_trigger_node() -> None:
    _, root = parse_bpmn("OutlookTriggerInbox")
    _find_email_trigger(root)
    print("OK: Outlook email-received trigger start event present")


def check_folder_binding() -> None:
    _, root = parse_bpmn("OutlookTriggerInbox")
    trigger = _find_email_trigger(root)
    connection_value = _bound_connection_value(trigger)
    parent_folder_id = find_parent_folder_id(trigger)
    if not connection_value:
        fail("trigger startEvent's connectionId context input is missing")
    if not parent_folder_id:
        fail("trigger startEvent has no parentFolderId event parameter configured")
    print("OK: Outlook connection and MailFolder reference are both bound")


# ── subcommand: check_folder_id_fresh ──────────────────────────────────
def check_folder_id_fresh() -> None:
    _, root = parse_bpmn("OutlookTriggerInbox")
    trigger = _find_email_trigger(root)

    process_folder_id = find_parent_folder_id(trigger)
    if not process_folder_id:
        sys.exit(
            "FAIL: trigger startEvent has no parentFolderId event parameter configured. "
            "The agent did not configure the required reference field."
        )

    # Prefer the trigger's own binding; fall back to the folder default only
    # when the process never persisted one.
    bound = _bound_connection_value(trigger)
    conn_id = _resolve_binding(root, bound) if bound else ""
    if not conn_id:
        conn_id = _find_default_outlook_connection()[0]

    live = _uip_resources_run(
        ["list", CONNECTOR_KEY, "MailFolder", "--connection-id", conn_id, "--output", "json"]
    )
    # Read the item id case-insensitively (a CLI that PascalCases --output json
    # keys per PR #2266 emits `Id`, not `id`) and drop any None so a missed key
    # can't collapse the set to `{None}` and falsely accuse the agent.
    live_ids = {
        fid
        for f in _extract_list_items(live)
        if (fid := (f.get("id") or f.get("Id")))
    }
    if not live_ids:
        sys.exit(
            "FAIL: resources run/execute list MailFolder returned no folders on the bound connection"
        )

    if process_folder_id in live_ids:
        print(f"OK: parentFolderId resolves on current connection ({len(live_ids)} folders checked)")
        return

    # describe declares Reference{LookupNames:["displayName"], LookupValue:"id"},
    # so a display name here means the resolve was skipped, not a stale id.
    live_names = {
        name.lower()
        for f in _extract_list_items(live)
        if (name := (f.get("displayName") or f.get("DisplayName")))
    }
    if process_folder_id.lower() in live_names:
        sys.exit(
            "FAIL: parentFolderId holds a folder's displayName, not its id. The field "
            "is a reference (LookupNames=[displayName], LookupValue=id), so the agent "
            "must write the `id` returned by `resources run list MailFolder`. This is a "
            "skipped or failed resolve, NOT the PR #348 stale-reference regression."
        )

    # The configured value is never echoed, not even truncated: reaching here
    # means it matched no live id AND no live display name, so it can still BE a
    # display name (a renamed or deleted folder, or one past the returned page).
    # Report its shape instead.
    sys.exit(
        f"FAIL (PR #348 regression): the configured parentFolderId ({len(process_folder_id)} chars) "
        f"is not among the {len(live_ids)} MailFolder IDs on the bound connection, and is not "
        "one of their display names either. The agent reused a reference ID from another "
        "connection or session."
    )


DISPATCH = {
    "check_trigger_node": check_trigger_node,
    "check_folder_binding": check_folder_binding,
    "check_folder_id_fresh": check_folder_id_fresh,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.exit(f"usage: {sys.argv[0]} {{{'|'.join(DISPATCH)}}}")
    DISPATCH[sys.argv[1]]()


if __name__ == "__main__":
    main()
