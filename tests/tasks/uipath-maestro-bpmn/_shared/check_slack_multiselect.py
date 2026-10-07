#!/usr/bin/env python3
"""Slack group-DM multiselect (BPMN): shared grader for `complex_array.yaml`
and `multiselect.yaml`.

Ported from Flow `connector_features/check_multiselect_flow.py`. Same
scenario (a Slack connector node creating a group direct message, whose
`users` field is a multiselect/complex-array of user IDs), re-homed from a
JSON node's `inputs` dict (matched by `"slack" in node.type.lower()`) to a
BPMN `bpmn:sendTask` carrying the registry `Intsvc.ActivityExecution` wrapper
with `connectorKey == uipath-salesforce-slack` (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4). Both Flow
tasks call this same script with the same argv convention (`populated` or an
integer count, default 3), so this one grader is used identically by both
BPMN ports; each task's own `check_<task>.py` handles its remaining,
task-specific criteria (locate/parse, advisory id search).

Assertion map (Flow -> BPMN):
  F check_multiselect_flow.py:86-91   "slack" in node.type.lower()
      -> slack_tasks(): sendTask carrying Intsvc.ActivityExecution with connectorKey == uipath-salesforce-slack
  F check_multiselect_flow.py:93-104  find_users(node.inputs), count/populated
      -> find_users(body_object(task)), same count/populated check
  F check_multiselect_flow.py:26-48   parse_users(): native list, or a string
                                       wrapping an array literal (JSON array or
                                       a `=js:(['U1','U2'])`-style expression)
                                           -> parse_users(): identical regex + ast.literal_eval tolerance
  F check_multiselect_flow.py:51-57   is_users_key(): 'users' with an optional
                                       array-notation suffix                    -> is_users_key(): identical regex
  F check_multiselect_flow.py:60-76   find_users(): recursive dict/list search
      -> find_users(): identical recursive search over the body object
  I   locate/parse .bpmn, no name hint (this script is shared by both tasks;
      complex_array's own project-name hint is handled by its own
      check_complex_array.py, not here)                                        -> parse_bpmn()
  I   parse a connector node's request body (Flow read a native `inputs` dict;
      BPMN puts the whole request in `uipath:input` elements)                  -> body_object()
  T   the body must be the one `target="body"` JSON object the runtime
      consumes; several inputs fail (they don't merge at runtime)            -> bpmn_check.body_object()
  T   every users entry is a Slack user id (^[UW][A-Z0-9]+$), so a display
      name in the array fails                                                -> is_user_id()
  T   the count is of distinct ids, so one id repeated does not pass         -> len(set(users))
  T   shared by both tasks' --ids / --connection criteria                    -> require_ids(), require_connection()
  DROPPED  require_no_private_connector_values, require_sequence_integrity,
           require_di_for_visible_elements (not in Flow; `bpmn validate`
           criterion covers structure)

Exits non-zero with a `FAIL:` message on the first failure; prints `OK: ...`
on success.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    BodyShapeError,
    body_object,
    context_value,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
)

SLACK_KEY = "uipath-salesforce-slack"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"

CONNECTION_RESOURCE = "Connection"
CONNECTION_ID_ATTRIBUTE = "ConnectionId"

_USERS_KEY_RE = re.compile(r"users(\[.*\])?")
_SLACK_USER_ID_RE = re.compile(r"[UW][A-Z0-9]+")
_BINDING_REF_RE = re.compile(r"=bindings\.(\S+)")


def slack_tasks(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_typed_uipath_extension(task, "activity", ACTIVITY_TYPE)
        and context_value(task, "connectorKey") == SLACK_KEY
    ]


def is_users_key(key) -> bool:
    """True for the 'users' multiselect key in any of its encodings.

    Accepts the bare name and array-notation variants: 'users', 'users[*]',
    'users[]', 'users[0]' -- same tolerance Flow's grader had for how a .flow
    might spell an array-valued key.
    """
    return isinstance(key, str) and _USERS_KEY_RE.fullmatch(key) is not None


def parse_users(value):
    """Normalize a 'users' field value to a list of entries, else None.

    Accepts a native list, or a string holding an array literal such as a
    "=js:(['U1','U2','U3'])" expression -- identical tolerance to Flow's
    `check_multiselect_flow.parse_users`.
    """
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        match = re.search(r"\[.*\]", value, re.DOTALL)
        if not match:
            return None
        literal = match.group(0)
        try:
            parsed = ast.literal_eval(literal)
        except (ValueError, SyntaxError):
            parsed = None
        if isinstance(parsed, (list, tuple)):
            return list(parsed)
        entries = re.findall(r"""['"]([^'"]+)['"]""", literal)
        return entries or None
    return None


def is_user_id(value) -> bool:
    return isinstance(value, str) and _SLACK_USER_ID_RE.fullmatch(value) is not None


def find_users(obj):
    """Recursively find a 'users' key holding a parseable multiselect value."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if is_users_key(key):
                users = parse_users(value)
                if users is not None:
                    return users
            found = find_users(value)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_users(item)
            if found is not None:
                return found
    return None


