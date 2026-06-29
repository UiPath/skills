#!/usr/bin/env python3
"""Scaffold a lowcode agent and inject LC_GUARDRAIL_MISAPPLIED.

The agent is a synthetic-test-data generator: it takes a non-PII `topic` and
produces fake sample records. Its LLM never receives real personal data. It
carries a `pii_detection` guardrail at **Llm** scope — format-valid, but the
live catalog's `when_not_to_use` says *"Do not apply at Llm scope if the agent's
LLM never receives raw PII from the user."* So the guardrail is misapplied.

`uip agent review` returns it clean (format-valid), so the only signal is the
judgment rule, reached by reading the catalog.
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
        "topic": {"type": "string", "description": "The theme to generate fake sample records for"},
    },
    "required": ["topic"],
}
SYSTEM_MSG = (
    "You are a synthetic test-data generator. Given a theme, you invent fake "
    "sample records for testing. You never receive or process real customer "
    "data — every value you emit is made up."
)
USER_MSG = "Generate fake sample records for: {{input.topic}}"

# pii_detection at Llm scope on an agent whose LLM never sees real PII —
# misapplied per the catalog's when_not_to_use.
GUARDRAIL = {
    "$guardrailType": "builtInValidator",
    "id": "99999999-9999-4999-9999-999999999999",
    "name": "PII block at Llm",
    "description": "Blocks PII reaching the LLM.",
    "validatorType": "pii_detection",
    "validatorParameters": [
        {"$parameterType": "enum-list", "id": "entities", "value": ["Email", "Person"]},
        {"$parameterType": "map-enum", "id": "entityThresholds", "value": {"Email": 0.5, "Person": 0.5}},
    ],
    "action": {"$actionType": "block", "reason": "PII detected — blocked."},
    "enabledForEvals": True,
    "selector": {"scopes": ["Llm"]},
}


def _patch_agent(agent_json: Path) -> None:
    data = json.loads(agent_json.read_text(encoding="utf-8"))
    data["inputSchema"] = json.loads(json.dumps(INPUT_SCHEMA))
    data["guardrails"] = [json.loads(json.dumps(GUARDRAIL))]
    for msg in data.get("messages", []):
        if msg.get("role") == "system":
            msg["content"] = SYSTEM_MSG
        elif msg.get("role") == "user":
            msg["content"] = USER_MSG
    agent_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _patch_entry_points(ep_json: Path) -> None:
    data = json.loads(ep_json.read_text(encoding="utf-8"))
    data["entryPoints"][0]["input"] = json.loads(json.dumps(INPUT_SCHEMA))
    ep_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    project = write_baseline_lowcode_agent(SOLUTION)
    _patch_agent(project / "agent.json")
    _patch_agent(project / ".agent-builder" / "agent.json")
    _patch_entry_points(project / "entry-points.json")
    _patch_entry_points(project / ".agent-builder" / "entry-points.json")
    print("Injected generate-only agent with a misapplied Llm-scope pii_detection guardrail")


if __name__ == "__main__":
    main()
