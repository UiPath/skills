#!/usr/bin/env python3
"""Conversational agent scaffold check.

Validates the PROD-canonical conversational `agent.json` shape per
`skills/uipath-agents/references/lowcode/agent-definition.md` § Conversational
Variant and Critical Rules 22-26.

Checks:
  1. metadata.isConversational == true (Rule 22)
  2. settings.engine == "conversational-v1" (Rule 22)
  3. settings.maxIterations is absent (omitted for conversational; Rule 25)
  4. metadata.targetRuntime is absent (PROD omits; Rule 25)
  5. inputSchema.properties is empty {} (Rule 24)
  6. inputSchema.required is absent or empty (Rule 24)
  7. outputSchema.properties is empty {} (PROD canonical — Rule 24)
  8. messages[1] (user role) content has no {{input.*}} template (Rule 23)
  9. messages[1].contentTokens contain no "variable" entries (Rule 23)
  10. entry-points.json schemas mirror agent.json — both empty (Rule 4 sync)
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "ChatSol" / "ChatAgent"
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def assert_conversational_shape(agent: dict) -> None:
    metadata = agent.get("metadata", {})
    settings = agent.get("settings", {})

    if metadata.get("isConversational") is not True:
        sys.exit(
            f'FAIL: metadata.isConversational must be true, got {metadata.get("isConversational")!r}'
        )
    print("OK: metadata.isConversational == true")

    if settings.get("engine") != "conversational-v1":
        sys.exit(
            f'FAIL: settings.engine must be "conversational-v1", got {settings.get("engine")!r}'
        )
    print('OK: settings.engine == "conversational-v1"')

    if "maxIterations" in settings:
        sys.exit(
            f'FAIL: settings.maxIterations must be omitted for conversational, got {settings.get("maxIterations")!r}'
        )
    print("OK: settings.maxIterations omitted")

    if "targetRuntime" in metadata:
        sys.exit(
            f'FAIL: metadata.targetRuntime must be omitted for PROD conversational, got {metadata.get("targetRuntime")!r}'
        )
    print("OK: metadata.targetRuntime omitted (PROD canonical)")

    input_schema = agent.get("inputSchema", {})
    input_props = input_schema.get("properties", {})
    if input_props:
        sys.exit(
            f"FAIL: inputSchema.properties must be empty for conversational, got keys: {list(input_props.keys())}"
        )
    required = input_schema.get("required", [])
    if required:
        sys.exit(
            f"FAIL: inputSchema.required must be empty or omitted for conversational, got {required}"
        )
    print("OK: inputSchema empty (no properties, no required)")

    output_schema = agent.get("outputSchema", {})
    output_props = output_schema.get("properties", {})
    if output_props:
        sys.exit(
            f"FAIL: outputSchema.properties must be empty (PROD canonical), got keys: {list(output_props.keys())}"
        )
    print("OK: outputSchema empty (PROD canonical)")


def assert_static_user_message(agent: dict) -> None:
    messages = agent.get("messages", [])
    user_msg = next((m for m in messages if m.get("role") == "user"), None)
    if user_msg is None:
        sys.exit("FAIL: no user-role message found in messages[]")

    content = user_msg.get("content", "")
    if "{{input" in content:
        sys.exit(
            f"FAIL: messages user content must be a static placeholder, not a variable template — got {content!r}"
        )

    tokens = user_msg.get("contentTokens", [])
    if not tokens:
        sys.exit("FAIL: messages user contentTokens must be non-empty")
    for i, token in enumerate(tokens):
        if token.get("type") == "variable":
            sys.exit(
                f'FAIL: messages user contentTokens[{i}] must not be type "variable" for conversational — got {token!r}'
            )
    print("OK: user message is static (no {{input}} template); contentTokens are simpleText")


def assert_schema_sync(agent: dict, entry: dict) -> None:
    entry_points = entry.get("entryPoints", [])
    if not entry_points:
        sys.exit("FAIL: entry-points.json missing entryPoints[]")

    ep = entry_points[0]
    ep_input = ep.get("input", {})
    ep_output = ep.get("output", {})

    if ep_input.get("properties"):
        sys.exit(
            f"FAIL: entry-points.json input.properties must be empty, got keys: {list(ep_input.get('properties', {}).keys())}"
        )
    if ep_input.get("required"):
        sys.exit(
            f"FAIL: entry-points.json input.required must be empty, got {ep_input.get('required')}"
        )
    if ep_output.get("properties"):
        sys.exit(
            f"FAIL: entry-points.json output.properties must be empty, got keys: {list(ep_output.get('properties', {}).keys())}"
        )
    print("OK: entry-points.json schemas mirror agent.json (Rule 4 sync)")


def main() -> None:
    agent = load(AGENT)
    assert_conversational_shape(agent)
    assert_static_user_message(agent)

    if ENTRY.is_file():
        entry = load(ENTRY)
        assert_schema_sync(agent, entry)
    else:
        print("OK: entry-points.json not present — skipping sync check")

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
