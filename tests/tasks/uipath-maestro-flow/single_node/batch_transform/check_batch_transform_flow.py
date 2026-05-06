#!/usr/bin/env python3
"""BatchTransformDemo: structural check for the Batch Transform pattern node.

Generation-only — does not run `uip maestro flow debug`. Verifies:

  1. Exactly one `uipath.pattern.batch-transform` node is present.
  2. `inputs.prompt` is non-empty.
  3. `inputs.outputColumns` is an array of objects with `name` + `description`
     keys (not flattened to a `{name: description}` map and not a string array).
  4. `inputs.attachment` is wired (non-empty), and is **not** a literal empty
     string — typically a `$vars.*` reference.
"""

import glob
import json
import sys

NODE_TYPE = "uipath.pattern.batch-transform"


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _read_flow() -> dict:
    flows = glob.glob("**/BatchTransformDemo*.flow", recursive=True)
    if not flows:
        _fail("no BatchTransformDemo*.flow found under cwd")
    with open(flows[0]) as f:
        return json.load(f)


def _find_node(flow: dict) -> dict:
    matches = [n for n in flow.get("nodes", []) if n.get("type") == NODE_TYPE]
    if not matches:
        types = sorted({n.get("type") for n in flow.get("nodes", [])})
        _fail(f"no node with type {NODE_TYPE!r}; types seen: {types}")
    if len(matches) > 1:
        _fail(f"expected exactly one {NODE_TYPE} node, found {len(matches)}")
    return matches[0]


def _check_outputColumns(value) -> None:
    if not isinstance(value, list):
        _fail(
            f"inputs.outputColumns must be a list, got {type(value).__name__}. "
            "The batch-transform plugin docs require the array-of-objects shape."
        )
    if not value:
        _fail("inputs.outputColumns is empty — at least one column is required")
    for i, col in enumerate(value):
        if not isinstance(col, dict):
            _fail(
                f"inputs.outputColumns[{i}] is {type(col).__name__}, expected dict "
                "with 'name' and 'description' keys"
            )
        for key in ("name", "description"):
            if key not in col or not isinstance(col[key], str) or not col[key].strip():
                _fail(
                    f"inputs.outputColumns[{i}].{key} is missing or empty. "
                    "Each entry must have non-empty 'name' and 'description'."
                )


def main():
    flow = _read_flow()
    node = _find_node(flow)
    inputs = node.get("inputs") or {}

    prompt = inputs.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        _fail("inputs.prompt missing or empty")

    attachment = inputs.get("attachment")
    if not isinstance(attachment, str) or not attachment.strip():
        _fail("inputs.attachment missing or empty — wire it to the flow input variable")

    _check_outputColumns(inputs.get("outputColumns"))

    print(
        f"OK: {NODE_TYPE} node present; prompt set; attachment wired; "
        f"outputColumns has {len(inputs['outputColumns'])} {{name,description}} entries"
    )


if __name__ == "__main__":
    main()
