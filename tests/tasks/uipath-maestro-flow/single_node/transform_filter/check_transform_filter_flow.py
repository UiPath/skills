#!/usr/bin/env python3
"""TransformFilterDemo: structural check for the dedicated Transform Filter node.

Generation-only — does not run `uip maestro flow debug`. Verifies:

  1. Exactly one node with `type` EXACTLY `core.action.transform.filter`.
     The match is strict (`==`), so a flow built with `.map`, `.group-by`, or
     the generic `core.action.transform` chain FAILS — this test pins the
     filter-only variant on purpose.
  2. `inputs.collection` is a PLAIN `$vars` path (e.g. `$vars.items.output`).
     A `=js:`-wrapped value, an inline array literal, or a non-`$vars` string
     is rejected (the transform runtime reads `collection` as a literal lookup
     path, not an expression).
  3. `inputs.operations` is a non-empty list containing an op with
     `type == "filter"` whose `config.filters` is a non-empty list of objects,
     each with a non-empty `field`, a `condition` in the allowed set, and a
     LITERAL scalar `value` (a string starting with `$vars`, `=js:`, or `{`
     is rejected — Transform filter `value` is literal-only).
  4. `outputs.output.source == "=result.response"` and
     `outputs.error.source == "=Error"`.
  5. `typeVersion` is present and non-empty (the exact value is copied from
     `uip maestro flow registry get core.action.transform.filter`, so we do
     NOT pin a specific version).
"""

import glob
import json
import sys
from typing import NoReturn

NODE_TYPE = "core.action.transform.filter"
EXPECTED_OUTPUT_SOURCE = "=result.response"
EXPECTED_ERROR_SOURCE = "=Error"

ALLOWED_CONDITIONS = {
    "equals",
    "not_equals",
    "greater_than",
    "less_than",
    "greater_equal",
    "less_equal",
    "contains",
    "starts_with",
    "ends_with",
    "is_null",
    "is_not_null",
}

# A literal filter `value` must not be an unresolved expression/template.
_EXPR_PREFIXES = ("$vars", "=js:", "{")


def _fail(msg: str) -> NoReturn:
    sys.exit(f"FAIL: {msg}")


def _read_flow() -> dict:
    flows = glob.glob("**/TransformFilterDemo*.flow", recursive=True)
    if not flows:
        _fail("no TransformFilterDemo*.flow found under cwd")
    with open(flows[0]) as f:
        return json.load(f)


def _find_node(flow: dict) -> dict:
    matches = [n for n in flow.get("nodes", []) if n.get("type") == NODE_TYPE]
    if not matches:
        types = sorted({n.get("type") for n in flow.get("nodes", [])})
        _fail(
            f"no node with type EXACTLY {NODE_TYPE!r}; types seen: {types}. "
            "This test pins the filter-only variant — `.map`, `.group-by`, and "
            "the generic `core.action.transform` chain do not satisfy it."
        )
    if len(matches) > 1:
        _fail(f"expected exactly one {NODE_TYPE} node, found {len(matches)}")
    return matches[0]


def _check_collection(inputs: dict) -> None:
    collection = inputs.get("collection")
    if not isinstance(collection, str) or not collection.strip():
        _fail("inputs.collection missing or empty — set it to a plain `$vars` path")
    coll = collection.strip()
    if coll.startswith("=js:"):
        _fail(
            f"inputs.collection={collection!r} is wrapped in `=js:`. Transform "
            "`collection` is a literal lookup path, not an expression — use a "
            "plain `$vars` path such as `$vars.items.output`."
        )
    if coll.startswith("[") or coll.startswith("{"):
        _fail(
            f"inputs.collection={collection!r} looks like an inline literal. "
            "Store the static array in a variable default or upstream node and "
            "point `collection` at a plain `$vars` path."
        )
    if not coll.startswith("$vars."):
        _fail(
            f"inputs.collection={collection!r} is not a plain `$vars` path. "
            "Expected something like `$vars.items.output`."
        )


