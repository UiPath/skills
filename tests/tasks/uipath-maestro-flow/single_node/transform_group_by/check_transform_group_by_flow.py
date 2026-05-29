#!/usr/bin/env python3
"""TransformGroupByDemo: structural check for the Group By transform node.

Generation-only — does not run `uip maestro flow debug`. Verifies:

  1. Exactly one node with `type == "core.action.transform.group-by"` is present
     (exact match, not a substring — a flow built with a different transform
     variant such as `core.action.transform.map` or the generic
     `core.action.transform` must fail).
  2. `inputs.collection` is a plain `$vars.<path>` string — NOT wrapped in `=js:`
     and NOT an inline array literal (the transform runtime reads the path as-is).
  3. `inputs.operations` is a non-empty list containing an operation with
     `type == "groupBy"` whose:
       - `config.groupByField` is a non-empty string, and
       - `config.aggregations` is a non-empty list of objects, each with a
         non-empty `operation` and a non-empty `alias`.
  4. `outputs.output.source == "=result.response"` and
     `outputs.error.source == "=Error"`.
  5. `typeVersion` is present and non-empty (the value is copied from
     `uip maestro flow registry get core.action.transform.group-by`, so it is
     deliberately NOT pinned to a specific value here).
"""

import glob
import json
import sys
from typing import NoReturn

NODE_TYPE = "core.action.transform.group-by"
EXPECTED_OUTPUT_SOURCE = "=result.response"
EXPECTED_ERROR_SOURCE = "=Error"


def _fail(msg: str) -> NoReturn:
    sys.exit(f"FAIL: {msg}")


def _read_flow() -> dict:
    flows = glob.glob("**/TransformGroupByDemo*.flow", recursive=True)
    if not flows:
        _fail("no TransformGroupByDemo*.flow found under cwd")
    with open(flows[0]) as f:
        return json.load(f)


def _find_node(flow: dict) -> dict:
    matches = [n for n in flow.get("nodes", []) if n.get("type") == NODE_TYPE]
    if not matches:
        types = sorted({n.get("type") for n in flow.get("nodes", [])})
        _fail(f"no node with type == {NODE_TYPE!r}; types seen: {types}")
    if len(matches) > 1:
        _fail(f"expected exactly one {NODE_TYPE} node, found {len(matches)}")
    return matches[0]


def _check_collection(inputs: dict) -> None:
    collection = inputs.get("collection")
    if not isinstance(collection, str) or not collection.strip():
        _fail("inputs.collection missing or empty — set it to a plain `$vars.<path>` string")
    value = collection.strip()
    if value.startswith("=js:"):
        _fail(
            f"inputs.collection={collection!r} is wrapped in `=js:`. Transform `collection` is a "
            "path field, not a `=js:` expression — use a plain path like `$vars.employees.output.items`."
        )
    if value.startswith("[") or value.startswith("{"):
        _fail(
            f"inputs.collection={collection!r} looks like an inline array/object literal. "
            "Store the static data in a variable defaultValue or upstream node and point "
            "`collection` at that path (e.g. `$vars.employees`)."
        )
    if not value.startswith("$vars."):
        _fail(
            f"inputs.collection={collection!r} is not a plain `$vars.<path>` string. "
            "Expected something like `$vars.employees.output.items`."
        )


def _check_operations(inputs: dict) -> None:
    operations = inputs.get("operations")
    if not isinstance(operations, list) or not operations:
        _fail("inputs.operations must be a non-empty list")

    group_by_ops = [
        op for op in operations if isinstance(op, dict) and op.get("type") == "groupBy"
    ]
    if not group_by_ops:
        types = [op.get("type") if isinstance(op, dict) else type(op).__name__ for op in operations]
        _fail(f"inputs.operations has no operation with type == 'groupBy'; op types seen: {types}")

    op = group_by_ops[0]
    config = op.get("config")
    if not isinstance(config, dict):
        _fail("the groupBy operation has no `config` object")

    group_by_field = config.get("groupByField")
    if not isinstance(group_by_field, str) or not group_by_field.strip():
        _fail("groupBy config.groupByField must be a non-empty string")

    aggregations = config.get("aggregations")
    if not isinstance(aggregations, list) or not aggregations:
        _fail("groupBy config.aggregations must be a non-empty list")
    for i, agg in enumerate(aggregations):
        if not isinstance(agg, dict):
            _fail(f"groupBy config.aggregations[{i}] is {type(agg).__name__}, expected an object")
        for key in ("operation", "alias"):
            val = agg.get(key)
            if not isinstance(val, str) or not val.strip():
                _fail(
                    f"groupBy config.aggregations[{i}].{key} is missing or empty. "
                    "Each aggregation needs a non-empty 'operation' and 'alias'."
                )


def _check_ports(node: dict) -> None:
    outputs = node.get("outputs") or {}
    out_src = ((outputs.get("output") or {}).get("source"))
    if out_src != EXPECTED_OUTPUT_SOURCE:
        _fail(
            f"outputs.output.source={out_src!r}; must be {EXPECTED_OUTPUT_SOURCE!r}."
        )
    err_src = ((outputs.get("error") or {}).get("source"))
    if err_src != EXPECTED_ERROR_SOURCE:
        _fail(
            f"outputs.error.source={err_src!r}; must be {EXPECTED_ERROR_SOURCE!r}."
        )


def _check_type_version(node: dict) -> None:
    tv = node.get("typeVersion")
    if not isinstance(tv, str) or not tv.strip():
        _fail(
            "typeVersion is missing or empty — copy it from "
            "`uip maestro flow registry get core.action.transform.group-by --output json`."
        )


def main():
    flow = _read_flow()
    node = _find_node(flow)
    inputs = node.get("inputs") or {}

    _check_type_version(node)
    _check_collection(inputs)
    _check_operations(inputs)
    _check_ports(node)

    print(
        f"OK: exactly one {NODE_TYPE} node present; typeVersion set; "
        f"collection is a plain $vars path; groupBy op has a groupByField and "
        f"non-empty aggregations; output source=`=result.response`, error source=`=Error`"
    )


if __name__ == "__main__":
    main()
