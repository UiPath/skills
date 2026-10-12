#!/usr/bin/env python3
"""DfPickerFlow: the folder-entity picker resolved into the solution, and the
connector node binds that entity in its folder."""

import glob
import json
import sys

NODE_TYPE = "uipath.connector.uipath-uipath-dataservice.create-entity-record-preview-"


def main():
    with open("_setup/picker_entity.json") as f:
        fixture = json.load(f)
    name, key, folder_key = fixture["name"], fixture["key"], fixture["folderKey"]

    keys = []
    for path in glob.glob("**/resources/**/entity/**/*.json", recursive=True):
        with open(path) as f:
            resource = json.load(f).get("resource", {})
        if (resource.get("name") or "").lower() == name.lower():
            keys.append(resource.get("key"))
    if key not in keys:
        sys.exit(f"FAIL: {name} ({key}) was not referenced into the solution (keys found: {keys})")

    flows = [p for p in glob.glob("**/*.flow", recursive=True) if "/.venv/" not in p]
    for path in flows:
        with open(path) as f:
            text = f.read()
        flow = json.loads(text)
        if not any(n.get("type") == NODE_TYPE for n in flow.get("nodes", [])):
            continue
        if not any(b.get("resource") == "entity" for b in flow.get("bindings", [])):
            sys.exit(f"FAIL: {path} has the node but no entity binding")
        if folder_key not in text:
            sys.exit(f"FAIL: {path} does not carry the entity's folder key {folder_key}")
        print(f"OK: {path}: {name} referenced into the solution and bound on the node in its folder")
        return
    sys.exit(f"FAIL: no {NODE_TYPE} node in {flows}")


if __name__ == "__main__":
    main()
