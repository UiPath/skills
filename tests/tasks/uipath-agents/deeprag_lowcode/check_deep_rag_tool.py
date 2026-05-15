#!/usr/bin/env python3
"""Built-in deep-rag tool resource check.

Validates that the low-code agent enabled the built-in `deep-rag` tool
by authoring a resource.json under DeepSol/DeepAgent/resources/ that
matches the static built-in-tools registry:

  - $resourceType == "tool"
  - type == "internal"
  - referenceKey is null
  - properties.toolType == "deep-rag"
  - id is a UUID-shaped string
  - isEnabled is truthy

The resource directory name is not prescribed; we scan every
resource.json under DeepSol/DeepAgent/resources/.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "DeepSol" / "DeepAgent"
RESOURCES_DIR = ROOT / "resources"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def find_resource_jsons() -> list:
    if not RESOURCES_DIR.is_dir():
        sys.exit(f"FAIL: {RESOURCES_DIR} does not exist — no resources/ directory")
    files = sorted(RESOURCES_DIR.rglob("resource.json"))
    if not files:
        sys.exit(f"FAIL: no resource.json files found under {RESOURCES_DIR}")
    return files


def check_deep_rag(path: Path, resource: dict) -> None:
    if resource.get("$resourceType") != "tool":
        sys.exit(f'FAIL: {path} $resourceType should be "tool", got {resource.get("$resourceType")!r}')
    if resource.get("type") != "internal":
        sys.exit(f'FAIL: {path} type should be "internal" for a built-in tool, got {resource.get("type")!r}')
    if resource.get("referenceKey") is not None:
        sys.exit(f"FAIL: {path} referenceKey should be null for a built-in tool, got {resource.get('referenceKey')!r}")
    rid = resource.get("id")
    if not isinstance(rid, str) or "-" not in rid:
        sys.exit(f"FAIL: {path} resource id missing or malformed: {rid!r}")
    if not resource.get("isEnabled"):
        sys.exit(f"FAIL: {path} resource.isEnabled must be truthy")
    tool_type = (resource.get("properties") or {}).get("toolType")
    if tool_type != "deep-rag":
        sys.exit(f'FAIL: {path} properties.toolType should be "deep-rag", got {tool_type!r}')


def main() -> None:
    files = find_resource_jsons()
    found_deep_rag = False
    for path in files:
        data = load(path)
        if (data.get("properties") or {}).get("toolType") == "deep-rag":
            check_deep_rag(path, data)
            found_deep_rag = True
    if not found_deep_rag:
        sys.exit('FAIL: no resource.json with properties.toolType == "deep-rag" found')
    print("PASS")


if __name__ == "__main__":
    main()
