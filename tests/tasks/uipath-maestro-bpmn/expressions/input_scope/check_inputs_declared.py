#!/usr/bin/env python3
"""Grade that the process takes its start values as process inputs and uses them.

Guards check_canvas_ready.py --check scope from passing for the wrong reason:
an input nothing reads leaves nothing to scope, so the scope check is vacuous.
An input counts only when a start event maps it into a variable (a row whose
source reads `vars.<input>`) and an element outside that start event reads
that variable.

Usage: check_inputs_declared.py <Name>.bpmn <min_inputs>
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
from bpmn_check import NS, fail, resolve_bpmn_file  # noqa: E402
import xml.etree.ElementTree as ET  # noqa: E402


def reads(text: str, var: str) -> bool:
    return re.search(rf"\bvars\.{re.escape(var)}\b", text) is not None


def texts(elements) -> list[str]:
    out = []
    for el in elements:
        out.extend(el.attrib.values())
        out.append(el.text or "")
    return out


path = resolve_bpmn_file(sys.argv[1])
root = ET.parse(path).getroot()
inputs = [v.get("id") for v in root.iter(f"{{{NS['uipath']}}}input") if v.get("elementId")]
starts = [el for el in root.iter() if el.tag.endswith("}startEvent")]
in_start = {id(e) for s in starts for e in s.iter()}
elsewhere = texts(e for e in root.iter() if id(e) not in in_start)
rows = [o for s in starts for o in s.iter(f"{{{NS['uipath']}}}output") if o.get("var")]

used = []
for name in inputs:
    mapped = [o.get("var") for o in rows if reads(o.get("source") or "", name)]
    if any(reads(t, var) for var in mapped for t in elsewhere):
        used.append(name)
if len(used) < int(sys.argv[2]):
    fail(
        f"expected at least {sys.argv[2]} process inputs mapped by a start event"
        f" into a variable a later step reads; declared {inputs}, used {used}"
    )
print(f"OK: {path} maps and reads process inputs {used}")
