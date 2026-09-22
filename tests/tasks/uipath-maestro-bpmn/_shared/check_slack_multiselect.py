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
  F check_multiselect_flow.py:86-91   "slack" in node.type.lower()              -> slack_tasks(): sendTask carrying Intsvc.ActivityExecution with connectorKey == uipath-salesforce-slack
  F check_multiselect_flow.py:93-104  find_users(node.inputs), count/populated  -> find_users(body_object(task)), same count/populated check
  F check_multiselect_flow.py:26-48   parse_users(): native list, or a string
                                       wrapping an array literal (JSON array or
                                       a `=js:(['U1','U2'])`-style expression)  -> parse_users(): identical regex + ast.literal_eval tolerance
  F check_multiselect_flow.py:51-57   is_users_key(): 'users' with an optional
                                       array-notation suffix                    -> is_users_key(): identical regex
  F check_multiselect_flow.py:60-76   find_users(): recursive dict/list search  -> find_users(): identical recursive search over the merged body object
  I   locate/parse .bpmn, no name hint (this script is shared by both tasks;
      complex_array's own project-name hint is handled by its own
      check_complex_array.py, not here)                                        -> parse_bpmn()
  I   parse a connector node's request body (Flow read a native `inputs` dict;
      BPMN puts the whole request in `uipath:input` elements)                  -> body_object()
  T   the registry's two observed body forms both count: one whole-body
      `target="body"` JSON blob (name="body"), or one typed `target="body"`
      input per field (name=<field>) -- registry-workflow.md documents the
      first as canonical; the second is what `bpmn_check.body_object()` on
      main (not yet on this branch) tolerates, so it is reimplemented locally
      here per the porting brief                                               -> body_object()
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    context_value,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
)

SLACK_KEY = "uipath-salesforce-slack"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"

_USERS_KEY_RE = re.compile(r"users(\[.*\])?")


def node_inputs(task: ET.Element) -> list[ET.Element]:
    return task.findall(".//uipath:input", NS)


def slack_tasks(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_typed_uipath_extension(task, "activity", ACTIVITY_TYPE)
        and context_value(task, "connectorKey") == SLACK_KEY
    ]


def body_object(task: ET.Element) -> dict:
    """Merge every `target="body"` input on `task` into one dict, accepting
    either registry-observed form: a single `name="body"` input holding the
    whole request as a JSON object, or one typed input per field (its own
    `name`, value/text is that field's value)."""
    obj: dict = {}
    for inp in node_inputs(task):
        if inp.attrib.get("target") != "body":
            continue
        name = inp.attrib.get("name")
        raw = inp.attrib.get("value")
        if raw is None:
            raw = inp.text
        raw = (raw or "").strip()
        if not raw:
            continue
        if name == "body":
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                obj.update(parsed)
            continue
        if not name:
            continue
        try:
            obj[name] = json.loads(raw)
        except json.JSONDecodeError:
            obj[name] = raw
    return obj


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
        users = find_users(body_object(task))
        if users is None:
            reasons.append(f"node '{node_id}': no 'users' multiselect field found")
            continue
        if expected_count == "populated":
            if users:
                print(f"OK: {path} — node '{node_id}' users={users}")
                sys.exit(0)
            reasons.append(f"node '{node_id}': users field is empty")
            continue
        if len(users) == expected_count:
            print(f"OK: {path} — node '{node_id}' users={users}")
            sys.exit(0)
        reasons.append(
            f"node '{node_id}': users field has {len(users)} entries, "
            f"expected {expected_count}: {users}"
        )

    fail("; ".join(reasons))


if __name__ == "__main__":
    main()
