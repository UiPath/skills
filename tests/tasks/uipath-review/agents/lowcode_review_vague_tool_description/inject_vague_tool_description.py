#!/usr/bin/env python3
"""Scaffold a lowcode agent and inject VAGUE_TOOL_DESCRIPTION.

Creates a tool resource.json with an empty `description`. The catalog
rule fires when description is missing, empty after strip, or shorter
than MIN_TOOL_DESC_LEN.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(
    0,
    os.path.join(
        os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-review", "_shared"
    ),
)
from lowcode_scaffold import write_baseline_lowcode_agent  # noqa: E402

SOLUTION = Path("ReviewSol")
TOOL_NAME = "vague_tool"


def main() -> None:
    project = write_baseline_lowcode_agent(SOLUTION)
    base = project / "resources" / TOOL_NAME
    base.mkdir(parents=True, exist_ok=True)
    resource = {
        "$resourceType": "tool",
        "id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        "type": "process",
        "location": "external",
        "name": TOOL_NAME,
        "description": "",
        "isEnabled": True,
        "inputSchema": {
            "type": "object",
            "properties": {
                "request": {
                    "type": "string",
                    "description": "Request for the tool",
                },
            },
            "required": ["request"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "description": "Tool result",
                },
            },
        },
        "settings": {},
        "guardrail": {"policies": []},
        "properties": {
            "processName": TOOL_NAME,
            "folderPath": "Shared",
            "exampleCalls": [],
        },
        "referenceKey": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
        "argumentProperties": {},
    }
    (base / "resource.json").write_text(json.dumps(resource, indent=2))
    print(f"Injected tool {TOOL_NAME!r} with empty description")


if __name__ == "__main__":
    main()
