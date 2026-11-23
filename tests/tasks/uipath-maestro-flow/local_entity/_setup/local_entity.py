#!/usr/bin/env python3
"""Seed and check a flow that reads a solution-authored (local) entity.

  local_entity.py seed <SolutionName> <EntityName>
      `uip solution init` + `uip df entities create --local` with a small schema.
  local_entity.py check <EntityName>
      Every native Data Fabric node naming <EntityName> in any .flow under the
      cwd carries the local resource key and the unassigned-folder sentinel,
      and the flow's bindings[] has the Entity rows for that key. At least one
      such node must exist.
"""

import glob
import json
import os
import subprocess
import sys

UNASSIGNED_FOLDER_ID = "99999999-9999-9999-9999-999999999999"
SCHEMA = {
    "fields": [
        {"name": "sku", "type": "STRING", "isRequired": True, "lengthLimit": 50},
        {"name": "quantity", "type": "DECIMAL", "decimalPrecision": 0},
    ]
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def run(cmd: list, cwd: str) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"{' '.join(cmd)} exited {result.returncode}: {result.stdout[-800:]}{result.stderr[-800:]}")


def seed(solution: str, entity: str) -> None:
    run(["uip", "solution", "init", solution, "--output", "json"], ".")
    run(["uip", "df", "entities", "create", entity, "--local", "--body", json.dumps(SCHEMA), "--output", "json"], solution)
    print(f"OK: seeded {solution} with local entity {entity}")


def local_resource_key(entity: str) -> str:
    paths = [p for p in glob.glob(f"**/resources/solution_folder/entity/native/{entity}.json", recursive=True)
             if "node_modules" not in p]
    if len(paths) != 1:
        fail(f"expected one local resource for {entity}, found {paths}")
    return json.load(open(paths[0]))["resource"]["key"]


def check(entity: str) -> None:
    key = local_resource_key(entity)
    flows = [p for p in glob.glob("**/*.flow", recursive=True) if "node_modules" not in p]
    seen = 0
    for path in flows:
        workflow = json.load(open(path))
        nodes = list(workflow.get("nodes", []))
        for sub in (workflow.get("subflows") or {}).values():
            nodes.extend(sub.get("nodes", []))
        for node in nodes:
            if not str(node.get("type", "")).startswith("core.datafabric."):
                continue
            config = (node.get("inputs") or {}).get("entityConfig") or {}
            if str(config.get("entityName", "")).lower() != entity.lower():
                continue
            seen += 1
            where = f"{path}:{node.get('id')}"
            if config.get("_resourceKey") != key:
                fail(f"{where} _resourceKey is {config.get('_resourceKey')!r}, expected local key {key}")
            if config.get("_folderKey") != UNASSIGNED_FOLDER_ID:
                fail(f"{where} _folderKey is {config.get('_folderKey')!r}, expected the local sentinel")
        rows = [b for b in workflow.get("bindings", []) if b.get("resource") == "Entity" and b.get("resourceKey") == key]
        if seen and {r.get("propertyAttribute") for r in rows} < {"name", "folderKey"}:
            fail(f"{path} bindings[] lacks the Entity name/folderKey rows for {key}")
    if not seen:
        fail(f"no core.datafabric.* node reads {entity} in {flows}")
    print(f"OK: {seen} node(s) bound to local {entity} ({key})")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "seed":
        seed(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3 and sys.argv[1] == "check":
        check(sys.argv[2])
    else:
        fail(__doc__)
