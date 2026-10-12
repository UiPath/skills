#!/usr/bin/env python3
"""DfPickerCase: the Data Fabric connector activity resolved, and its entity
picker was referenced into the solution by `case spec --solution-folder`.
The entity is the one `_setup/ensure_folder_entity.py` recorded."""

import glob
import json
import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)
from _shared.case_check import (  # noqa: E402
    assert_task_type_present,
    task_is_skeleton,
)

def main():
    with open("_setup/picker_entity.json") as f:
        fixture = json.load(f)
    name, key = fixture["name"], fixture["key"]

    # `case init` scaffolds caseplan.case now; the shared helpers default to caseplan.json.
    task = assert_task_type_present(
        "execute-connector-activity",
        caseplan_path="DfPickerCase/DfPickerCase/caseplan.case",
    )
    if task_is_skeleton(task):
        sys.exit("FAIL: execute-connector-activity task is a skeleton (no typeId / connectionId)")
    context = (task.get("data") or {}).get("context", [])
    ck = next((c.get("value") for c in context if c.get("name") == "connectorKey"), None)
    if ck != "uipath-uipath-dataservice":
        sys.exit(f"FAIL: expected connectorKey 'uipath-uipath-dataservice'; got {ck!r}")

    entities = []
    for path in glob.glob("DfPickerCase/resources/**/entity/**/*.json", recursive=True):
        with open(path) as f:
            resource = json.load(f).get("resource", {})
        if (resource.get("name") or "").lower() == name.lower():
            entities.append(resource.get("key"))
    if key not in entities:
        sys.exit(
            f"FAIL: the folderEntityName picker was not referenced into the solution "
            f"({name} keys found: {entities}); run case spec with --solution-folder"
        )
    print(f"OK: Data Fabric activity resolved (typeId set, connectorKey={ck!r}); {name} referenced into the solution")


if __name__ == "__main__":
    main()
