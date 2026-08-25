#!/usr/bin/env python3
"""Conversational agent scaffold check.

Verifies the conversational essentials produced by `uip agent init
--conversational` survive scaffold + validate. The CLI's `--conversational`
flag emits the canonical shape; this check confirms the agent didn't
break the conversational-defining fields when applying any post-init
edits (model override, system prompt, etc.).

Checks:
  1. metadata.isConversational == true
  2. settings.engine == "conversational-v1"
  3. settings.maxIterations absent
  4. outputSchema.properties is empty {} (Rule 26 — never populate)
  5. messages[1] (user role) content has no {{input.*}} template, and
     contentTokens contain no `variable` entries (§ Messages)
  6. entry-points.json schemas mirror agent.json (Rule 4 sync)
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


def assert_conversational_essentials(agent: dict) -> None:
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
            f'FAIL: settings.maxIterations must be absent for conversational '
            f'(CLI omits it; conversational has no iteration cap), '
            f'got {settings.get("maxIterations")!r}'
        )
    print("OK: settings.maxIterations absent")

    output_props = (agent.get("outputSchema") or {}).get("properties") or {}
    if output_props:
        sys.exit(
            f"FAIL: outputSchema.properties must be empty for conversational (Rule 26), "
            f"got keys: {list(output_props)}"
        )
    print("OK: outputSchema.properties empty (Rule 26)")


def assert_static_user_message(agent: dict) -> None:
    messages = agent.get("messages", [])
    user_msg = next((m for m in messages if m.get("role") == "user"), None)
    if user_msg is None:
        sys.exit("FAIL: no user-role message found in messages[]")

    content = user_msg.get("content", "")
    if "{{input" in content:
        sys.exit(
            f"FAIL: messages user content must not contain {{input.*}} template for conversational — got {content!r}"
        )

    tokens = user_msg.get("contentTokens", [])
    for i, token in enumerate(tokens):
        if token.get("type") == "variable":
            sys.exit(
                f'FAIL: messages user contentTokens[{i}] must not be type "variable" for conversational — got {token!r}'
            )
    print(
        f"OK: messages[1] (user) has no {{input}} template and no variable contentTokens "
        f"({len(tokens)} token(s))"
    )


def assert_schema_sync(agent: dict, entry: dict) -> None:
    entry_points = entry.get("entryPoints", [])
    if not entry_points:
        sys.exit("FAIL: entry-points.json missing entryPoints[]")

    ep = entry_points[0]
    agent_in = agent.get("inputSchema") or {}
    agent_out = agent.get("outputSchema") or {}
    ep_in = ep.get("input") or {}
    ep_out = ep.get("output") or {}

    if (agent_in.get("properties") or {}) != (ep_in.get("properties") or {}):
        sys.exit(
            "FAIL: agent.json inputSchema.properties != entry-points.json entryPoints[0].input.properties"
        )
    if (agent_in.get("required") or []) != (ep_in.get("required") or []):
        sys.exit(
            "FAIL: agent.json inputSchema.required != entry-points.json entryPoints[0].input.required"
        )
    if (agent_out.get("properties") or {}) != (ep_out.get("properties") or {}):
        sys.exit(
            "FAIL: agent.json outputSchema.properties != entry-points.json entryPoints[0].output.properties"
        )
    print("OK: agent.json schemas match entry-points.json (Rule 4 sync)")


def main() -> None:
    agent = load(AGENT)
    assert_conversational_essentials(agent)
    assert_static_user_message(agent)

    if ENTRY.is_file():
        entry = load(ENTRY)
        assert_schema_sync(agent, entry)
    else:
        print("OK: entry-points.json not present — skipping sync check")

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
