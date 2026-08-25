#!/usr/bin/env python3
"""Scaffold a lowcode agent and set up the audit-logging flavor of
LC_GUARDRAIL_RECOMMENDED.

The agent has a `SendCustomerEmail` tool whose required argument is the
recipient email (the tool legitimately handles PII) and configures NO
guardrails. Blocking PII on this tool would break it, so the right
recommendation is a Tool-scope **log** guardrail for an audit trail (not
block). The reviewer should emit `LC_GUARDRAIL_RECOMMENDED` naming the tool and
recommending a log/audit action.
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
from lowcode_scaffold import (  # noqa: E402
    connection_binding,
    set_message,
    write_baseline_lowcode_agent,
    write_bindings,
)

SOLUTION = Path("ReviewSol")
TOOL_NAME = "SendCustomerEmail"
TOOL_DESCRIPTION = (
    "Sends an email to a customer. Requires the recipient's email address "
    "and the message body. Use after drafting the reply to deliver it."
)
CONNECTION_ID = "88888888-8888-4888-8888-888888888888"
FOLDER_KEY = "99999999-9999-4999-8999-999999999999"

# Schema-valid integration tool wiring: `uip agent validate` parses each
# resource through the storage-schema Zod union, which requires the full
# connector wiring (properties.method/connection/parameters/bodyStructure,
# iconUrl, argumentProperties). A bare tool stub fails with
# "resource.json: Invalid input" — fixture noise that distracts the reviewer
# from the intended missing-guardrail signal.
TOOL_RESOURCE = {
    "$resourceType": "tool",
    "id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
    "type": "integration",
    "location": "external",
    "name": TOOL_NAME,
    "description": TOOL_DESCRIPTION,
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
    "iconUrl": "",
    "settings": {},
    "guardrail": {"policies": []},
    "argumentProperties": {},
    "properties": {
        "toolPath": "/hubs/productivity/send-mail-v2",
        "objectName": "send-mail-v2",
        "toolDisplayName": TOOL_NAME,
        "toolDescription": TOOL_DESCRIPTION,
        "method": "POST",
        "bodyStructure": {"contentType": "json"},
        "connection": {
            "id": CONNECTION_ID,
            "name": "review-fixture-outlook",
            "elementInstanceId": 0,
            "apiBaseUri": "",
            "state": "enabled",
            "isDefault": False,
            "connector": {
                "key": "uipath-microsoft-outlook365",
                "name": "Microsoft Outlook 365",
                "image": "",
                "enabled": True,
                "isPreview": False,
            },
            "folder": {"key": FOLDER_KEY, "path": FOLDER_KEY},
            "solutionProperties": {"resourceKey": CONNECTION_ID},
        },
        "parameters": [],
    },
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
    data.pop("guardrails", None)
    set_message(data, "user", USER_MSG)
    agent_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    project = write_baseline_lowcode_agent(SOLUTION)
    _write_tool_resource(project)
    _patch_agent(project / "agent.json")
    _patch_agent(project / ".agent-builder" / "agent.json")
    write_bindings(project, [connection_binding(CONNECTION_ID, "uipath-microsoft-outlook365")])
    print("Injected SendCustomerEmail tool (handles PII) with no guardrail")


if __name__ == "__main__":
    main()