def _check_filter_value_literal(value, fidx: int) -> None:
    if isinstance(value, str):
        v = value.strip()
        for prefix in _EXPR_PREFIXES:
            if v.startswith(prefix):
                _fail(
                    f"config.filters[{fidx}].value={value!r} is an unresolved "
                    f"expression/template (starts with {prefix!r}). Transform "
                    "filter `value` is literal-only — use a literal scalar like "
                    "100, \"active\", or true."
                )
    elif isinstance(value, (dict, list)):
        _fail(
            f"config.filters[{fidx}].value is a {type(value).__name__}; "
            "filter `value` must be a literal scalar (number, string, or bool)."
        )


def _check_operations(inputs: dict) -> None:
    operations = inputs.get("operations")
    if not isinstance(operations, list) or not operations:
        _fail("inputs.operations must be a non-empty list with a filter op")

    filter_ops = [
        op for op in operations if isinstance(op, dict) and op.get("type") == "filter"
    ]
    if not filter_ops:
        op_types = [op.get("type") if isinstance(op, dict) else op for op in operations]
        _fail(
            f"inputs.operations has no op with type=='filter'; op types: {op_types}"
        )

    found_any_filter = False
    for op in filter_ops:
        config = op.get("config")
        if not isinstance(config, dict):
            _fail("filter operation has no `config` object")
        filters = config.get("filters")
        if not isinstance(filters, list) or not filters:
            _fail("config.filters must be a non-empty list of filter objects")
        for fidx, flt in enumerate(filters):
            if not isinstance(flt, dict):
                _fail(f"config.filters[{fidx}] is {type(flt).__name__}, expected object")
            field = flt.get("field")
            if not isinstance(field, str) or not field.strip():
                _fail(f"config.filters[{fidx}].field is missing or empty")
            condition = flt.get("condition")
            if condition not in ALLOWED_CONDITIONS:
                _fail(
                    f"config.filters[{fidx}].condition={condition!r} not in allowed "
                    f"set {sorted(ALLOWED_CONDITIONS)}"
                )
            # is_null / is_not_null take no value; everything else needs a literal.
            if condition in ("is_null", "is_not_null"):
                found_any_filter = True
                continue
            if "value" not in flt:
                _fail(
                    f"config.filters[{fidx}] (condition={condition!r}) has no `value`"
                )
            _check_filter_value_literal(flt.get("value"), fidx)
            found_any_filter = True

    if not found_any_filter:
        _fail("no usable filter condition found in config.filters")


def _check_output_sources(node: dict) -> None:
    outputs = node.get("outputs") or {}
    out_src = ((outputs.get("output")) or {}).get("source")
    if out_src != EXPECTED_OUTPUT_SOURCE:
        _fail(
            f"outputs.output.source={out_src!r}; must be {EXPECTED_OUTPUT_SOURCE!r}"
        )
    err_src = ((outputs.get("error")) or {}).get("source")
    if err_src != EXPECTED_ERROR_SOURCE:
        _fail(
            f"outputs.error.source={err_src!r}; must be {EXPECTED_ERROR_SOURCE!r}"
        )


def _check_type_version(node: dict) -> None:
    tv = node.get("typeVersion")
    if not isinstance(tv, str) or not tv.strip():
        _fail(
            "typeVersion is missing or empty — copy it from "
            "`uip maestro flow registry get core.action.transform.filter`."
        )


def main():
    flow = _read_flow()
    node = _find_node(flow)
    inputs = node.get("inputs") or {}

    _check_collection(inputs)
    _check_operations(inputs)
    _check_output_sources(node)
    _check_type_version(node)

    print(
        f"OK: exactly one {NODE_TYPE} node; collection is a plain `$vars` path; "
        f"operations has a filter op with a non-empty config.filters of literal "
        f"conditions; output source=`=result.response`, error source=`=Error`; "
        f"typeVersion={node.get('typeVersion')!r}"
    )


if __name__ == "__main__":
    main()
