#!/usr/bin/env python3
"""Grade that the process takes its start values as process inputs.

Guards check_canvas_ready.py --check scope from passing for the wrong reason:
with no `.input()` there is nothing to scope, so the scope check is vacuous.

Usage: check_inputs_declared.py <Name>.bpmn <min_inputs>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
from bpmn_check import NS, fail, resolve_bpmn_file  # noqa: E402
import xml.etree.ElementTree as ET  # noqa: E402

path = resolve_bpmn_file(sys.argv[1])
inputs = [v.get("id") for v in ET.parse(path).getroot().iter(f"{{{NS['uipath']}}}input") if v.get("elementId")]
if len(inputs) < int(sys.argv[2]):
    fail(f"expected at least {sys.argv[2]} process inputs, found {inputs}")
print(f"OK: {path} declares process inputs {inputs}")
