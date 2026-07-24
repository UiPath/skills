#!/usr/bin/env python3
"""Attachments context resource check.

Validates that the agent authored a runtime-attachments context resource
per references/lowcode/capabilities/context/attachments.md:

  1. A resource under resources/<folder>/resource.json declares:
       - $resourceType == "context"
       - contextType   == "attachments"   (lowercase — Anti-pattern 12)
       - name == its folder name (convention: folder matches `name`)
  2. The resource carries an `attachments` object (runtime file context).
  3. settings.retrievalMode, when present, is a documented value.

Attachments are runtime-only: NO solution-level file and NO index binding
are produced, so this check intentionally does not assert on
bindings_v2.json.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "AttachSol" / "DocReviewAgent"
RESOURCES = ROOT / "resources"

# Documented retrievalMode values (see context/index.md). Accept both the
# lowercase forms from the docs and the camelCase the index check tolerates.
VALID_RETRIEVAL_MODES = {
    "semantic",
    "structured",
    "deeprag",
    "batchtransform",
    "deepRAG",
    "batchTransform",
}


def find_attachments_resource() -> tuple[str, dict]:
    if not RESOURCES.is_dir():
        sys.exit(f"FAIL: {RESOURCES} does not exist — no context resource authored")
    seen = []
    for path in sorted(RESOURCES.rglob("resource.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        seen.append((data.get("$resourceType"), data.get("contextType")))
        if data.get("$resourceType") == "context" and data.get("contextType") == "attachments":
            print(f"OK: found attachments context resource at {path.relative_to(ROOT.parent)}")
            return path.parent.name, data
    sys.exit(
        'FAIL: no context resource with $resourceType=="context" and '
        f'contextType=="attachments" found under {RESOURCES}. Seen '
        f'($resourceType, contextType): {seen}'
    )


def assert_shape(folder_name: str, resource: dict) -> None:
    ctype = resource.get("contextType")
    if ctype != "attachments":
        sys.exit(
            f'FAIL: contextType must be exactly "attachments" (lowercase), got {ctype!r}'
        )
    name = resource.get("name")
    if name != folder_name:
        sys.exit(
            f"FAIL: resource.json name {name!r} must match its folder name "
            f"{folder_name!r} (convention: folder matches `name`)"
        )
    attachments = resource.get("attachments")
    if not isinstance(attachments, dict):
        sys.exit(
            "FAIL: attachments context must carry an `attachments` object "
            f"(runtime file context); got {attachments!r}"
        )
    print(f'OK: contextType="attachments", name=folder={name!r}, attachments object present')

    settings = resource.get("settings")
    if isinstance(settings, dict) and "retrievalMode" in settings:
        mode = settings.get("retrievalMode")
        if mode not in VALID_RETRIEVAL_MODES:
            sys.exit(
                f"FAIL: settings.retrievalMode {mode!r} is not a documented value "
                f"{sorted(VALID_RETRIEVAL_MODES)}"
            )
        print(f"OK: settings.retrievalMode is {mode!r}")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: agent directory {ROOT} does not exist")
    folder_name, resource = find_attachments_resource()
    assert_shape(folder_name, resource)


if __name__ == "__main__":
    main()
