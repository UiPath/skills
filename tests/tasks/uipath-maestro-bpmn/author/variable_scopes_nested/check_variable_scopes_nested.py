#!/usr/bin/env python3
"""Variable-scope check for nested and multi-entry scoping.

Covers the scopes the single-entry check cannot reach:
  - two start events, each owning its own caller-supplied input, with no input
    leaking onto the other entry point
  - a variable owned by a subprocess, declared in the subprocess's own
    `<uipath:variables>` block and keyed to an element inside that subprocess
  - a public output keyed to a root end event

Every assertion reads the authored `.bpmn`. Generated metadata
(`entry-points.json`) is deliberately not asserted: the CLI packager produces
it, so grading it would couple this test to another component's behaviour
instead of to the canvas contract.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared.bpmn_check import NS, fail, parse_bpmn  # noqa: E402

DECL_TAGS = ("input", "output", "inputOutput")


def decls_of(owner):
    """Declaration children of the owner's own `<uipath:variables>` block."""
    out = []
    for ext in owner.findall("bpmn:extensionElements", NS):
        for block in ext.findall("uipath:variables", NS):
            for child in block:
                if child.tag.split("}")[1] in DECL_TAGS:
                    out.append(child)
    return out


def ident(d):
    return d.attrib.get("id") or d.attrib.get("name") or "<unnamed>"


