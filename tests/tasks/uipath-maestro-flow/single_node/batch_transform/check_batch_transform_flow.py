#!/usr/bin/env python3
"""BatchTransformDemo: structural check for the Batch Transform pattern node.

Generation-only — does not run `uip maestro flow debug`. Verifies:

  1. Exactly one `uipath.pattern.batch-transform` node is present.
  2. `inputs.prompt` is non-empty.
  3. `inputs.outputColumns` is an array of objects with `name` + `description`
     keys (not flattened to a `{name: description}` map and not a string array).
  4. `inputs.attachment` is wired to the WHOLE flow input object via
     `=js:$vars.<name>` — not `.Id`, `.FullName`, or any subfield. The runtime
     wants the full Flow Attachment `{ FullName, Id, Metadata, MimeType }`.
  5. The referenced flow input variable is declared `type: "object"`.
  6. The flow declares an `out` variable named `result`, and at least one End
     node maps it via `outputs.result.source` using a `=js:$vars.<bt>.output`
     reference (not a bare `$vars.…` literal — rule 12 requires the `=js:`
     prefix).
"""

import glob
import json
import re
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


_ATTACHMENT_REF = re.compile(r"^=js:\s*\$vars\.([A-Za-z_][A-Za-z0-9_]*)\s*$")


def _check_attachment_is_whole_object(flow: dict, attachment) -> None:
    if not isinstance(attachment, str) or not attachment.strip():
        _fail("inputs.attachment missing or empty — wire it to the flow input variable")
    m = _ATTACHMENT_REF.match(attachment.strip())
    if not m:
        _fail(
            f"inputs.attachment={attachment!r} must be `=js:$vars.<name>` referencing the WHOLE "
            "Flow Attachment object — not a bare id, GUID, URL, path, or subfield like `.Id`."
        )
    var_name = m.group(1)
    globals_ = (flow.get("variables") or {}).get("globals") or []
    var = next((v for v in globals_ if v.get("id") == var_name), None)
    if var is None:
        _fail(
            f"inputs.attachment references `$vars.{var_name}` but no flow `globals` variable "
            f"with id={var_name!r} exists. Declare it as an `in` variable of type `object`."
        )
    if var.get("type") != "object":
        _fail(
            f"flow input variable `{var_name}` has type={var.get('type')!r}; must be `object` "
            "to hold the full Flow Attachment `{ FullName, Id, Metadata, MimeType }`."
        )


_OUTPUT_MAPPING_REF = re.compile(r"^=js:\s*\$vars\.([A-Za-z_][A-Za-z0-9_]*)\.output\b")


def _check_result_output_mapping(flow: dict, bt_node_id: str) -> None:
    """The flow surfaces the BT result as an `out` variable `result`. Verify
    the variable exists and at least one End node maps it correctly.

    Each End node may carry an `outputs.<varId>.source` for every `out`
    variable; the source MUST use `=js:$vars.<bt>.output` (rule 12).
    """
    globals_ = (flow.get("variables") or {}).get("globals") or []
    result_var = next(
        (
            v
            for v in globals_
            if v.get("id") == "result" and v.get("direction") == "out"
        ),
        None,
    )
    if result_var is None:
        _fail(
            "flow has no `out` variable with id='result'. The task prompt asks for the "
            "Batch Transform result file handle to be surfaced as a flow output named `result`."
        )

    end_nodes = [
        n for n in flow.get("nodes", []) if n.get("type") == "core.control.end"
    ]
    if not end_nodes:
        _fail("flow has no End node — required to terminate the path and map outputs")

    mapped_on = []
    for end in end_nodes:
        src = ((end.get("outputs") or {}).get("result") or {}).get("source")
        if not isinstance(src, str) or not src.strip():
            continue
        m = _OUTPUT_MAPPING_REF.match(src.strip())
        if m and m.group(1) == bt_node_id:
            mapped_on.append(end.get("id"))
    if not mapped_on:
        _fail(
            "no End node maps `outputs.result.source` to `=js:$vars."
            f"{bt_node_id}.output` (or similar). Without an `=js:` mapping per rule 12, "
            "the flow output is the literal string instead of the real BT result handle."
        )


def main():
    flow = _read_flow()
    node = _find_node(flow)
    inputs = node.get("inputs") or {}

    prompt = inputs.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        _fail("inputs.prompt missing or empty")

    _check_attachment_is_whole_object(flow, inputs.get("attachment"))
    _check_outputColumns(inputs.get("outputColumns"))
    _check_result_output_mapping(flow, node["id"])

    print(
        f"OK: {NODE_TYPE} node present; prompt set; attachment is whole-object ref to a "
        f"`type: object` flow input; outputColumns has {len(inputs['outputColumns'])} "
        "{name,description} entries; End node maps `result` via `=js:` reference"
    )


if __name__ == "__main__":
    main()
