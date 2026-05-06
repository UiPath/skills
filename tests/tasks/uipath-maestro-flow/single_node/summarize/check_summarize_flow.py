#!/usr/bin/env python3
"""SummarizeDemo: structural check for the Summarize pattern node.

Generation-only — does not run `uip maestro flow debug`. Verifies:

  1. Exactly one `uipath.pattern.deep-rag` node is present (the wire type
     stays `deep-rag` even though the canvas display name is "Summarize").
  2. `inputs.prompt` is non-empty.
  3. `inputs.attachment` is wired to the WHOLE flow input object via
     `=js:$vars.<name>` — not `.Id`, `.FullName`, or any subfield. The runtime
     wants the full Flow Attachment `{ FullName, Id, Metadata, MimeType }`.
  4. The referenced flow input variable is declared `type: "object"`.
  5. `inputs.returnCitations` is the boolean `true` (per the prompt's request).
"""

import glob
import json
import re
import sys

NODE_TYPE = "uipath.pattern.deep-rag"
_ATTACHMENT_REF = re.compile(r"^=js:\s*\$vars\.([A-Za-z_][A-Za-z0-9_]*)\s*$")


def _fail(msg: str):
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


def main():
    flow = _read_flow()
    node = _find_node(flow)
    inputs = node.get("inputs") or {}

    prompt = inputs.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        _fail("inputs.prompt missing or empty")

    _check_attachment_is_whole_object(flow, inputs.get("attachment"))

    return_citations = inputs.get("returnCitations")
    if return_citations is not True:
        _fail(
            f"inputs.returnCitations must be the boolean true (the prompt requested citations), "
            f"got {return_citations!r}"
        )

    print(
        f"OK: {NODE_TYPE} node present; prompt set; attachment is whole-object ref to a "
        "`type: object` flow input; returnCitations=true"
    )


if __name__ == "__main__":
    main()
