#!/usr/bin/env python3
"""Connector trigger with filter: verify the emitted filter tree references the
expected field and uses PascalCase operator names (Studio Web contract)."""

import json
import sys


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
    try:
        with open("trigger_detail.json") as f:
            detail = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"FAIL: cannot load trigger_detail.json: {e}")

    filter_tree = detail.get("filter")
    if not isinstance(filter_tree, dict):
        sys.exit("FAIL: trigger_detail.json has no `filter` object")

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

    print("PASS: filter tree references `subject` and uses PascalCase `Contains`")


if __name__ == "__main__":
    main()
