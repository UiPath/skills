#!/usr/bin/env python3
"""Scaffold a lowcode agent and inject LC_PROMPT_INSTRUCTION_CONFLICTS.

Rewrites the system message to contain two mutually exclusive output
instructions (JSON-only vs. plain-text-paragraph-never-JSON). The judgment
rule fires when a literal reading of the prompt produces contradictory
behaviour — something a regex cannot decide, so it lives in the skill.
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
CONFLICT = (
    "You are a support ticket classifier. ALWAYS respond with ONLY a single "
    "JSON object and nothing else before or after it. ALSO, always write your "
    "answer as a warm, friendly plain-text paragraph and never use JSON or any "
    "structured format."
)


def _patch(agent_json: Path) -> None:
    data = json.loads(agent_json.read_text(encoding="utf-8"))
    for msg in data.get("messages", []):
        if msg.get("role") == "system":
            msg["content"] = CONFLICT
    agent_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    project = write_baseline_lowcode_agent(SOLUTION)
    _patch(project / "agent.json")
    _patch(project / ".agent-builder" / "agent.json")
    print("Injected contradictory system-prompt instructions (JSON-only vs plain-text paragraph)")


if __name__ == "__main__":
    main()
