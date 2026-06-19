#!/usr/bin/env python3
"""Edit-roundtrip check.

Validates the final state of GreeterAgent after the agent has
scaffolded, validated, edited, and re-validated it:

  1. agent.json.inputSchema  == entry-points.json entryPoints[0].input
     agent.json.outputSchema == entry-points.json entryPoints[0].output
     (Critical Rule 4 — schema sync survives the edit.)
  2. inputSchema declares BOTH `name` and `language` as required
     string fields (the edit added `language`).
  3. outputSchema declares `greeting` as a string.
  4. The user message template inlines BOTH {{input.name}} and
     {{input.language}} AND contentTokens contains matching variable
     tokens for both fields (Critical Rules 5 and 6).
  5. .agent-builder/agent.json exists — proves validate ran after the
     edit and regenerated the build artifact.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "GreetSol" / "GreeterAgent"
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"
BUILT_AGENT = ROOT / ".agent-builder" / "agent.json"

INPUT_FIELDS = ["name", "language"]


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def assert_schema_sync(agent: dict, entry: dict) -> tuple[dict, dict]:
    entry_points = entry.get("entryPoints")
    if not isinstance(entry_points, list) or not entry_points:
        sys.exit("FAIL: entry-points.json has no entryPoints[0]")
    ep = entry_points[0]
    if agent.get("inputSchema") != ep.get("input"):
        sys.exit(
            "FAIL: agent.json.inputSchema != entry-points.json entryPoints[0].input "
            "— schema sync broken after edit (Critical Rule 4)"
        )
    if agent.get("outputSchema") != ep.get("output"):
        sys.exit(
            "FAIL: agent.json.outputSchema != entry-points.json entryPoints[0].output "
            "— schema sync broken after edit (Critical Rule 4)"
        )
    print("OK: inputSchema and outputSchema are in sync with entry-points.json")
    return agent["inputSchema"], agent["outputSchema"]


def assert_input_fields(in_schema: dict) -> None:
    props = in_schema.get("properties") if isinstance(in_schema, dict) else None
    if not isinstance(props, dict):
        sys.exit(f"FAIL: inputSchema.properties missing or not an object: {props!r}")
    missing = [f for f in INPUT_FIELDS if f not in props]
    if missing:
        sys.exit(
            f"FAIL: inputSchema.properties missing {missing!r} after edit; "
            f"got {sorted(props)!r}"
        )
    for f in INPUT_FIELDS:
        ftype = props[f].get("type") if isinstance(props[f], dict) else None
        if ftype != "string":
            sys.exit(f"FAIL: inputSchema.properties.{f}.type should be 'string', got {ftype!r}")
    required = in_schema.get("required")
    if not isinstance(required, list):
        sys.exit(f"FAIL: inputSchema.required must be a list, got {required!r}")
    missing_req = [f for f in INPUT_FIELDS if f not in required]
    if missing_req:
        sys.exit(
            f"FAIL: inputSchema.required missing {missing_req!r}; got {required!r}"
        )
    print(f"OK: inputSchema declares both {INPUT_FIELDS} as required string fields")


def assert_output_field(out_schema: dict) -> None:
    props = out_schema.get("properties") if isinstance(out_schema, dict) else None
    if not isinstance(props, dict) or "greeting" not in props:
        sys.exit(
            f"FAIL: outputSchema.properties missing 'greeting'; "
            f"got {list(props) if isinstance(props, dict) else props!r}"
        )
    g = props["greeting"]
    if not isinstance(g, dict) or g.get("type") != "string":
        sys.exit(f"FAIL: outputSchema.properties.greeting.type should be 'string', got {g!r}")
    print("OK: outputSchema declares greeting:string")


def assert_user_message_inlines_both(agent: dict) -> None:
    messages = agent.get("messages")
    if not isinstance(messages, list):
        sys.exit(f"FAIL: agent.json.messages is not a list: {messages!r}")
    user_messages = [m for m in messages if isinstance(m, dict) and m.get("role") == "user"]
    if not user_messages:
        sys.exit("FAIL: agent.json.messages has no entry with role == 'user'")
    user = user_messages[0]
    content = user.get("content", "")
    tokens = user.get("contentTokens")
    if not isinstance(tokens, list):
        sys.exit(f"FAIL: user message contentTokens is not a list: {tokens!r}")

    for field in INPUT_FIELDS:
        placeholder = "{{input." + field + "}}"
        if placeholder not in content:
            sys.exit(
                f"FAIL: user message content does not inline {placeholder} "
                f"after edit (Critical Rule 5); content={content!r}"
            )
        expected = {"type": "variable", "rawString": f"input.{field}"}
        if expected not in tokens:
            sys.exit(
                f"FAIL: user message contentTokens missing variable token for "
                f"input.{field} (Critical Rule 6)\n  expected: {expected}\n"
                f"  got tokens: {json.dumps(tokens, indent=2)}"
            )
    print(f"OK: user message inlines both {INPUT_FIELDS} with matching contentTokens")


def assert_agent_builder_regenerated() -> None:
    if not BUILT_AGENT.is_file():
        sys.exit(
            f"FAIL: {BUILT_AGENT} does not exist — validate did not regenerate "
            ".agent-builder/agent.json after the edit"
        )
    try:
        built = json.loads(BUILT_AGENT.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: .agent-builder/agent.json is not valid JSON: {e}")
    built_props = (built.get("inputSchema") or {}).get("properties") or {}
    missing = [f for f in INPUT_FIELDS if f not in built_props]
    if missing:
        sys.exit(
            f"FAIL: .agent-builder/agent.json does not reflect edited "
            f"inputSchema — missing {missing!r}; got {sorted(built_props)!r}"
        )
    print("OK: .agent-builder/agent.json reflects the edited inputSchema")


def main() -> None:
    agent = load(AGENT)
    entry = load(ENTRY)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    assert_input_fields(in_schema)
    assert_output_field(out_schema)
    assert_user_message_inlines_both(agent)
    assert_agent_builder_regenerated()


if __name__ == "__main__":
    main()
