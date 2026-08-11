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

    # Studio Web's persisted group shape: numeric groupOperator (0 = And,
    # 1 = Or) + a non-empty `filters` array.
    def _is_filter_group(n):
        return (
            isinstance(n, dict)
            and isinstance(n.get("groupOperator"), (int, float))
            and not isinstance(n.get("groupOperator"), bool)
            and isinstance(n.get("filters"), list)
            and bool(n.get("filters"))
        )

    # trigger_detail.json IS the `--detail` object (the exact JSON passed to
    # `node configure --detail`), so `filter` must be a TOP-LEVEL key — that is
    # where the CLI reads it. A filter wrapped under `detail` / `inputs` is not
    # the --detail object and the CLI would silently ignore it, so it fails.
    filter_tree = detail.get("filter")
    if not _is_filter_group(filter_tree):
        top = sorted(detail.keys()) if isinstance(detail, dict) else type(detail).__name__
        sys.exit(
            "FAIL: expected a `filter` tree as a TOP-LEVEL key of the --detail "
            "object (numeric groupOperator + non-empty `filters`); do not wrap it "
            f"under `detail`/`inputs`. Top-level keys found: {top}"
        )

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
