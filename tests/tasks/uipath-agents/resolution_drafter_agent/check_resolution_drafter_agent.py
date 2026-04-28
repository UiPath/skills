#!/usr/bin/env python3
"""Resolution Drafter Agent check.

Validates that the scaffolded ResolutionDrafterAgent follows the
Confluence spec for the Billing Dispute Resolution golden scenario:

  1. projectId is a well-formed UUID (Anti-pattern 8).
  2. agent.json.inputSchema  == entry-points.json entryPoints[0].input
     agent.json.outputSchema == entry-points.json entryPoints[0].output
     (Critical Rule 4 — schema sync.)
  3. Input schema declares the four documented fields by name:
     customer, invoice, adjustment, disputeAnalysis.
  4. Output schema declares `subject` and `body` by name. Types and
     `required` arrays are not enforced.
  5. The user-message template inlines every input field via
     {{input.<field>}} with a matching variable contentTokens entry
     (Critical Rules 5 and 6).
  6. The system prompt covers all three adjustment-type variations
     (credit memo / revised invoice / both or multiple) so the drafter
     adapts its output to the adjustment type.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "ResolutionSol" / "ResolutionDrafterAgent"
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"

INPUT_FIELDS = ["customer", "invoice", "adjustment", "disputeAnalysis"]
OUTPUT_FIELDS = ["subject", "body"]


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def assert_project_id(agent: dict) -> None:
    pid = agent.get("projectId")
    if not isinstance(pid, str) or "-" not in pid:
        sys.exit(f"FAIL: projectId is missing or malformed: {pid!r}")
    print(f"OK: projectId is a UUID-shaped string ({pid})")


def assert_schema_sync(agent: dict, entry: dict) -> tuple[dict, dict]:
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

    return agent_in, agent_out


def assert_input_shape(schema: dict) -> None:
    if not isinstance(schema, dict):
        sys.exit(f"FAIL: inputSchema must be a dict, got {schema!r}")
    props = schema.get("properties")
    if not isinstance(props, dict):
        sys.exit(f"FAIL: inputSchema.properties is not an object: {props!r}")
    missing = [f for f in INPUT_FIELDS if f not in props]
    if missing:
        sys.exit(
            f"FAIL: inputSchema.properties missing fields {missing!r}; "
            f"got {sorted(props)!r}"
        )
    print(f"OK: inputSchema declares all 4 fields ({', '.join(INPUT_FIELDS)})")


def assert_output_shape(schema: dict) -> None:
    if not isinstance(schema, dict):
        sys.exit(f"FAIL: outputSchema must be a dict, got {schema!r}")
    props = schema.get("properties")
    if not isinstance(props, dict):
        sys.exit(f"FAIL: outputSchema.properties is not an object: {props!r}")
    missing = [f for f in OUTPUT_FIELDS if f not in props]
    if missing:
        sys.exit(
            f"FAIL: outputSchema.properties missing fields {missing!r}; "
            f"got {sorted(props)!r}"
        )
    print(f"OK: outputSchema declares fields {OUTPUT_FIELDS}")


def get_user_message(agent: dict) -> dict:
    messages = agent.get("messages")
    if not isinstance(messages, list):
        sys.exit(f"FAIL: agent.json.messages is not a list: {messages!r}")
    user_messages = [m for m in messages if isinstance(m, dict) and m.get("role") == "user"]
    if not user_messages:
        sys.exit("FAIL: agent.json.messages has no entry with role == 'user'")
    return user_messages[0]


def assert_user_message_inlines(agent: dict) -> None:
    user = get_user_message(agent)
    content = user.get("content", "")
    tokens = user.get("contentTokens")
    if not isinstance(tokens, list):
        sys.exit(f"FAIL: user message contentTokens is not a list: {tokens!r}")

    for field in INPUT_FIELDS:
        placeholder = "{{input." + field + "}}"
        if placeholder not in content:
            sys.exit(
                f"FAIL: user message content does not inline {placeholder}; "
                f"content={content!r}"
            )
        expected = {"type": "variable", "rawString": f"input.{field}"}
        if expected not in tokens:
            sys.exit(
                f"FAIL: user message contentTokens missing variable token for "
                f"input.{field}\n  expected: {expected}\n"
                f"  got tokens: {json.dumps(tokens, indent=2)}"
            )
    print(f"OK: user message inlines all 4 inputs with matching contentTokens")


def assert_system_prompt_three_way(agent: dict) -> None:
    messages = agent.get("messages", [])
    system = next(
        (m for m in messages if isinstance(m, dict) and m.get("role") == "system"),
        None,
    )
    if system is None:
        sys.exit("FAIL: agent.json.messages has no entry with role == 'system'")
    content = (system.get("content") or "").lower()

    if "credit memo" not in content:
        sys.exit("FAIL: system prompt does not mention 'credit memo'")
    if "revised invoice" not in content:
        sys.exit("FAIL: system prompt does not mention 'revised invoice'")
    if "both" not in content and "multiple" not in content:
        sys.exit(
            "FAIL: system prompt does not handle the combined case "
            "(neither 'both' nor 'multiple' present)"
        )
    print(
        "OK: system prompt covers all three adjustment types "
        "(credit memo, revised invoice, both/multiple)"
    )


def main() -> None:
    agent = load(AGENT)
    entry = load(ENTRY)

    assert_project_id(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    assert_input_shape(in_schema)
    assert_output_shape(out_schema)
    assert_user_message_inlines(agent)
    assert_system_prompt_three_way(agent)


if __name__ == "__main__":
    main()
