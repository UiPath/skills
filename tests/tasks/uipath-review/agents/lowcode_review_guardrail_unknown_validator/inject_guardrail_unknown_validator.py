#!/usr/bin/env python3
"""Scaffold a lowcode agent and inject a built-in guardrail with a bogus validator.

Adds a `$guardrailType: "builtInValidator"` guardrail whose `validatorType` is a
made-up name not in any tenant's guardrail catalog. `uip agent review` (Step 2.5a)
fetches the live catalog (`uip agent guardrails list`) and must emit
GUARDRAIL_UNKNOWN_VALIDATOR. A deliberately bogus name (rather than a real
validator) makes the finding fire for *any* authed tenant, independent of which
validators that tenant actually exposes.
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

GUARDRAIL = {
    "$guardrailType": "builtInValidator",
    "id": "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb",
    "name": "Made-up validator guardrail",
    "description": "References a validator that is not in the catalog.",
    "validatorType": "totally_made_up_validator",
    "validatorParameters": [],
    "action": {"$actionType": "block", "reason": "test"},
    "enabledForEvals": True,
    "selector": {"scopes": ["Agent"]},
}


def _patch_agent(agent_json: Path) -> None:
    data = json.loads(agent_json.read_text(encoding="utf-8"))
    data["guardrails"] = [json.loads(json.dumps(GUARDRAIL))]
    agent_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    project = write_baseline_lowcode_agent(SOLUTION)
    _patch_agent(project / "agent.json")
    _patch_agent(project / ".agent-builder" / "agent.json")
    print("Injected built-in guardrail with a bogus validatorType")


if __name__ == "__main__":
    main()
