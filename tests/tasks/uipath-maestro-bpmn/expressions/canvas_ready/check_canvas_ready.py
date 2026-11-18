#!/usr/bin/env python3
"""Grade that an authored BPMN opens on the Studio Web canvas without expression errors.

Two canvas contracts that `compile` and `validate` both accept, so only this
check catches them (dogfood 2026-11-17, issues 6 and 7):

1. Every expression the author wrote, in any field (an attribute, an element's
   text, or a string inside a JSON body), is JavaScript: it starts with `=js:`.
   The designer opens a value that starts with a plain `=` in its C# editor.
   Exempt, as the canvas writes them: a row `source` reading the node's own
   result (`=result…`, `=response…`, `=Error`, a form field such as `=Action`),
   `=bindings.<id>`, `=iterator…`, a `=jsonString:` configuration blob, and the start-event row that maps a process
   input (`=vars.<inputId>`).
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

RESULT_READ = re.compile(r"^=(result|response|Error|bindings\.|iterator|jsonString:)")
BARE_FIELD = re.compile(r"^=[A-Za-z_]\w*$")


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

    bad: list[str] = []

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
        if not value.startswith("=") or value.startswith("=js:"):
            return
        if owner in starts and re.fullmatch(r"=vars\.(\w+)", value) and value[6:] in inputs:
            return
        if RESULT_READ.match(value) or BARE_FIELD.match(value):
            return
        bad.append(f"{owner}: {where} {value!r}")

    def walk(element: ET.Element, owner: str | None) -> None:
        owner = element.get("id") or owner
        for attr, value in element.attrib.items():
            scan(value, owner, f"{local(element.tag)}@{local(attr)}")
        if element.text:
            scan(element.text, owner, local(element.tag))
        for child in element:
            walk(child, owner)

    for process in root.iter(f"{{{NS['bpmn']}}}process"):
        walk(process, None)
    if bad and "js" in checks:
        fail(
            "expressions not written as =js: (the designer opens them as C#):\n  "
            + "\n  ".join(sorted(set(bad)))
        )

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
    report = json.dumps(data)
    unset = re.findall(r"\[([^\]]+)\] (VARIABLE_NOT_SET|VARIABLE_DOES_NOT_EXIST)[^\\\"]*", report)
    if unset:
        fail(f"variables read where they are not set: {sorted(set(unset))}\n{report[-1200:]}")
    print(f"OK: {path} writes =js: expressions and reads only variables set upstream")


if __name__ == "__main__":
    main()
