#!/usr/bin/env python3
"""Connector trigger with filter: verify the emitted `trigger_detail.json`
(found anywhere under the solution) carries a structured filter tree that
references the expected field and uses PascalCase operator names (Studio Web
contract). Consolidates the JSON-validity and filter-tree-shape checks the YAML
previously inlined as root-only `file_exists` / `json_check` criteria, resolving
the file recursively so a nested emit (inside the flow project dir) still grades."""

import glob
import json
import os
import sys

DETAIL_GLOB = "**/trigger_detail.json"


def _walk(node):
    """Yield every dict in a nested filter tree (groups + leaves)."""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def main():
    path = "trigger_detail.json"
    if not os.path.exists(path):
        matches = glob.glob(DETAIL_GLOB, recursive=True)
        if not matches:
            sys.exit("FAIL: trigger_detail.json not found")
        path = matches[0]

    try:
        with open(path) as f:
            detail = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"FAIL: cannot load {path}: {e}")

    # MST-8802 regression guard: filterExpression was removed as an input field;
    # the agent must NOT emit it at the top level.
    if detail.get("filterExpression") is not None:
        sys.exit("FAIL: trigger_detail.json must not carry top-level `filterExpression`")

    filter_tree = detail.get("filter")
    if not isinstance(filter_tree, dict):
        sys.exit("FAIL: trigger_detail.json has no `filter` object")

    # Studio Web's persisted shape: numeric groupOperator (0 = And, 1 = Or) and a
    # non-empty `filters` array.
    if not isinstance(filter_tree.get("groupOperator"), (int, float)) or isinstance(
        filter_tree.get("groupOperator"), bool
    ):
        sys.exit("FAIL: filter.groupOperator must be a number (0 = And, 1 = Or)")
    filters = filter_tree.get("filters")
    if not isinstance(filters, list) or not filters:
        sys.exit("FAIL: filter.filters must be a non-empty array")

    nodes = list(_walk(filter_tree))

    # 1. Filter tree must reference the `subject` field on at least one leaf.
    # A leaf filter has an `operator` string + `value`; a group has
    # `groupOperator` + `filters`. The field identifier lives under `id`,
    # `fieldName`, `field`, or `name` depending on the emitter.
    leaves = [n for n in nodes if isinstance(n.get("operator"), str)]

    def _field(n):
        return n.get("fieldName") or n.get("field") or n.get("id") or n.get("name")

    fields = [_field(n) for n in leaves]
    if not any(isinstance(f, str) and "subject" in f.lower() for f in fields):
        sys.exit(
            f"FAIL: filter tree does not reference the `subject` field "
            f"(found fields: {[f for f in fields if f]})"
        )

    # 2. At least one leaf must use the PascalCase `Contains` operator.
    operators = {n.get("operator") for n in leaves if isinstance(n.get("operator"), str)}
    if "Contains" not in operators:
        sys.exit(
            f"FAIL: expected PascalCase `Contains` operator in filter tree, "
            f"found operators: {sorted(o for o in operators if o)}"
        )

    print(f"PASS: {path} filter tree references `subject` and uses PascalCase `Contains`")


if __name__ == "__main__":
    main()
