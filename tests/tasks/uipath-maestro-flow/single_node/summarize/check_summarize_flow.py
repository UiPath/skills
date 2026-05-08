#!/usr/bin/env python3
"""SummarizeDemo: structural check for the Summarize pattern node.

Generation-only — does not run `uip maestro flow debug`. Verifies:

  1. Exactly one `uipath.pattern.deep-rag` node is present (the wire type
     stays `deep-rag` even though the canvas display name is "Summarize").
  2. The instance has no `model` block (BPMN type/serviceType lives in
     `definitions[].model` only — rule 16).
  3. `typeVersion` is exactly `"1.0"` (matches `definitions[<dr>].version`).
  4. `inputs.prompt` is non-empty.
  5. `inputs.attachment` matches the canonical canvas-produced wiring:
     `=js:$vars.<triggerId>.output.<fileVarId>` — referencing a flow `in`
     variable of `type: "file"` bound to the trigger via `triggerNodeId`.
  6. `inputs.returnCitations` is the boolean `true` (per the prompt's request).
  7. The instance `outputs.output.source` is the literal `=response`.
  8. The flow declares `out` variables `summary` and `citations`, and at least
     one End node maps each via PascalCase paths:
       summary    -> =js:$vars.<dr>.output.content.Text
       citations  -> =js:$vars.<dr>.output.content.Citations
     Lowercase `.text` / `.citations` is rejected (the response shape is
     PascalCase; lowercase resolves to undefined at runtime).
"""

import glob
import json
import re
import sys
from typing import NoReturn

NODE_TYPE = "uipath.pattern.deep-rag"
EXPECTED_TYPE_VERSION = "1.0"
EXPECTED_OUTPUT_SOURCE = "=response"

_ATTACHMENT_REF = re.compile(
    r"^=js:\s*\$vars\.([A-Za-z_][A-Za-z0-9_]*)\.output\.([A-Za-z_][A-Za-z0-9_]*)\s*$"
)
_OUTPUT_MAPPING_BASE = re.compile(r"^=js:\s*\$vars\.([A-Za-z_][A-Za-z0-9_]*)\.output\.content\.")


def _fail(msg: str) -> NoReturn:
    sys.exit(f"FAIL: {msg}")


def _read_flow() -> dict:
    flows = glob.glob("**/SummarizeDemo*.flow", recursive=True)
    if not flows:
        _fail("no SummarizeDemo*.flow found under cwd")
    with open(flows[0]) as f:
        return json.load(f)


def _find_node(flow: dict) -> dict:
    matches = [n for n in flow.get("nodes", []) if n.get("type") == NODE_TYPE]
    if not matches:
        types = sorted({n.get("type") for n in flow.get("nodes", [])})
        _fail(
            f"no node with type {NODE_TYPE!r}; types seen: {types}. "
            f"Note: the wire type stays 'deep-rag' even though the display name is 'Summarize'."
        )
    if len(matches) > 1:
        _fail(f"expected exactly one {NODE_TYPE} node, found {len(matches)}")
    return matches[0]


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
            f"node id={trigger_id!r} has type={trigger_node.get('type')!r}; expected a trigger."
        )

    globals_ = (flow.get("variables") or {}).get("globals") or []
    var = next((v for v in globals_ if v.get("id") == file_var_id), None)
    if var is None:
        _fail(
            f"inputs.attachment references `$vars.{trigger_id}.output.{file_var_id}` but no "
            f"flow `globals` variable with id={file_var_id!r} exists."
        )
    if var.get("direction") != "in":
        _fail(
            f"flow input variable `{file_var_id}` has direction={var.get('direction')!r}; "
            "must be `in`."
        )
    if var.get("type") != "file":
        _fail(
            f"flow input variable `{file_var_id}` has type={var.get('type')!r}; must be `file`."
        )
    if var.get("triggerNodeId") != trigger_id:
        _fail(
            f"flow input variable `{file_var_id}` has triggerNodeId={var.get('triggerNodeId')!r}; "
            f"must be {trigger_id!r}."
        )


