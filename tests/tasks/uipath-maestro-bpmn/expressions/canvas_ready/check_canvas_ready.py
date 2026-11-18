#!/usr/bin/env python3
"""Grade that an authored BPMN opens on the Studio Web canvas without expression errors.

Two canvas contracts that `compile` and `validate` both accept, so only this
check catches them (dogfood 2026-11-17, issues 6 and 7):

1. Every expression the author wrote is JavaScript: it starts with `=js:`.
   The designer opens a value that starts with a plain `=` in its C# editor.
   Exempt, as the canvas writes them: a row `source` reading the node's own
   result (`=result…`, `=response…`, `=Error`, a form field such as `=Action`),
   `=bindings.<id>`, `=iterator…`, and the start-event row that maps a process
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

RESULT_READ = re.compile(r"^=(result|response|Error|bindings\.|iterator)\b")
BARE_FIELD = re.compile(r"^=[A-Za-z_]\w*$")


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


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
    for element in root.iter():
        owner = element.get("id")
        ext = element.find("bpmn:extensionElements", NS)
        if owner and ext is not None:
            for row in ext.iter(f"{{{NS['uipath']}}}output"):
                src = row.get("source") or ""
                if not src.startswith("=") or src.startswith("=js:"):
                    continue
                if owner in starts and re.fullmatch(r"=vars\.(\w+)", src) and src[6:] in inputs:
                    continue
                if RESULT_READ.match(src) or BARE_FIELD.match(src):
                    continue
                bad.append(f"{owner}: output row source {src!r}")
            for row in ext.iter(f"{{{NS['uipath']}}}input"):
                value = row.get("value") or ""
                if value.startswith("=") and not value.startswith("=js:") and not RESULT_READ.match(value):
                    bad.append(f"{owner}: input {row.get('name')!r} value {value!r}")
        if element.tag == f"{{{NS['bpmn']}}}sequenceFlow":
            cond = element.find("bpmn:conditionExpression", NS)
            body = (cond.text or "").strip() if cond is not None else ""
            if body and not body.startswith("=js:"):
                bad.append(f"{owner}: condition {body!r}")
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
