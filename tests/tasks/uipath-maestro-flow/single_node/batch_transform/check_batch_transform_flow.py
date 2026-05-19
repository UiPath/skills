#!/usr/bin/env python3
"""BatchTransformDemo: structural check for the Batch Transform pattern node.

Generation-only — does not run `uip maestro flow debug`. Verifies:

  1. Exactly one `uipath.pattern.batch-transform` node is present.
  2. The instance has no `model` block (BPMN type/serviceType lives in
     `definitions[].model` only — rule 16).
  3. `typeVersion` is exactly `"1.0"` (matches `definitions[<bt>].version`).
  4. `inputs.prompt` is non-empty.
  5. `inputs.outputColumns` is an array of objects with `name` + `description`
     keys (not flattened to a `{name: description}` map and not a string array).
  6. `inputs.attachment` matches the canonical canvas-produced wiring:
     `=js:$vars.<triggerId>.output.<fileVarId>` — referencing a flow `in`
     variable of `type: "file"` bound to the trigger via `triggerNodeId`.
     Bare `=js:$vars.<name>` (no trigger output) is rejected.
  7. The instance `outputs.output.source` is the literal `=response`.
  8. The flow declares an `out` variable named `result`, and at least one End
     node maps it via `outputs.result.source` using a `=js:$vars.<bt>.output`
     reference.
"""

import glob
import json
import re
import sys
from typing import NoReturn

NODE_TYPE = "uipath.pattern.batch-transform"
EXPECTED_TYPE_VERSION = "1.0"
EXPECTED_OUTPUT_SOURCE = "=response"

# Canonical canvas wiring: =js:$vars.<triggerId>.output.<fileVarId>
# (a trigger-bound `in` file variable surfaces under the trigger's output)
_ATTACHMENT_REF = re.compile(
    r"^=js:\s*\$vars\.([A-Za-z_][A-Za-z0-9_]*)\.output\.([A-Za-z_][A-Za-z0-9_]*)\s*$"
)

# Output mapping: =js:$vars.<bt>.output  (or any deeper subfield path)
_OUTPUT_MAPPING_REF = re.compile(r"^=js:\s*\$vars\.([A-Za-z_][A-Za-z0-9_]*)\.output\b")


def _fail(msg: str) -> NoReturn:
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


def _check_attachment_canonical(flow: dict, attachment) -> None:
    if not isinstance(attachment, str) or not attachment.strip():
        _fail("inputs.attachment missing or empty — wire it to the trigger output binding")
    m = _ATTACHMENT_REF.match(attachment.strip())
    if not m:
        _fail(
            f"inputs.attachment={attachment!r} is not the canonical canvas-produced shape. "
            "Expected `=js:$vars.<triggerId>.output.<fileVarId>` — the canvas wires file-typed "
            "flow `in` variables through the trigger's output. Do NOT use the bare "
            "`=js:$vars.<name>` shape, a `.Id`/`.FullName` subfield, or a literal id/URL/path."
        )
    trigger_id, file_var_id = m.group(1), m.group(2)

    # Trigger node must exist and be a trigger
    trigger_node = next(
        (n for n in flow.get("nodes", []) if n.get("id") == trigger_id),
        None,
    )
    if trigger_node is None:
        _fail(
            f"inputs.attachment references `$vars.{trigger_id}.output...` but no node with "
            f"id={trigger_id!r} exists in the flow."
        )
    if not isinstance(trigger_node.get("type"), str) or "trigger" not in trigger_node["type"]:
        _fail(
            f"node id={trigger_id!r} has type={trigger_node.get('type')!r}; expected a trigger "
            "(file-typed input variables must be trigger-bound)."
        )

    # File variable must exist as a flow `in` of type "file" with triggerNodeId binding
    globals_ = (flow.get("variables") or {}).get("globals") or []
    var = next((v for v in globals_ if v.get("id") == file_var_id), None)
    if var is None:
        _fail(
            f"inputs.attachment references `$vars.{trigger_id}.output.{file_var_id}` but no "
            f"flow `globals` variable with id={file_var_id!r} exists. Declare it as an `in` "
            "variable of type `file` with `triggerNodeId` set to the trigger id."
        )
    if var.get("direction") != "in":
        _fail(
            f"flow input variable `{file_var_id}` has direction={var.get('direction')!r}; "
            "must be `in` to receive the attachment from outside the flow."
        )
    if var.get("type") != "file":
        _fail(
            f"flow input variable `{file_var_id}` has type={var.get('type')!r}; must be `file` "
            "to hold the full Flow Attachment `{ FullName, Id, Metadata, MimeType }` payload at runtime."
        )
    if var.get("triggerNodeId") != trigger_id:
        _fail(
            f"flow input variable `{file_var_id}` has triggerNodeId={var.get('triggerNodeId')!r}; "
            f"must be {trigger_id!r} to surface under that trigger's output."
        )


