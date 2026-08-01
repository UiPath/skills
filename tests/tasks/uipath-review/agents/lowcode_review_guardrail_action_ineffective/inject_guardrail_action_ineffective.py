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
from lowcode_scaffold import (  # noqa: E402
    connection_binding,
    set_message,
    write_baseline_lowcode_agent,
    write_bindings,
)

SOLUTION = Path("ReviewSol")
TOOL_NAME = "SendCustomerEmail"
CONNECTION_ID = "99999999-9999-4999-8999-999999999999"
FOLDER_KEY = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
CONNECTOR_KEY = "uipath-microsoft-outlook365"
ICON_URL = (
    "https://alpha.uipath.com/elements_/scaleunit_/"
    "3854d037-4ab5-4881-909b-968c433f6d88/v3/element/elements/"
    f"{CONNECTOR_KEY}/image"
)
TOOL_DESCRIPTION = (
    "Sends an email to a customer. Requires the recipient's email address "
    "and the message body. Use after drafting the reply to deliver it."
)

TOOL_RESOURCE = {
    "$resourceType": "tool",
    "id": "77777777-7777-4777-7777-777777777777",
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
                "title": "Recipient email",
                "description": "The customer's email address to send the message to",
            },
            "body": {
                "type": "string",
                "title": "Body",
                "description": "The email body",
            },
        },
        "additionalProperties": False,
        "required": ["recipient_email", "body"],
    },
    "outputSchema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "sent": {
                "type": "boolean",
                "title": "Sent",
                "description": "Whether the email was sent",
            }
        },
    },
    "iconUrl": ICON_URL,
    "settings": {},
    "guardrail": {"policies": []},
    "isPreview": False,
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
                "key": CONNECTOR_KEY,
                "name": "Microsoft Outlook 365",
                "image": ICON_URL,
                "enabled": True,
                "isPreview": False,
            },
            "folder": {"key": FOLDER_KEY, "path": FOLDER_KEY},
            "solutionProperties": {"resourceKey": CONNECTION_ID},
        },
        "parameters": [
            {
                "name": "recipient_email",
                "displayName": "Recipient email",
                "type": "string",
                "fieldLocation": "body",
                "value": "{{prompt}}",
                "description": "The customer's email address to send the message to",
                "position": "primary",
                "sortOrder": 1,
                "required": True,
                "fieldVariant": "dynamic",
                "isCascading": False,
                "dynamic": True,
                "enumValues": None,
                "loadReferenceOptionsByDefault": None,
                "dynamicBehavior": [],
                "reference": None,
            },
            {
                "name": "body",
                "displayName": "Body",
                "type": "string",
                "fieldLocation": "body",
                "value": "{{prompt}}",
                "description": "The email body",
                "position": "primary",
                "sortOrder": 2,
                "required": True,
                "fieldVariant": "dynamic",
                "isCascading": False,
                "dynamic": True,
                "enumValues": None,
                "loadReferenceOptionsByDefault": None,
                "dynamicBehavior": [],
                "reference": None,
            },
        ],
    },
}

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
    set_message(data, "user", USER_MSG)
    agent_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    project = write_baseline_lowcode_agent(SOLUTION)
    _write_tool_resource(project)
    _patch_agent(project / "agent.json")
    _patch_agent(project / ".agent-builder" / "agent.json")
    write_bindings(project, [connection_binding(CONNECTION_ID, CONNECTOR_KEY)])
    print("Injected SendCustomerEmail tool + Tool-scope pii_detection block guardrail")


if __name__ == "__main__":
    main()
