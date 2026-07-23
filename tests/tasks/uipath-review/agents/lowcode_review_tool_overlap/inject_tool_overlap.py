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
PROJECT = SOLUTION / "SampleAgent"
TOOLS = [
    (
        "LookupCustomer",
        "lookup_customer",
        "cccccccc-cccc-4ccc-cccc-ccccccccccc0",
        "Look up a customer by their email address and return the customer's profile details.",
    ),
    (
        "FindCustomer",
        "find_customer",
        "cccccccc-cccc-4ccc-cccc-ccccccccccc1",
        "Find a customer using their email and return the customer's profile information.",
    ),
]


def main() -> None:
    write_baseline_lowcode_agent(SOLUTION)
    for folder, name, rid, desc in TOOLS:
        d = PROJECT / "resources" / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / "resource.json").write_text(
            json.dumps(
                {
                    "$resourceType": "tool",
                    "type": "external",
                    "id": rid,
                    "name": name,
                    "description": desc,
                    "isEnabled": True,
                    "properties": {},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    print("Injected two overlapping tools: lookup_customer / find_customer")


if __name__ == "__main__":
    main()