def _check_no_instance_model(node: dict) -> None:
    if "model" in node:
        _fail(
            "Summarize node instance has a `model` block. Per rule 16, BPMN type / serviceType "
            "belong only in `definitions[].model`. Drop the instance `model` field."
        )


def _check_type_version(node: dict) -> None:
    tv = node.get("typeVersion")
    if tv != EXPECTED_TYPE_VERSION:
        _fail(
            f"typeVersion={tv!r}; must be {EXPECTED_TYPE_VERSION!r} (matches "
            "`definitions[<deep-rag>].version`). `1.0.0` is wrong."
        )


def _check_output_source(node: dict) -> None:
    src = ((node.get("outputs") or {}).get("output") or {}).get("source")
    if src != EXPECTED_OUTPUT_SOURCE:
        _fail(
            f"outputs.output.source={src!r}; must be {EXPECTED_OUTPUT_SOURCE!r} (the BPMN "
            "engine wraps its result under that key). `=deepRagResult` is a stale "
            "pre-#1380 shape."
        )


def _check_pascal_output_mappings(flow: dict, dr_node_id: str) -> None:
    """The flow surfaces synthesis text + citations as `out` variables. Verify
    both variables exist and at least one End node maps each correctly with
    PascalCase nested paths.
    """
    globals_ = (flow.get("variables") or {}).get("globals") or []
    for var_id in ("summary", "citations"):
        if not any(v.get("id") == var_id and v.get("direction") == "out" for v in globals_):
            _fail(
                f"flow has no `out` variable with id={var_id!r}. The task prompt asks for "
                f"`{var_id}` to be surfaced as a flow output."
            )

    end_nodes = [n for n in flow.get("nodes", []) if n.get("type") == "core.control.end"]
    if not end_nodes:
        _fail("flow has no End node — required to terminate the path and map outputs")

    expected = {
        "summary": "Text",
        "citations": "Citations",
    }
    for var_id, pascal_field in expected.items():
        mapped = False
        for end in end_nodes:
            src = ((end.get("outputs") or {}).get(var_id) or {}).get("source")
            if not isinstance(src, str) or not src.strip():
                continue
            src_stripped = src.strip()
            base_m = _OUTPUT_MAPPING_BASE.match(src_stripped)
            if not base_m or base_m.group(1) != dr_node_id:
                continue
            # Ensure the Pascal field is in the path
            if f".content.{pascal_field}" in src_stripped:
                mapped = True
                break
            # Detect lowercase mistake explicitly
            lowercase_field = pascal_field[0].lower() + pascal_field[1:]
            if f".content.{lowercase_field}" in src_stripped:
                _fail(
                    f"End node maps `outputs.{var_id}.source={src!r}` using lowercase "
                    f"`.content.{lowercase_field}` — the response shape is PascalCase "
                    f"`.content.{pascal_field}`. Lowercase fields resolve to undefined at runtime."
                )
        if not mapped:
            _fail(
                f"no End node maps `outputs.{var_id}.source` to "
                f"`=js:$vars.{dr_node_id}.output.content.{pascal_field}` (or a deeper path). "
                "Without the PascalCase mapping, the flow output is the literal string or "
                "undefined at runtime."
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

    return_citations = inputs.get("returnCitations")
    if return_citations is not True:
        _fail(
            f"inputs.returnCitations must be the boolean true (the prompt requested citations), "
            f"got {return_citations!r}"
        )

    _check_output_source(node)
    _check_pascal_output_mappings(flow, node["id"])

    print(
        f"OK: {NODE_TYPE} node present; no instance model; typeVersion=1.0; prompt set; "
        f"attachment wired via trigger output to a `type: file` `in` variable; "
        f"returnCitations=true; output source=`=response`; End node maps `summary` to "
        f"`content.Text` and `citations` to `content.Citations` (PascalCase) via `=js:`"
    )


if __name__ == "__main__":
    main()
