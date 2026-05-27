#!/usr/bin/env python3
"""Inject VAGUE_TOOL_DESCRIPTION violation: create a tool resource.json
with an empty `description`. The catalog rule fires when description
is missing, empty after strip, or shorter than MIN_TOOL_DESC_LEN.
"""

import json
from pathlib import Path

BASE = Path("ReviewSol/SampleAgent/resources/VagueTool")
TOOL_NAME = "vague_tool"


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    resource = {
        "$resourceType": "tool",
        "type": "external",
        "id": "cccccccc-cccc-4ccc-cccc-cccccccccccc",
        "name": TOOL_NAME,
        "description": "",
        "isEnabled": True,
        "properties": {},
    }
    (BASE / "resource.json").write_text(json.dumps(resource, indent=2))
    print(f"Injected tool {TOOL_NAME!r} with empty description")


if __name__ == "__main__":
    main()
