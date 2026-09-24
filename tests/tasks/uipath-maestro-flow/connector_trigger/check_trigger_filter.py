#!/usr/bin/env python3
"""Connector trigger with filter: verify the emitted `.flow` carries the Outlook
email-received trigger filter in BOTH places the platform reads it.

One logical filter is persisted twice on the trigger node, and each copy has
its own reader:

  * `inputs.detail.configuration` (`=jsonString:` envelope) →
    `essentialConfiguration.filter` — the structured tree Studio Web renders.
    Missing tree ⇒ the designer silently drops the filter on first open.
  * `inputs.detail.filterExpression` — the JMESPath the runtime subscribes
    with. Missing clause ⇒ the trigger fires on every email.

Both authoring loops emit both copies (the CLI's `node configure` derives the
expression from the tree; the SDK's `onEvent({ filters })` lowers to both), so
this grades the outcome rather than either loop's input format.

Modes:
    check_trigger_filter.py node        trigger node present
    check_trigger_filter.py tree        tree: AND of subject Contains "good day"
                                        + from.emailAddress.address Equals abc@xyz.com
    check_trigger_filter.py expression  filterExpression carries both clauses

Exit 0 on pass, 1 on failure (message printed).
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _shared.flow_check import find_flow_files  # noqa: E402

NODE_TYPE = "uipath.connector.trigger.uipath-microsoft-outlook365.email-received"
JSONSTRING_PREFIX = "=jsonString:"
SUBJECT = ("subject", "Contains", "good day")
SENDER = ("from.emailAddress.address", "Equals", "abc@xyz.com")
EXPRESSION_CLAUSES = (
    ("subject contains 'good day'", re.compile(r"contains\(\s*subject\s*,\s*'good day'\s*\)", re.I)),
    (
        "from.emailAddress.address == 'abc@xyz.com'",
        re.compile(r"from\.emailAddress\.address\s*==\s*'abc@xyz\.com'", re.I),
    ),
)


def _fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def _trigger_node() -> tuple[str, dict]:
    seen: list[str] = []
    for path in find_flow_files(flow_glob="GoodDayMailTrigger.flow") or []:
        with open(path, encoding="utf-8") as handle:
            flow = json.load(handle)
        for node in flow.get("nodes", []):
            seen.append(str(node.get("type")))
            if node.get("type") == NODE_TYPE:
                return path, node
    _fail(f"no {NODE_TYPE} node in GoodDayMailTrigger.flow (node types: {sorted(set(seen))})")
    raise AssertionError("unreachable")


def _detail(path: str, node: dict) -> dict:
    detail = (node.get("inputs") or {}).get("detail")
    if not isinstance(detail, dict):
        _fail(f"trigger node '{node.get('id')}' in {path} has no inputs.detail — it was never configured")
    return detail


def _tree(path: str, detail: dict) -> dict:
    configuration = detail.get("configuration")
    if not isinstance(configuration, str) or not configuration.startswith(JSONSTRING_PREFIX):
        _fail(f"inputs.detail.configuration is missing or not a '{JSONSTRING_PREFIX}' envelope in {path}")
    try:
        blob = json.loads(configuration[len(JSONSTRING_PREFIX):])
    except json.JSONDecodeError as error:
        _fail(f"configuration blob is not valid JSON in {path}: {error}")
    tree = (blob.get("essentialConfiguration") or {}).get("filter")
    if not isinstance(tree, dict) or not isinstance(tree.get("filters"), list):
        _fail(f"essentialConfiguration.filter is not a filter tree in {path} (found {tree!r})")
    return tree


def _leaves(group: dict):
    for item in group.get("filters") or []:
        if isinstance(item, dict):
            yield group, item
    for sub in group.get("groups") or []:
        if isinstance(sub, dict):
            yield from _leaves(sub)


def _leaf_value(leaf: dict) -> object:
    value = leaf.get("value")
    return value.get("value") if isinstance(value, dict) else value


def check_node() -> None:
    path, node = _trigger_node()
    print(f"PASS: {path} has trigger node '{node.get('id')}' ({NODE_TYPE})")


def check_tree() -> None:
    path, node = _trigger_node()
    tree = _tree(path, _detail(path, node))
    leaves = list(_leaves(tree))
    for field, operator, expected in (SUBJECT, SENDER):
        match = [
            (group, leaf)
            for group, leaf in leaves
            if (leaf.get("id") or leaf.get("fieldName") or leaf.get("field")) == field
            and leaf.get("operator") == operator
            and str(_leaf_value(leaf)).casefold() == expected.casefold()
        ]
        if not match:
            found = [(l.get("id"), l.get("operator"), _leaf_value(l)) for _, l in leaves]
            _fail(f"filter tree in {path} has no `{field}` {operator} {expected!r} leaf (leaves: {found})")
        if any(group.get("groupOperator") != 0 for group, _ in match):
            _fail(f"`{field}` leaf in {path} sits in a non-AND group (groupOperator must be 0)")
    print(f"PASS: {path} filter tree ANDs subject Contains 'good day' and sender Equals abc@xyz.com")


def check_expression() -> None:
    path, node = _trigger_node()
    expression = _detail(path, node).get("filterExpression")
    if not isinstance(expression, str) or not expression.strip():
        _fail(f"inputs.detail.filterExpression is empty in {path} — the runtime would not filter")
    missing = [label for label, pattern in EXPRESSION_CLAUSES if not pattern.search(expression)]
    if missing:
        _fail(f"filterExpression {expression!r} in {path} lacks: {missing}")
    if "&&" not in expression:
        _fail(f"filterExpression {expression!r} in {path} does not AND its clauses")
    print(f"PASS: {path} filterExpression carries both clauses: {expression}")


def main() -> None:
    modes = {"node": check_node, "tree": check_tree, "expression": check_expression}
    if len(sys.argv) != 2 or sys.argv[1] not in modes:
        _fail(f"usage: check_trigger_filter.py {{{'|'.join(modes)}}}")
    modes[sys.argv[1]]()


if __name__ == "__main__":
    main()