def bound_connection(root: ET.Element, task: ET.Element) -> str:
    """The connection id ``task`` is bound to, else why it is not bound."""
    value = context_value(task, "connection")
    match = _BINDING_REF_RE.fullmatch(value)
    if not match:
        return f"connection {value!r} is not =bindings.<id>"

    binding_id = match.group(1)
    for binding in root.findall(".//uipath:binding", NS):
        if binding.attrib.get("id") != binding_id:
            continue
        if binding.attrib.get("resource") != CONNECTION_RESOURCE:
            continue
        if binding.attrib.get("propertyAttribute") != CONNECTION_ID_ATTRIBUTE:
            continue

        key = binding.attrib.get("resourceKey", "")
        default = binding.attrib.get("default", "")
        if key != default:
            return f"binding {binding_id} resourceKey {key!r} != default {default!r}"
        return key
    return f"no {CONNECTION_RESOURCE}/{CONNECTION_ID_ATTRIBUTE} binding {binding_id!r}"


def require_connection(name_hint: str | None, connection_id: str) -> None:
    path, root = parse_bpmn(name_hint)
    tasks = slack_tasks(root)
    if not tasks:
        fail(f"no Slack connector task in {path}")

    bound = {bound_connection(root, task) for task in tasks}
    if bound != {connection_id}:
        fail(f"Slack task bound to {sorted(bound)}, expected {connection_id}")
    print(f"OK: {path} Slack task bound to {connection_id}")


def require_ids(name_hint: str | None, ids: tuple[str, ...]) -> None:
    path, _root = parse_bpmn(name_hint)
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    missing = [uid for uid in ids if uid not in text]
    for uid in ids:
        print(f"{'OK     ' if uid not in missing else 'MISSING'} {uid}")
    if missing:
        fail(f"resolved Slack user id(s) not found in {path}: {missing}")
    print(f"OK: {path} references every resolved Slack user id")


def main() -> None:
    expected_count = (
        "populated"
        if len(sys.argv) > 1 and sys.argv[1] == "populated"
        else int(sys.argv[1]) if len(sys.argv) > 1 else 3
    )

    path, root = parse_bpmn()
    tasks = slack_tasks(root)
    if not tasks:
        fail(
            f"no bpmn:sendTask carrying {ACTIVITY_TYPE} for connector key "
            f"{SLACK_KEY!r} in {path}"
        )

    reasons = []
    for task in tasks:
        node_id = task.attrib.get("id", "<unknown>")
        try:
            users = find_users(body_object(task))
        except BodyShapeError as exc:
            reasons.append(f"node '{node_id}': {exc}")
            continue
        if users is None:
            reasons.append(f"node '{node_id}': no 'users' multiselect field found")
            continue
        not_ids = [user for user in users if not is_user_id(user)]
        if not_ids:
            reasons.append(f"node '{node_id}': users entries are not Slack user ids: {not_ids}")
            continue
        if expected_count == "populated":
            if any(str(user).strip() for user in users):
                print(f"OK: {path} — node '{node_id}' users={users}")
                sys.exit(0)
            reasons.append(f"node '{node_id}': users field is empty")
            continue
        if len(set(users)) == expected_count:
            print(f"OK: {path} — node '{node_id}' users={users}")
            sys.exit(0)
        reasons.append(
            f"node '{node_id}': users field has {len(set(users))} distinct entries, "
            f"expected {expected_count}: {users}"
        )

    fail("; ".join(reasons))


if __name__ == "__main__":
    main()
