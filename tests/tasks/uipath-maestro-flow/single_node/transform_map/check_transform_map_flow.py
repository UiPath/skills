#!/usr/bin/env python3
"""TransformMapDemo: structural check for the Transform Map node (smoke).

Generation-only — does not run `uip maestro flow debug`. Verifies:

  1. Exactly one node whose `type` is EXACTLY `core.action.transform.map`
     (strict `==`, NOT a substring) — a flow built with the generic
     `core.action.transform` or any other variant (`.filter`, `.group-by`)
     must fail, since the whole point of this smoke test is pinning the
     exact `map` variant.
  2. `inputs.collection` is a string that starts with `$vars.` and does NOT
     start with `=js:` — the transform `collection` is a plain variable path,
     never an `=js:` expression and never an inline array literal.
  3. `inputs.operations` is a non-empty list containing an operation with
     `type == "map"` whose `config.mappings` is a non-empty list of objects,
     each having a non-empty `field` and a non-empty `transformation`.
  4. `outputs.output.source == "=result.response"` and
     `outputs.error.source == "=Error"`.
  5. `typeVersion` is present and non-empty (the exact value is copied from
     `uip maestro flow registry get core.action.transform.map`, so we do NOT
     pin a specific version string here).
"""

import glob
import json
import sys
from typing import NoReturn

NODE_TYPE = "core.action.transform.map"
EXPECTED_OUTPUT_SOURCE = "=result.response"
EXPECTED_ERROR_SOURCE = "=Error"


def _fail(msg: str) -> NoReturn:
    sys.exit(f"FAIL: {msg}")


def _read_flow() -> dict:
    flows = glob.glob("**/TransformMapDemo*.flow", recursive=True)
    if not flows:
        _fail("no TransformMapDemo*.flow found under cwd")
    with open(flows[0]) as f:
        return json.load(f)


def _find_node(flow: dict) -> dict:
    # Strict equality on type — NOT a substring match. The generic
    # `core.action.transform` node and the `.filter` / `.group-by` variants
    # must NOT satisfy this smoke test.
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
        _fail("inputs.collection missing or empty — set it to a plain `$vars.<...>` path")
    c = collection.strip()
    if c.startswith("=js:"):
        _fail(
            f"inputs.collection={collection!r} starts with `=js:`. The transform "
            "`collection` is a plain variable path, never an `=js:` expression. "
            "Use e.g. `$vars.people.output`."
        )
    if not c.startswith("$vars."):
        _fail(
            f"inputs.collection={collection!r} must start with `$vars.` (a plain "
            "variable path). Inline array literals and other shapes are rejected."
        )


def _check_operations(inputs: dict) -> None:
    operations = inputs.get("operations")
    if not isinstance(operations, list) or not operations:
        _fail("inputs.operations must be a non-empty list with a `map` operation")
    map_ops = [op for op in operations if isinstance(op, dict) and op.get("type") == "map"]
    if not map_ops:
        _fail(
            "inputs.operations has no operation with type == 'map'. "
            f"operations seen: {[op.get('type') for op in operations if isinstance(op, dict)]}"
        )
    for op in map_ops:
        config = op.get("config")
        if not isinstance(config, dict):
            _fail("map operation has no `config` object")
        mappings = config.get("mappings")
        if not isinstance(mappings, list) or not mappings:
            _fail("map operation config.mappings must be a non-empty list")
        for i, m in enumerate(mappings):
            if not isinstance(m, dict):
                _fail(f"config.mappings[{i}] is {type(m).__name__}, expected an object")
            for key in ("field", "transformation"):
                val = m.get(key)
                if not isinstance(val, str) or not val.strip():
                    _fail(
                        f"config.mappings[{i}].{key} is missing or empty. "
                        "Each mapping needs a non-empty 'field' and 'transformation'."
                    )


def _check_output_sources(node: dict) -> None:
    outputs = node.get("outputs") or {}
    out_src = ((outputs.get("output")) or {}).get("source")
    if out_src != EXPECTED_OUTPUT_SOURCE:
        _fail(
            f"outputs.output.source={out_src!r}; must be {EXPECTED_OUTPUT_SOURCE!r}."
        )
    err_src = ((outputs.get("error")) or {}).get("source")
    if err_src != EXPECTED_ERROR_SOURCE:
        _fail(
            f"outputs.error.source={err_src!r}; must be {EXPECTED_ERROR_SOURCE!r}."
        )


def _check_type_version(node: dict) -> None:
    tv = node.get("typeVersion")
    if not isinstance(tv, str) or not tv.strip():
        _fail(
            "typeVersion missing or empty — copy it from "
            "`uip maestro flow registry get core.action.transform.map`."
        )


def main():
    flow = _read_flow()
    node = _find_node(flow)
    inputs = node.get("inputs") or {}

    _check_type_version(node)
    _check_collection(inputs)
    _check_operations(inputs)
    _check_output_sources(node)

    print(
        f"OK: exactly one {NODE_TYPE} node; collection is a plain `$vars.` path; "
        f"a `map` operation with non-empty mappings (field+transformation); "
        f"output source=`{EXPECTED_OUTPUT_SOURCE}`, error source=`{EXPECTED_ERROR_SOURCE}`; "
        f"typeVersion present"
    )


if __name__ == "__main__":
    main()
