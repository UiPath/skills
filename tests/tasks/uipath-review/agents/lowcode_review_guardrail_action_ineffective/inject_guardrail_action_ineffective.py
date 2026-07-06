#!/usr/bin/env python3
"""Scaffold a lowcode agent and inject a format-VALID but semantically wrong guardrail.

Adds a `SendCustomerEmail` tool whose required argument is the recipient email
(so the tool legitimately needs PII), plus a Tool-scoped `pii_detection`
guardrail with a `block` action on that tool. Every part is format-valid — real
validator, allowed scope (`Tool`), valid params, valid action — so
`uip agent review` (Step 2.5a) returns it clean (no `GUARDRAIL_*` finding).

The defect is purely semantic and lives ONLY in the live catalog: the
`pii_detection` entry's `when_not_to_use` says *"Do not use at Tool scope with
Block or Filter action if the tool requires PII to function (e.g., a SendEmail
tool needs the recipient email address)"* — blocking PII on the email tool
breaks the tool. A naive eyeball of `agent.json` reads "PII blocking = good", so
the reviewer must fetch the catalog to flag `LC_GUARDRAIL_ACTION_INEFFECTIVE`.
This is the same un-eyeball-able property that makes the unknown_validator task
reliable single-shot.
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
TOOL_NAME = "SendCustomerEmail"

TOOL_RESOURCE = {
    "$resourceType": "tool",
    "id": "77777777-7777-4777-7777-777777777777",
    "type": "integration",
    "location": "external",
    "name": TOOL_NAME,
    "description": (
        "Sends an email to a customer. Requires the recipient's email address "
        "and the message body. Use after drafting the reply to deliver it."
    ),
    "isEnabled": True,
    "inputSchema": {
        "type": "object",
        "properties": {
            "recipient_email": {
                "type": "string",
                "description": "The customer's email address to send the message to",
            },
            "body": {"type": "string", "description": "The email body"},
        },
        "required": ["recipient_email", "body"],
    },
    "outputSchema": {
        "type": "object",
        "properties": {"sent": {"type": "boolean", "description": "Whether the email was sent"}},
    },
    "settings": {},
    # Tool resources must carry a guardrail.policies array (Studio Web rejects
    # without it); empty is valid — the guardrail itself lives in agent.json.
    "guardrail": {"policies": []},
}

# Tool-scoped pii_detection with a BLOCK action on the email tool. Format-valid;
# semantically wrong (catalog when_not_to_use: do not block PII on a tool that
# needs the PII to function).
GUARDRAIL = {
    "$guardrailType": "builtInValidator",
    "id": "88888888-8888-4888-8888-888888888888",
    "name": "PII block on SendCustomerEmail tool",
    "description": "Blocks PII on the SendCustomerEmail tool calls.",
    "validatorType": "pii_detection",
    "validatorParameters": [
        {"$parameterType": "enum-list", "id": "entities", "value": ["Email"]},
        {"$parameterType": "map-enum", "id": "entityThresholds", "value": {"Email": 0.5}},
    ],
    "action": {"$actionType": "block", "reason": "PII detected on tool call — blocked."},
    "enabledForEvals": True,
    "selector": {"scopes": ["Tool"], "matchNames": [TOOL_NAME]},
}

USER_MSG = (
    "Customer request: {{input.input}}. Draft a reply and email it to the "
    "customer using the SendCustomerEmail tool (it needs their email address)."
)


def _write_tool_resource(project: Path) -> None:
    for base in (project, project / ".agent-builder"):
        res_dir = base / "resources" / TOOL_NAME
        res_dir.mkdir(parents=True, exist_ok=True)
        (res_dir / "resource.json").write_text(
            json.dumps(TOOL_RESOURCE, indent=2), encoding="utf-8"
        )


def _patch_agent(agent_json: Path) -> None:
    data = json.loads(agent_json.read_text(encoding="utf-8"))
    data["guardrails"] = [json.loads(json.dumps(GUARDRAIL))]
    for msg in data.get("messages", []):
        if msg.get("role") == "user":
            msg["content"] = USER_MSG
    agent_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    project = write_baseline_lowcode_agent(SOLUTION)
    _write_tool_resource(project)
    _patch_agent(project / "agent.json")
    _patch_agent(project / ".agent-builder" / "agent.json")
    print("Injected SendCustomerEmail tool + Tool-scope pii_detection block guardrail")


if __name__ == "__main__":
    main()
