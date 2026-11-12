#!/usr/bin/env python3
"""Grade a "draft project" request that asked for source files, not a draft gate.

The word "draft" names a deliverable here, so the agent builds: the project's
`.bpmn` carries at least one typed activity (not only the bare `bpmn:task`
boxes a draft-gate skeleton has), sits beside `project.uiproj`, and
`uip maestro bpmn validate` reports it Valid.

Usage: check_draft_word_build.py <ProjectName>
"""

import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import NS, fail, parse_bpmn  # noqa: E402

# A built process uses typed activities; a skeleton has bare bpmn:task only.
TYPED_ACTIVITIES = ("serviceTask", "sendTask", "receiveTask", "scriptTask", "userTask",
                    "businessRuleTask", "manualTask", "callActivity")


def main() -> None:
    path, root = parse_bpmn(sys.argv[1])

    typed = [el for tag in TYPED_ACTIVITIES for el in root.findall(f".//bpmn:{tag}", NS)]
    typed += [t for t in root.findall(".//bpmn:task", NS)
              if t.find(".//uipath:activity", NS) is not None]
    if not typed:
        fail(f"{path} has no typed activity: only bare bpmn:task boxes, a draft-gate skeleton")

    if not os.path.isfile(os.path.join(os.path.dirname(path), "project.uiproj")):
        fail(f"project.uiproj missing beside {path}")

    uip = shutil.which("uip")
    if not uip:
        fail("uip not found on PATH; cannot validate the process")
    res = subprocess.run([uip, "maestro", "bpmn", "validate", path, "--output", "json"],
                         capture_output=True, text=True, timeout=45)
    try:
        data = json.loads(res.stdout).get("Data") or {}
    except ValueError:
        data = {}
    status = data.get("Status") or data.get("status")
    if status != "Valid":
        fail(f"uip maestro bpmn validate did not report Valid (exit {res.returncode}): {res.stdout[:400]}")

    print(f"OK: {path} validates with {len(typed)} typed activit{'y' if len(typed) == 1 else 'ies'}")


if __name__ == "__main__":
    main()
