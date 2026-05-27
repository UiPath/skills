#!/usr/bin/env python3
"""Inject DUPLICATE_TOOL_NAMES violation: create two resource.json files
that share the same `name` field. Runtime uses tool name as a unique
handle; duplicates collide.
"""

import json
import os
from pathlib import Path

BASE = Path("ReviewSol/SampleAgent/resources")
SHARED_NAME = "duplicated_handle"

TOOLS = [
    ("ToolA", "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa"),
    ("ToolB", "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"),
]


def make_resource(uid: str) -> dict:
    return {
        "$resourceType": "tool",
        "type": "external",
        "id": uid,
        "name": SHARED_NAME,
        "description": (
            "Test fixture: two tools share this name to trigger "
            "DUPLICATE_TOOL_NAMES."
        ),
        "isEnabled": True,
        "properties": {},
    }


def main() -> None:
    for dir_name, uid in TOOLS:
        d = BASE / dir_name
        d.mkdir(parents=True, exist_ok=True)
        resource_path = d / "resource.json"
        resource_path.write_text(json.dumps(make_resource(uid), indent=2))
    print(f"Injected {len(TOOLS)} tools sharing name={SHARED_NAME!r}")


if __name__ == "__main__":
    main()
