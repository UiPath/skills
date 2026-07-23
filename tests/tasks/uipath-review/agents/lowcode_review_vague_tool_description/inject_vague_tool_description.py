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
BASE = Path("ReviewSol/SampleAgent/resources/VagueTool")
TOOL_NAME = "vague_tool"


def main() -> None:
    write_baseline_lowcode_agent(SOLUTION)
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
