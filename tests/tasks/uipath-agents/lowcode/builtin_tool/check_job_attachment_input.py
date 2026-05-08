#!/usr/bin/env python3
"""Job-attachment input contract check.

The prompt asks for an agent that analyzes "PDF and image attachments"
via the "Analyze Files" built-in tool. That tool is fed by an attachment
input on the agent — without it the tool has nothing to read.

Validates that DocAnalystAgent/agent.json declares:

  - inputSchema.definitions["job-attachment"] — an object schema
  - At least one inputSchema.properties.<name> whose schema is
    {"$ref": "#/definitions/job-attachment"}
  - At least one of those input names is referenced from a
    messages[].content string as `{{input.<name>}}` (otherwise the
    attachment is declared but never passed to the model).
"""

import json
import os
import re
import sys
from pathlib import Path

AGENT_JSON = Path(os.getcwd()) / "DocsSol" / "DocAnalystAgent" / "agent.json"
JOB_ATTACHMENT_REF = "#/definitions/job-attachment"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def main() -> None:
    agent = load(AGENT_JSON)
    schema = agent.get("inputSchema") or {}

    defs = schema.get("definitions") or {}
    ja_def = defs.get("job-attachment")
    if not isinstance(ja_def, dict):
        sys.exit(
            'FAIL: agent.json inputSchema.definitions["job-attachment"] is missing. '
            "Define a job-attachment schema so the agent can accept file inputs "
            "for the Analyze Files tool."
        )
    if ja_def.get("type") != "object":
        sys.exit(
            'FAIL: inputSchema.definitions["job-attachment"] must be an object '
            f'schema, got type={ja_def.get("type")!r}'
        )
    print('OK: inputSchema.definitions["job-attachment"] is defined')

    props = schema.get("properties") or {}
    refs = [
        name
        for name, prop in props.items()
        if isinstance(prop, dict) and prop.get("$ref") == JOB_ATTACHMENT_REF
    ]
    if not refs:
        sys.exit(
            f'FAIL: no inputSchema property uses $ref="{JOB_ATTACHMENT_REF}". '
            "The agent has no file input — the Analyze Files tool would have "
            "nothing to analyze."
        )
    print(f"OK: input properties typed as job-attachment: {refs}")

    messages = agent.get("messages") or []
    bodies = [m.get("content", "") for m in messages if isinstance(m, dict)]
    missing = []
    for name in refs:
        # Match {{ input.<name> }} with any internal whitespace.
        pattern = re.compile(
            r"\{\{\s*input\." + re.escape(name) + r"\s*\}\}"
        )
        if not any(pattern.search(body) for body in bodies):
            missing.append(name)
    if missing:
        sys.exit(
            f"FAIL: job-attachment input(s) {missing} are declared but "
            "never referenced as {{input.<name>}} in any message content. "
            "Every attachment input must be wired into a prompt or the "
            "model never sees it."
        )
    print(f"OK: all job-attachment inputs are referenced in messages: {refs}")


if __name__ == "__main__":
    main()
