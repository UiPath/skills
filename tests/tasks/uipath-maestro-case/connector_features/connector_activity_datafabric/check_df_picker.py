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

CASEPLAN = "DfPickerCase/DfPickerCase/caseplan.case"


def values_for(node, field):
    """Every value `field` holds anywhere under `node`."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == field:
                yield v
            yield from values_for(v, field)
    elif isinstance(node, list):
        for item in node:
            yield from values_for(item, field)


def main():
    with open("_setup/picker_entity.json") as f:
        fixture = json.load(f)
    name, key, folder_key = fixture["name"], fixture["key"], fixture["folderKey"]

    # `case init` scaffolds caseplan.case now; the shared helpers default to caseplan.json.
    task = assert_task_type_present(
        "execute-connector-activity",
        caseplan_path=CASEPLAN,
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
    data = task.get("data") or {}
    scopes = {v for v in values_for(data, "entityScope") if isinstance(v, str)}
    if "folder" not in scopes:
        sys.exit(f"FAIL: the task's entityScope is {sorted(scopes)}, not 'folder'")

    with open(CASEPLAN) as f:
        bindings = json.load(f).get("bindings") or []
    by_id = {b.get("id"): b for b in bindings}

    def bound_rows(field):
        """The root bindings the task's `field` values point at."""
        refs = {v for v in values_for(data, field) if isinstance(v, str)}
        return refs, [by_id[r[len("=bindings."):]] for r in refs if r.startswith("=bindings.") and r[len("=bindings."):] in by_id]

    refs, rows = bound_rows("folderEntityName")
    picked = [b for b in rows if b.get("resourceKey") == key and (b.get("resource") or "").lower() == "entity"
              and (b.get("default") or "").lower() == name.lower()]
    if not picked:
        sys.exit(f"FAIL: the task's folderEntityName is {sorted(refs)}, not =bindings.<id> of an entity binding for "
                 f"{name} ({key}); copy spec.resourceBindings into bindings[] and the task inputs")

    folder_refs, folder_rows = bound_rows("folderEntityName_folderKey")
    if not any(b.get("default") == folder_key for b in folder_rows) and folder_key not in folder_refs:
        sys.exit(f"FAIL: the task's folderEntityName_folderKey is {sorted(folder_refs)}, not the {fixture['folderPath']} "
                 f"folder ({folder_key})")

    print(f"OK: Data Fabric activity resolved (typeId set, connectorKey={ck!r}); {name} referenced into the solution and bound on the task")


if __name__ == "__main__":
    main()
