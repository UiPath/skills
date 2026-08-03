#!/usr/bin/env python3
"""Scaffold a lowcode agent and set up the content-safety flavor of
LC_GUARDRAIL_RECOMMENDED.

The agent is a marketing copywriter that generates open-ended promotional text
from a user-supplied topic, and configures NO guardrails. Per the catalog's
content-safety use cases, an open-ended content generator should have a
content-safety guardrail. The reviewer should emit `LC_GUARDRAIL_RECOMMENDED`
naming the content-safety case (generic phrasing — do not name a
platform-documented validator unless already present).
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

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {"type": "string", "description": "What the promotional copy is about"},
        "audience": {"type": "string", "description": "The target audience for the copy"},
    },
    "required": ["topic"],
}
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "copy": {"type": "string", "description": "The generated promotional copy"},
    },
}
SYSTEM_MSG = (
    "You are a marketing copywriter. You generate open-ended promotional blog "
    "posts and advertising copy on whatever topic the user requests."
)
USER_MSG = "Write promotional copy about {{input.topic}} for {{input.audience}}."


def _patch_agent(agent_json: Path) -> None:
    data = json.loads(agent_json.read_text(encoding="utf-8"))
    data["inputSchema"] = json.loads(json.dumps(INPUT_SCHEMA))
    data["outputSchema"] = json.loads(json.dumps(OUTPUT_SCHEMA))
    for msg in data.get("messages", []):
        if msg.get("role") == "system":
            msg["content"] = SYSTEM_MSG
        elif msg.get("role") == "user":
            msg["content"] = USER_MSG
    data.pop("guardrails", None)
    agent_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _patch_entry_points(ep_json: Path) -> None:
    data = json.loads(ep_json.read_text(encoding="utf-8"))
    data["entryPoints"][0]["input"] = json.loads(json.dumps(INPUT_SCHEMA))
    data["entryPoints"][0]["output"] = json.loads(json.dumps(OUTPUT_SCHEMA))
    ep_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    project = write_baseline_lowcode_agent(SOLUTION)
    _patch_agent(project / "agent.json")
    _patch_agent(project / ".agent-builder" / "agent.json")
    _patch_entry_points(project / "entry-points.json")
    _patch_entry_points(project / ".agent-builder" / "entry-points.json")
    print("Injected content-generating agent with no content-safety guardrail")


if __name__ == "__main__":
    main()
