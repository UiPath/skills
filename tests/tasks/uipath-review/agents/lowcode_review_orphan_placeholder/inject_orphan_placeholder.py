#!/usr/bin/env python3
"""Scaffold a lowcode agent and inject ORPHAN_PLACEHOLDER.

Adds `{{input.bogus_field}}` to a user message in agent.json where
`bogus_field` is NOT declared in inputSchema.properties. The catalog
rule fires when a placeholder references a property that does not
exist in the input schema.
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
AGENT_JSON = Path("ReviewSol/SampleAgent/agent.json")
ORPHAN_FIELD = "bogus_field"
ORPHAN_PLACEHOLDER = "{{input.bogus_field}}"


def main() -> None:
    write_baseline_lowcode_agent(SOLUTION)
    d = json.loads(AGENT_JSON.read_text())

    # Ensure messages[] exists and find or create a user message.
    messages = d.setdefault("messages", [])
    user_msg = next((m for m in messages if m.get("role") == "user"), None)
    if user_msg is None:
        user_msg = {"role": "user", "content": ""}
        messages.append(user_msg)

    existing = user_msg.get("content") or ""
    user_msg["content"] = (
        existing.rstrip()
        + "\n\nAdditional context: "
        + ORPHAN_PLACEHOLDER
    )

    # Deliberately do NOT add ORPHAN_FIELD to inputSchema.properties —
    # that is the violation.
    assert ORPHAN_FIELD not in (
        d.get("inputSchema", {}).get("properties") or {}
    ), f"Pre-condition violated: {ORPHAN_FIELD} is already in inputSchema"

    AGENT_JSON.write_text(json.dumps(d, indent=2))
    print(
        f"Injected orphan placeholder {ORPHAN_PLACEHOLDER!r} into a user "
        f"message; field {ORPHAN_FIELD!r} is NOT in inputSchema"
    )


if __name__ == "__main__":
    main()
