#!/usr/bin/env python3
"""Scaffold a lowcode agent and inject LC_GUARDRAIL_PII_MISSING.

Rewrites the input schema so the agent clearly processes personal data
(customer_email, full_name, ssn) and leaves the guardrails array absent.
The judgment rule fires when the agent processes personal data (inferred
from field names/descriptions) but has no pii_detection guardrail — an
inference a regex cannot make reliably.
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
PII_SCHEMA = {
    "type": "object",
    "properties": {
        "customer_email": {"type": "string", "description": "The customer's email address"},
        "full_name": {"type": "string", "description": "The customer's full legal name"},
        "ssn": {"type": "string", "description": "The customer's social security number"},
    },
    "required": ["customer_email", "full_name", "ssn"],
}
USER_MSG = (
    "Customer {{input.full_name}} <{{input.customer_email}}> (SSN {{input.ssn}}). "
    "Handle their support request."
)


def _patch_agent(agent_json: Path) -> None:
    data = json.loads(agent_json.read_text(encoding="utf-8"))
    data["inputSchema"] = PII_SCHEMA
    for msg in data.get("messages", []):
        if msg.get("role") == "user":
            msg["content"] = USER_MSG
    data.pop("guardrails", None)
    agent_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _patch_entry_points(ep_json: Path) -> None:
    data = json.loads(ep_json.read_text(encoding="utf-8"))
    data["entryPoints"][0]["input"] = PII_SCHEMA
    ep_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    project = write_baseline_lowcode_agent(SOLUTION)
    _patch_agent(project / "agent.json")
    _patch_agent(project / ".agent-builder" / "agent.json")
    _patch_entry_points(project / "entry-points.json")
    _patch_entry_points(project / ".agent-builder" / "entry-points.json")
    print("Injected PII input schema (customer_email/full_name/ssn) with no PII guardrail")


if __name__ == "__main__":
    main()
