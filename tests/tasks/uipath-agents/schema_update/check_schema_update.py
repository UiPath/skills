#!/usr/bin/env python3
"""Schema update check.

Asserts:
  1. agent.json.inputSchema  == entry-points.json entryPoints[0].input
     agent.json.outputSchema == entry-points.json entryPoints[0].output
     (Critical Rule 4 — schema sync.)
  2. The input schema matches the prompt spec — an "object" with a
     required string field named `userQuery`.
  3. The output schema matches the prompt spec — an "object" with a
     string field named `reply`.
  4. The agent's user message template inlines the input variable:
     `content` includes `{{input.userQuery}}` and `contentTokens`
     contains a matching `{"type":"variable","rawString":"input.userQuery"}`
     entry (Critical Rules 5 and 6).
"""

import json
import os
import sys
from pathlib import Path

AGENT = Path(os.getcwd()) / "QuerySol" / "QueryAgent" / "agent.json"
ENTRY = Path(os.getcwd()) / "QuerySol" / "QueryAgent" / "entry-points.json"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def assert_input_shape(schema: dict, label: str) -> None:
    if not isinstance(schema, dict):
        sys.exit(f"FAIL: {label} is not an object: {schema!r}")
    if schema.get("type") != "object":
        sys.exit(f"FAIL: {label}.type should be 'object', got {schema.get('type')!r}")
    props = schema.get("properties")
    if not isinstance(props, dict) or "userQuery" not in props:
        sys.exit(f"FAIL: {label}.properties missing 'userQuery': got {list(props) if isinstance(props, dict) else props!r}")
    uq = props["userQuery"]
    if not isinstance(uq, dict) or uq.get("type") != "string":
        sys.exit(f"FAIL: {label}.properties.userQuery.type should be 'string', got {uq!r}")
    required = schema.get("required")
    if not isinstance(required, list) or "userQuery" not in required:
        sys.exit(f"FAIL: {label}.required must contain 'userQuery', got {required!r}")
    print(f"OK: {label} declares required userQuery:string (matches prompt)")


def assert_output_shape(schema: dict, label: str) -> None:
    if not isinstance(schema, dict):
        sys.exit(f"FAIL: {label} is not an object: {schema!r}")
    if schema.get("type") != "object":
        sys.exit(f"FAIL: {label}.type should be 'object', got {schema.get('type')!r}")
    props = schema.get("properties")
    if not isinstance(props, dict) or "reply" not in props:
        sys.exit(f"FAIL: {label}.properties missing 'reply': got {list(props) if isinstance(props, dict) else props!r}")
    reply = props["reply"]
    if not isinstance(reply, dict) or reply.get("type") != "string":
        sys.exit(f"FAIL: {label}.properties.reply.type should be 'string', got {reply!r}")
    print(f"OK: {label} declares reply:string (matches prompt)")


def assert_user_message_inlines_variable(agent: dict, field: str) -> None:
    messages = agent.get("messages")
    if not isinstance(messages, list):
        sys.exit(f"FAIL: agent.json.messages is not a list: {messages!r}")
    user_messages = [m for m in messages if isinstance(m, dict) and m.get("role") == "user"]
    if not user_messages:
        sys.exit("FAIL: agent.json.messages has no entry with role == 'user'")
    user = user_messages[0]

    placeholder = "{{input." + field + "}}"
    content = user.get("content", "")
    if placeholder not in content:
        sys.exit(f"FAIL: user message content does not inline {placeholder}: content={content!r}")

    tokens = user.get("contentTokens")
    if not isinstance(tokens, list):
        sys.exit(f"FAIL: user message contentTokens is not a list: {tokens!r}")
    expected = {"type": "variable", "rawString": f"input.{field}"}
    if expected not in tokens:
        sys.exit(
            f"FAIL: user message contentTokens missing variable token for input.{field}\n"
            f"  expected token: {expected}\n"
            f"  got tokens:     {json.dumps(tokens, indent=2)}"
        )
    print(f"OK: user message inlines {placeholder} with a matching variable contentToken")


def main():
    agent = load(AGENT)
    entry = load(ENTRY)

    entry_points = entry.get("entryPoints")
    if not isinstance(entry_points, list) or not entry_points:
        sys.exit("FAIL: entry-points.json has no entryPoints[0]")
    ep = entry_points[0]

    agent_in = agent.get("inputSchema")
    entry_in = ep.get("input")
    if agent_in != entry_in:
        sys.exit(
            "FAIL: agent.json.inputSchema != entry-points.json entryPoints[0].input\n"
            f"  agent.json.inputSchema:\n{json.dumps(agent_in, sort_keys=True, indent=2)}\n"
            f"  entry-points.input:\n{json.dumps(entry_in, sort_keys=True, indent=2)}"
        )
    print("OK: inputSchema identical in agent.json and entry-points.json")

    agent_out = agent.get("outputSchema")
    entry_out = ep.get("output")
    if agent_out != entry_out:
        sys.exit(
            "FAIL: agent.json.outputSchema != entry-points.json entryPoints[0].output\n"
            f"  agent.json.outputSchema:\n{json.dumps(agent_out, sort_keys=True, indent=2)}\n"
            f"  entry-points.output:\n{json.dumps(entry_out, sort_keys=True, indent=2)}"
        )
    print("OK: outputSchema identical in agent.json and entry-points.json")

    assert_input_shape(agent_in, "agent.json.inputSchema")
    assert_output_shape(agent_out, "agent.json.outputSchema")
    assert_user_message_inlines_variable(agent, "userQuery")


if __name__ == "__main__":
    main()
