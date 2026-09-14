#!/usr/bin/env python3
"""Variable-scope check.

Every `<uipath:variables>` declaration must carry an `elementId` that resolves
to a real element, and the scope must make the variable reachable where it is
used: the caller-supplied input keyed to the start event, and a variable read by a gateway
keyed either to the `<bpmn:process>` id or to the node whose mapping writes it
(the canvas emits the latter for a task output — `VariableMutationUtils.ts`).

Deliberately NOT asserted: the `custom` attribute, whose effect on canvas
re-sync is unverified.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared.bpmn_check import NS, fail, parse_bpmn, text_content  # noqa: E402

DECL_TAGS = ("input", "output", "inputOutput")


def declarations(root):
    """Every declaration child of every `<uipath:variables>` block."""
    out = []
    for block in root.iter("{%s}variables" % NS["uipath"]):
        for child in block:
            if child.tag.split("}")[1] in DECL_TAGS:
                out.append(child)
    return out


def condition_text(root):
    return " ; ".join(
        text_content(c)
        for c in root.iter("{%s}conditionExpression" % NS["bpmn"])
    )


def main() -> None:
    path, root = parse_bpmn("TierRouting")

    process = root.find("bpmn:process", NS)
    if process is None:
        fail(f"{path}: no <bpmn:process>")
    process_id = process.attrib.get("id")

    # The canvas resolves an elementId against the process id plus flow-element
    # and edge ids only; a DI shape id is an orphan and gets deleted on import
    # (migrations/s191_2-migration-utils.ts).
    all_ids = {process_id} | {
        e.attrib["id"] for e in process.iter()
        if e.attrib.get("id") and e.tag.startswith("{%s}" % NS["bpmn"])
    }
    start_ids = {e.attrib.get("id") for e in root.iter("{%s}startEvent" % NS["bpmn"])}

    decls = declarations(root)
    if not decls:
        fail(f"{path}: no variable declarations in <uipath:variables>")

    # 1. Every declaration carries an elementId.
    unscoped = [d.attrib.get("id") or d.attrib.get("name") for d in decls
                if not d.attrib.get("elementId")]
    if unscoped:
        fail(f"{path}: declarations without an elementId: {sorted(unscoped)}. "
             "Every <uipath:variables> child needs one.")
    print(f"OK: all {len(decls)} declarations carry an elementId")

    # 2. Every elementId resolves to an element that exists.
    dangling = {d.attrib.get("id"): d.attrib["elementId"] for d in decls
                if d.attrib["elementId"] not in all_ids}
    if dangling:
        fail(f"{path}: elementId does not match any element in the file: {dangling}")
    print("OK: every elementId resolves to a real element")

    # 3. The caller-supplied input is start-event scoped. The canvas writes a
    #    caller argument as a root `input` keyed to the start event that accepts
    #    it (reducers/canvasSlice.ts updateRootVariablesForInput); any other
    #    scope is not a caller-suppliable input.
    amount = [d for d in decls
              if (d.attrib.get("name") or "").lower() == "amount"
              or (d.attrib.get("id") or "").lower().endswith("amount")]
    if not amount:
        fail(f"{path}: no declaration for the caller-supplied amount")
    if not any(d.attrib["elementId"] in start_ids for d in amount):
        got = {d.attrib.get("id"): d.attrib["elementId"] for d in amount}
        fail(f"{path}: the caller-supplied amount must be scoped to the start event "
             f"so the caller can pass it in; got {got}")
    print("OK: caller-supplied amount is start-event scoped")

    # 4. The variable the gateway reads is reachable from that gateway: either
    #    process-scoped (globally available), or scoped to a node whose mapping
    #    writes it via `var=` — which is the shape the canvas itself emits for a
    #    task output (VariableMutationUtils.ts). Both are valid; a scope that is
    #    neither is not reachable downstream.
    conditions = condition_text(root)
    if not conditions:
        fail(f"{path}: no gateway conditionExpression found")
    # Which element writes each variable: the nearest id-bearing ancestor of
    # each mapping `<uipath:output var="...">`.
    parents = {child: parent for parent in process.iter() for child in parent}
    writers = {}
    for m in process.iter("{%s}output" % NS["uipath"]):
        var = m.attrib.get("var")
        if not var:
            continue
        node = parents.get(m)
        while node is not None and not node.attrib.get("id"):
            node = parents.get(node)
        if node is not None:
            writers[var] = node.attrib["id"]
    # Match by `id` only. The canvas resolves a `vars.X` reference against a
    # declaration's id (and its canonicalId, which is backfilled only for
    # legacy obfuscated ids), never its `name` — so accepting a name match here
    # would pass a file the canvas rejects with VARIABLE_DOES_NOT_EXIST.
    read_by_gateway = [
        d for d in decls
        if d.attrib.get("id")
        and re.search(r"\bvars\.%s\b" % re.escape(d.attrib["id"]), conditions)
    ]
    if not read_by_gateway:
        referenced = sorted(set(re.findall(r"\bvars\.([A-Za-z_$][\w$]*)", conditions)))
        declared = sorted(d.attrib.get("id") or "?" for d in decls)
        fail(f"{path}: no declared variable id is read by a gateway condition. "
             f"Conditions reference {referenced}; declared ids are {declared}. "
             "References resolve by id, not by name.")
    unreachable = {}
    for d in read_by_gateway:
        eid = d.attrib["elementId"]
        vid = d.attrib.get("id")
        if eid == process_id or writers.get(vid) == eid:
            continue
        unreachable[vid] = eid
    if unreachable:
        fail(f"{path}: a variable read by a gateway condition must be scoped to the "
             f"process id {process_id!r}, or to the node whose mapping writes it; "
             f"got {unreachable}")
    print(f"OK: gateway-read variable(s) reachable from the gateway "
          f"({ {d.attrib.get('id'): d.attrib['elementId'] for d in read_by_gateway} })")

    print("PASS: all variable-scope checks passed")


if __name__ == "__main__":
    main()