def _check_no_instance_model(node: dict) -> None:
    if "model" in node:
        _fail(
            "Batch Transform node instance has a `model` block. Per rule 16, BPMN type / "
            "serviceType belong only in `definitions[].model`. Drop the instance `model` field."
        )


def _check_type_version(node: dict) -> None:
    tv = node.get("typeVersion")
    if tv != EXPECTED_TYPE_VERSION:
        _fail(
            f"typeVersion={tv!r}; must be {EXPECTED_TYPE_VERSION!r} (matches "
            "`definitions[<batch-transform>].version`). `1.0.0` is wrong."
        )


def _check_output_source(node: dict) -> None:
    src = ((node.get("outputs") or {}).get("output") or {}).get("source")
    if src != EXPECTED_OUTPUT_SOURCE:
        _fail(
            f"outputs.output.source={src!r}; must be {EXPECTED_OUTPUT_SOURCE!r} (the BPMN "
            "engine wraps its result under that key — convention every ServiceTask follows). "
            "`=batchTransformResult` is a stale pre-#1380 shape."
        )


def _check_result_output_mapping(flow: dict, bt_node_id: str) -> None:
    globals_ = (flow.get("variables") or {}).get("globals") or []
    result_var = next(
        (v for v in globals_ if v.get("id") == "result" and v.get("direction") == "out"),
        None,
    )
    if result_var is None:
        _fail(
            "flow has no `out` variable with id='result'. The task prompt asks for the "
            "Batch Transform result file handle to be surfaced as a flow output named `result`."
        )

    end_nodes = [n for n in flow.get("nodes", []) if n.get("type") == "core.control.end"]
    if not end_nodes:
        _fail("flow has no End node — required to terminate the path and map outputs")

    for end in end_nodes:
        src = ((end.get("outputs") or {}).get("result") or {}).get("source")
        if not isinstance(src, str) or not src.strip():
            continue
        m = _OUTPUT_MAPPING_REF.match(src.strip())
        if m and m.group(1) == bt_node_id:
            return

    _fail(
        f"no End node maps `outputs.result.source` to `=js:$vars.{bt_node_id}.output` "
        "(or similar). Without an `=js:` mapping per rule 12, the flow output is the literal "
        "string instead of the real BT result handle."
    )


def main():
    flow = _read_flow()
    node = _find_node(flow)
    inputs = node.get("inputs") or {}

    _check_no_instance_model(node)
    _check_type_version(node)

    prompt = inputs.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        _fail("inputs.prompt missing or empty")

    _check_attachment_canonical(flow, inputs.get("attachment"))
    _check_outputColumns(inputs.get("outputColumns"))
    _check_output_source(node)
    _check_result_output_mapping(flow, node["id"])

    print(
        f"OK: {NODE_TYPE} node present; no instance model; typeVersion=1.0; prompt set; "
        f"attachment wired via trigger output to a `type: file` `in` variable; "
        f"outputColumns has {len(inputs['outputColumns'])} {{name,description}} entries; "
        f"output source=`=response`; End node maps `result` via `=js:` reference"
    )


if __name__ == "__main__":
    main()