def main() -> None:
    path, root = parse_bpmn("OrderEnrich")

    process = root.find("bpmn:process", NS)
    if process is None:
        fail(f"{path}: no <bpmn:process>")
    process_id = process.attrib.get("id")

    # Canvas resolves elementId against the process id plus BPMN element ids;
    # DI shape ids are orphans (migrations/s191_2-migration-utils.ts).
    all_ids = {process_id} | {
        e.attrib["id"] for e in process.iter()
        if e.attrib.get("id") and e.tag.startswith("{%s}" % NS["bpmn"])
    }
    subprocesses = list(process.iter("{%s}subProcess" % NS["bpmn"]))
    root_starts = [e for e in process.findall("bpmn:startEvent", NS)]
    root_ends = {e.attrib.get("id") for e in process.findall("bpmn:endEvent", NS)}

    root_decls = decls_of(process)
    sub_decls = {s.attrib.get("id"): decls_of(s) for s in subprocesses}
    every = root_decls + [d for ds in sub_decls.values() for d in ds]
    if not every:
        fail(f"{path}: no variable declarations found")

    # 1. Every declaration, at every level, carries an elementId.
    unscoped = [ident(d) for d in every if not d.attrib.get("elementId")]
    if unscoped:
        fail(f"{path}: declarations without an elementId: {sorted(unscoped)}")
    print(f"OK: all {len(every)} declarations carry an elementId")

    # 2. Every elementId resolves.
    dangling = {ident(d): d.attrib["elementId"] for d in every
                if d.attrib["elementId"] not in all_ids}
    if dangling:
        fail(f"{path}: elementId does not match any element in the file: {dangling}")
    print("OK: every elementId resolves to a real element")

    # 3. Each root start event owns exactly one caller-supplied input, and no
    #    two start events share one. The canvas writes a caller argument as a
    #    root `input` keyed to the start event that accepts it
    #    (reducers/canvasSlice.ts updateRootVariablesForInput), so a second
    #    start's argument keyed to the first start belongs to the wrong caller.
    if len(root_starts) < 2:
        fail(f"{path}: expected two root start events, found {len(root_starts)}")
    start_ids = {e.attrib.get("id") for e in root_starts}
    inputs = [d for d in root_decls if d.tag.split("}")[1] == "input"]
    stray = {ident(d): d.attrib["elementId"] for d in inputs
             if d.attrib["elementId"] not in start_ids}
    if stray:
        fail(f"{path}: a caller-supplied input must be scoped to the start event that "
             f"accepts it; got {stray}")
    by_start = {}
    for d in inputs:
        by_start.setdefault(d.attrib["elementId"], set()).add(d.attrib.get("name"))
    missing = start_ids - set(by_start)
    if missing:
        fail(f"{path}: start event(s) {sorted(missing)} accept no caller-supplied "
             "input — each start event owns the argument its caller passes in")
    for sid, names in by_start.items():
        if len(names) != 1:
            fail(f"{path}: start event {sid!r} owns {sorted(names)}; each start event "
                 "accepts exactly one caller-supplied input in this process")
    shared = [n for n in {n for ns in by_start.values() for n in ns}
              if sum(1 for ns in by_start.values() if n in ns) > 1]
    if shared:
        fail(f"{path}: input name(s) {sorted(shared)} are claimed by more than one "
             "start event; each caller input belongs to exactly one entry point")
    print("OK: each start event owns exactly its own caller input "
          f"({ {k: sorted(v) for k, v in by_start.items()} })")

    # 4. A subprocess owns a variable, declared in its own block and keyed
    #    within that subprocess — either the subprocess itself or a node inside
    #    it. Both are accepted deliberately: the canvas keys such a variable to
    #    the writing node (VariableMutationUtils.ts) and reserves the
    #    self-keyed form for user-created custom variables, but a non-custom
    #    self-keyed declaration is *relocated* to the root block on import
    #    (migrations/s191_2-migration-utils.ts), not rejected. Grading that
    #    difference would fail a file the platform accepts. What is settled, and
    #    what this asserts, is that the scope must be inside the subprocess:
    #    keyed to a root element it is not the subprocess's variable at all.
    #    Subprocess blocks hold `inputOutput` only (s180-migrations.ts).
    if not subprocesses:
        fail(f"{path}: no <bpmn:subProcess> found")
    with_own = {sid: ds for sid, ds in sub_decls.items() if ds}
    if not with_own:
        fail(f"{path}: no subprocess declares its own variable — a variable owned by "
             "the subprocess belongs in that subprocess's <uipath:variables> block")
    for sub in subprocesses:
        sid = sub.attrib.get("id")
        ds = sub_decls.get(sid) or []
        if not ds:
            continue
        inner_ids = {e.attrib["id"] for e in sub.iter() if e.attrib.get("id")}
        bad_tag = [ident(d) for d in ds if d.tag.split("}")[1] != "inputOutput"]
        if bad_tag:
            fail(f"{path}: subprocess {sid!r} may only declare <uipath:inputOutput>; "
                 f"got other tags for {sorted(bad_tag)}")
        wrong = {ident(d): d.attrib["elementId"] for d in ds
                 if d.attrib["elementId"] not in inner_ids}
        if wrong:
            fail(f"{path}: a variable owned by subprocess {sid!r} must be scoped "
                 f"within that subprocess — {sid!r} itself, or a node inside it; "
                 f"got {wrong}")
    print(f"OK: subprocess-owned variable(s) declared and scoped inside "
          f"({sorted(with_own)})")

    # 5. The public output is keyed to a root end event. The canvas writes root
    #    `outputs` only through the end-event pair reducer (canvasSlice.ts
    #    updateRootVariablesForOutput), and migration 13 forces basic end-event
    #    outputs into that shape (migrations/s191_2-migration-utils.ts).
    outputs = [d for d in root_decls if d.tag.split("}")[1] == "output"]
    if not outputs:
        fail(f"{path}: no <uipath:output> declaration — the process must publish a result")
    bad = {ident(d): d.attrib["elementId"] for d in outputs
           if d.attrib["elementId"] not in root_ends}
    if bad:
        fail(f"{path}: a published output must be scoped to a root end event "
             f"{sorted(root_ends)}; got {bad}")
    print("OK: published output(s) scoped to a root end event "
          f"({sorted(ident(d) for d in outputs)})")

    print(f"PASS: nested and multi-entry variable scopes correct (process {process_id!r})")


if __name__ == "__main__":
    main()
