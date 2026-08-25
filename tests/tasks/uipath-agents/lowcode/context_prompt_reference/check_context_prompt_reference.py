#!/usr/bin/env python3
"""Context prompt-reference check.

Validates that the agent referenced an attachments context in a prompt
message (system or user) via the Studio expression syntax
`@{contexts.Knowledge}` and kept `content` and `contentTokens` aligned:

  1. The Knowledge resource is a context (`$resourceType: "context"`) with
     `contextType: "attachments"` (lowercase — Anti-pattern 12).
  2. At least one message's content contains `@{contexts.Knowledge}`.
  3. That message's contentTokens contains a matching `{type: "expression",
     rawString: "contexts.Knowledge"}` token (Critical Rule 6 — the `@{ }`
     expression family, not a `variable`).
  4. `Knowledge` is NOT declared as an inputSchema property — a context is a
     runtime-resolved resource, not an input field.
  5. inputSchema/outputSchema stay in sync with entry-points.json
     (Critical Rule 4).
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "DocSol" / "DocAssistant"
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"
RESOURCE = ROOT / "resources" / "Knowledge" / "resource.json"

CONTEXT_NAME = "Knowledge"
EXPR_RAW = f"contexts.{CONTEXT_NAME}"          # token rawString, prefix included
EXPR_LITERAL = "@{" + EXPR_RAW + "}"           # how it appears in content


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def assert_context_resource() -> None:
    res = load(RESOURCE)
    if res.get("$resourceType") != "context":
        sys.exit(
            f"FAIL: {RESOURCE} $resourceType is {res.get('$resourceType')!r}, "
            "expected 'context'"
        )
    ctype = res.get("contextType")
    if ctype != "attachments":
        sys.exit(
            f"FAIL: Knowledge contextType is {ctype!r}, expected 'attachments' "
            "(lowercase — Anti-pattern 12)"
        )
    print("OK: Knowledge is an attachments context resource")


def assert_prompt_references_context(agent: dict) -> None:
    messages = agent.get("messages")
    if not isinstance(messages, list):
        sys.exit(f"FAIL: agent.json.messages is not a list: {messages!r}")
    referencing = [
        m
        for m in messages
        if isinstance(m, dict) and EXPR_LITERAL in m.get("content", "")
    ]
    if not referencing:
        contents = {
            m.get("role"): m.get("content")
            for m in messages
            if isinstance(m, dict)
        }
        sys.exit(
            f"FAIL: no message content references {EXPR_LITERAL}: "
            f"messages={contents!r}"
        )

    expected = {"type": "expression", "rawString": EXPR_RAW}
    for msg in referencing:
        tokens = msg.get("contentTokens")
        if not isinstance(tokens, list):
            sys.exit(
                f"FAIL: {msg.get('role')} message contentTokens is not a list: "
                f"{tokens!r}"
            )
        if expected not in tokens:
            sys.exit(
                f"FAIL: {msg.get('role')} message contentTokens has no "
                f"expression token with rawString {EXPR_RAW!r} (Critical "
                "Rule 6 — context refs are `expression` tokens, not "
                f"`variable`)\n  expected: {expected}\n"
                f"  got tokens: {json.dumps(tokens, indent=2)}"
            )
    roles = ", ".join(str(m.get("role")) for m in referencing)
    print(
        "OK: prompt references @{contexts.Knowledge} with a synced "
        f"expression token (message roles: {roles})"
    )


def assert_context_not_an_input(agent: dict) -> None:
    in_schema = agent.get("inputSchema")
    props = in_schema.get("properties") if isinstance(in_schema, dict) else None
    if isinstance(props, dict) and CONTEXT_NAME in props:
        sys.exit(
            f"FAIL: inputSchema.properties declares {CONTEXT_NAME!r} — a context "
            "is a runtime-resolved resource, not an inputSchema field"
        )
    print("OK: Knowledge is not declared as an inputSchema field")


def assert_schema_sync(agent: dict, entry: dict) -> None:
    entry_points = entry.get("entryPoints")
    if not isinstance(entry_points, list) or not entry_points:
        sys.exit("FAIL: entry-points.json has no entryPoints[0]")
    ep = entry_points[0]
    if agent.get("inputSchema") != ep.get("input"):
        sys.exit(
            "FAIL: agent.json.inputSchema != entry-points.json entryPoints[0].input "
            "(Critical Rule 4)"
        )
    if agent.get("outputSchema") != ep.get("output"):
        sys.exit(
            "FAIL: agent.json.outputSchema != entry-points.json entryPoints[0].output "
            "(Critical Rule 4)"
        )
    print("OK: inputSchema and outputSchema are in sync with entry-points.json")


def main() -> None:
    agent = load(AGENT)
    entry = load(ENTRY)
    assert_context_resource()
    assert_prompt_references_context(agent)
    assert_context_not_an_input(agent)
    assert_schema_sync(agent, entry)


if __name__ == "__main__":
    main()
