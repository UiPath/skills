#!/usr/bin/env python3
"""DataFabric entity-set context resource check.

Validates that the agent authored a DataFabric context resource per
references/lowcode/capabilities/context/datafabric.md:

  1. A resource under resources/<folder>/resource.json declares:
       - $resourceType == "context"
       - contextType   == "datafabricentityset"  (lowercase — Anti-pattern 12)
       - name == its folder name (convention: folder matches `name`)
  2. `entitySet` is a non-empty list; each entry is an object carrying an
     entity `name` and a `referenceKey` (the DataFabric-specific shape —
     entirely different from index/attachments).
  3. The DataFabric shape has NO `indexName` and NO `settings` — assert both
     are absent so the agent did not copy the index/attachments shape.

Solution-level generation for DataFabric is unsupported, so this check
intentionally does not assert on solution-level files or bindings.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "DataFabricSol" / "CustomerInsightsAgent"
RESOURCES = ROOT / "resources"


def find_datafabric_resource() -> tuple[str, dict]:
    if not RESOURCES.is_dir():
        sys.exit(f"FAIL: {RESOURCES} does not exist — no context resource authored")
    seen = []
    for path in sorted(RESOURCES.rglob("resource.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        seen.append((data.get("$resourceType"), data.get("contextType")))
        if (
            data.get("$resourceType") == "context"
            and data.get("contextType") == "datafabricentityset"
        ):
            print(
                f"OK: found DataFabric context resource at {path.relative_to(ROOT.parent)}"
            )
            return path.parent.name, data
    sys.exit(
        'FAIL: no context resource with $resourceType=="context" and '
        f'contextType=="datafabricentityset" found under {RESOURCES}. Seen '
        f'($resourceType, contextType): {seen}'
    )


def assert_shape(folder_name: str, resource: dict) -> None:
    ctype = resource.get("contextType")
    if ctype != "datafabricentityset":
        sys.exit(
            'FAIL: contextType must be exactly "datafabricentityset" (lowercase), '
            f"got {ctype!r}"
        )
    name = resource.get("name")
    if name != folder_name:
        sys.exit(
            f"FAIL: resource.json name {name!r} must match its folder name "
            f"{folder_name!r} (convention: folder matches `name`)"
        )

    entity_set = resource.get("entitySet")
    if not isinstance(entity_set, list) or not entity_set:
        sys.exit(
            f"FAIL: DataFabric context must carry a non-empty `entitySet` list, "
            f"got {entity_set!r}"
        )
    for i, entity in enumerate(entity_set):
        if not isinstance(entity, dict):
            sys.exit(f"FAIL: entitySet[{i}] must be an object, got {entity!r}")
        if not entity.get("name"):
            sys.exit(f"FAIL: entitySet[{i}] is missing an entity `name`")
        if "referenceKey" not in entity:
            sys.exit(
                f"FAIL: entitySet[{i}] is missing `referenceKey` (the DataFabric "
                "entity key)"
            )
    print(
        f'OK: contextType="datafabricentityset", name=folder={name!r}, '
        f"entitySet has {len(entity_set)} entity reference(s)"
    )

    # DataFabric shape differs from index/attachments: no indexName, no settings.
    if "indexName" in resource:
        sys.exit(
            "FAIL: DataFabric context must NOT carry `indexName` (that is the "
            "index/attachments shape)"
        )
    if "settings" in resource:
        sys.exit(
            "FAIL: DataFabric context must NOT carry `settings` (that is the "
            "index/attachments shape)"
        )
    print("OK: no indexName / settings (correct DataFabric shape)")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: agent directory {ROOT} does not exist")
    folder_name, resource = find_datafabric_resource()
    assert_shape(folder_name, resource)


if __name__ == "__main__":
    main()
