#!/usr/bin/env python3
"""Grade that an authored BPMN opens on the Studio Web canvas without expression errors.

Two canvas contracts that `compile` and `validate` both accept, so only this
check catches them (dogfood 2026-11-17, issues 6 and 7):

1. Every expression the author wrote, in any field (an attribute, an element's
   text, or a string inside a JSON body), is JavaScript: it starts with `=js:`.
   The designer opens a plain `=` expression in its C# editor.
   Exempt, as the canvas writes them: a row `source` reading the node's own
   result (`=result…`, `=response…`, `=Error`, a form or agent field such as `=Action`),
   an output row `source` of exactly `=this["<name>"]`, `=bindings.<id>`,
   `=iterator…`, a `=jsonString:` configuration blob, the script envelope
   (`=vars`, `=metadata`), a human-task form input (`=vars.<path>` in
   `HitlTaskArguments`), and the start-event row that maps a process input
   (`=vars.<inputId>`). Names, ids, documentation and annotations are literal
   text and not scanned; at least one `=js:` must exist.
2. No element reads a variable that is not set where it runs. A process input
   belongs to the start event, so reading `vars.<inputId>` downstream is "A
   variable is unresolved" on the canvas; `validate` reports it only as a
   `VARIABLE_NOT_SET` warning.

Usage: check_canvas_ready.py <Name>.bpmn [--check js|scope]   (default: both)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
from bpmn_check import NS, fail, resolve_bpmn_file  # noqa: E402
import xml.etree.ElementTree as ET  # noqa: E402

RESULT_READ = re.compile(r"^=((result|response|Error|iterator)(\.\w+|\[\d+\])*$|bindings\.|jsonString:)")
# The engine reads the key raw up to the first `]`, so a key never contains one.
THIS_READ = re.compile(r'^=this\["[^\]]*"\]$')
# A form or agent output field (`=Decision`); also lets an undeclared typo such as `=totl` pass.
BARE_FIELD = re.compile(r"^=(?!(true|false|null)$)[A-Za-z_]\w*$")
ENVELOPE = re.compile(r"^=(vars|metadata)$")
FORM_INPUT = re.compile(r"^=vars\.[\w.\[\]]+$")
# Literal text, never evaluated: a node or row name, an id, documentation, an annotation.
LITERAL_ATTRS = {"id", "name"}
LITERAL_TEXT = {"documentation", "text"}


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def strings(value: object):
    """Every string inside a parsed JSON value (a body or arguments input)."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def main() -> None:
    args = sys.argv[1:]
    checks = {"js", "scope"}
    if len(args) == 3 and args[1] == "--check" and args[2] in checks:
        checks = {args[2]}
    elif len(args) != 1:
        fail("usage: check_canvas_ready.py <Name>.bpmn [--check js|scope]")
    path = resolve_bpmn_file(args[0])
    root = ET.parse(path).getroot()

    inputs = {v.get("id") for v in root.iter(f"{{{NS['uipath']}}}input") if v.get("elementId")}
    starts = {e.get("id") for e in root.iter(f"{{{NS['bpmn']}}}startEvent")}
    declared = {e.get("id") for e in root.iter() if e.get("id") and e.get("elementId")}
    forms = {e.get("id") for e in root.iter(f"{{{NS['bpmn']}}}userTask")}

    bad: list[str] = []
    authored = 0

    def scan(value: str, owner: str | None, where: str) -> None:
        value = value.strip()
        if value[:1] in "[{":
            try:
                parsed = json.loads(value)
            except ValueError:
                parsed = None
            if parsed is not None:
                for s in strings(parsed):
                    scan(s, owner, where)
                return
        nonlocal authored
        if value.startswith("=js:"):
            authored += 1
        if not value.startswith("=") or value.startswith("=js:"):
            return
        if owner in starts and re.fullmatch(r"=vars\.(\w+)", value) and value[6:] in inputs:
            return
        if RESULT_READ.match(value) or ENVELOPE.match(value):
            return
        if THIS_READ.match(value) and where == "output@source":
            return
        if BARE_FIELD.match(value) and where.endswith("@source") and (owner in forms or value[1:] not in declared):
            return
        if "[HitlTaskArguments]" in where and FORM_INPUT.match(value):
            return
        bad.append(f"{owner}: {where} {value!r}")

    def walk(element: ET.Element, owner: str | None) -> None:
        owner = element.get("id") or owner
        for attr, value in element.attrib.items():
            if local(attr) not in LITERAL_ATTRS:
                scan(value, owner, f"{local(element.tag)}@{local(attr)}")
        if element.text and local(element.tag) not in LITERAL_TEXT:
            name = element.get("name")
            scan(element.text, owner, local(element.tag) + (f"[{name}]" if name else ""))
        for child in element:
            walk(child, owner)

    for process in root.iter(f"{{{NS['bpmn']}}}process"):
        walk(process, None)
    if bad and "js" in checks:
        fail(
            "expressions not written as =js: (the designer opens them as C#):\n  "
            + "\n  ".join(sorted(set(bad)))
        )
    if "js" in checks and not authored:
        fail("no =js: expression: the process computes nothing")

    if "scope" not in checks:
        print(f"OK: {path} writes every authored expression as =js:")
        return
    proc = subprocess.run(
        ["uip", "maestro", "bpmn", "validate", str(path), "--output", "json"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    try:
        data = json.loads(proc.stdout).get("Data") or {}
    except ValueError:
        fail(f"validate printed no JSON: {(proc.stdout or proc.stderr)[-800:]}")
    # Fail closed: a report this grader cannot read must not pass as "no unset reads".
    if data.get("Status") != "Valid":
        fail(f"validate did not report Status Valid: {json.dumps(data)[-1200:]}")
    warnings = data.get("Warnings") or ""
    if not isinstance(warnings, str):
        fail(f"validate Warnings is not the text this grader reads: {warnings!r}"[:1200])
    lines = [line.strip() for line in warnings.splitlines() if line.strip()]
    if lines and not re.fullmatch(r"\d+ warning\(s\):", lines[0]):
        fail(f"unrecognized validate Warnings header: {lines[0]!r}")
    found = [re.fullmatch(r"- \[([^\]]+)\] (\w+)\b.*", line) for line in lines[1:]]
    if not all(found):
        fail(f"unrecognized validate warning line(s): {[l for l, m in zip(lines[1:], found) if not m]}")
    unset = [m.groups() for m in found if m.group(2) in {"VARIABLE_NOT_SET", "VARIABLE_DOES_NOT_EXIST"}]
    if unset:
        fail(f"variables read where they are not set: {sorted(set(unset))}\n{warnings[-1200:]}")
    print(f"OK: {path} writes =js: expressions and reads only variables set upstream")


if __name__ == "__main__":
    main()
