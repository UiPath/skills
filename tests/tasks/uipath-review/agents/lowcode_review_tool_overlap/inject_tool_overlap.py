#!/usr/bin/env python3
"""Scaffold a lowcode agent and inject LC_TOOL_OVERLAP.

Writes two tool resources whose descriptions a user could plausibly apply
to the same request (both "look up a customer by email and return their
profile"). The judgment rule fires when two tools are interchangeable
enough that the LLM would be unable to choose between them — a semantic
read, not a string match.
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
TOOLS = [
    (
        "lookup_customer",
        "cccccccc-cccc-4ccc-8ccc-ccccccccccc0",
        "dddddddd-dddd-4ddd-8ddd-ddddddddddd0",
        "Look up a customer by their email address and return the customer's profile details.",
    ),
    (
        "find_customer",
        "cccccccc-cccc-4ccc-8ccc-ccccccccccc1",
        "dddddddd-dddd-4ddd-8ddd-ddddddddddd1",
        "Find a customer using their email and return the customer's profile information.",
    ),
]


def main() -> None:
    project = write_baseline_lowcode_agent(SOLUTION)
    for name, rid, reference_key, desc in TOOLS:
        d = project / "resources" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "resource.json").write_text(
            json.dumps(
                {
                    "$resourceType": "tool",
                    "id": rid,
                    "type": "process",
                    "location": "external",
                    "name": name,
                    "description": desc,
                    "isEnabled": True,
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Customer email address",
                            },
                        },
                        "required": ["email"],
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "profile": {
                                "type": "string",
                                "description": "Customer profile details",
                            },
                        },
                    },
                    "settings": {},
                    "guardrail": {"policies": []},
                    "properties": {
                        "processName": name,
                        "folderPath": "Shared",
                        "exampleCalls": [],
                    },
                    "referenceKey": reference_key,
                    "argumentProperties": {},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    print("Injected two overlapping tools: lookup_customer / find_customer")


if __name__ == "__main__":
    main()
