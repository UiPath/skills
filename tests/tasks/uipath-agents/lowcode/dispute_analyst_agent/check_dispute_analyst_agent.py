#!/usr/bin/env python3
"""Dispute Analyst Agent check.

Validates that the scaffolded DisputeAnalystAgent faithfully encodes the
Confluence spec for the Billing Dispute Resolution golden scenario:

  1. projectId is a well-formed UUID (Anti-pattern 8).
  2. agent.json.inputSchema  == entry-points.json entryPoints[0].input
     agent.json.outputSchema == entry-points.json entryPoints[0].output
     (Critical Rule 4 — schema sync.)
  3. Input schema declares all five top-level fields (invoice,
     erpInvoice, customerContext, discrepancies, dispute) by name.
  4. Output schema declares every disputeAnalysis field by name —
     either flattened at the top level or nested under a single
     `disputeAnalysis` property. Types and `required` arrays are not
     enforced.
  5. The user message template inlines every input field via
     {{input.<field>}} with a matching variable contentTokens entry
     (Critical Rules 5 and 6).
  6. The system prompt mentions at least three dispute-domain terms,
     guarding against the scaffolded placeholder being left in place.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "DisputeSol" / "DisputeAnalystAgent"
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"

INPUT_FIELDS = ["invoice", "erpInvoice", "customerContext", "discrepancies", "dispute"]

OUTPUT_FIELDS = [
    "validity",
    "rootCause",
    "rootCauseDetail",
    "recommendedResolution",
    "recommendedCreditAmount",
    "confidenceScore",
    "rationale",
    "customerFacingExplanation",
    "flags",
]

DOMAIN_TERMS = ["dispute", "validity", "confidence", "root cause", "credit"]


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
        sys.exit(f"FAIL: inputSchema is not a dict: {schema!r}")
    props = schema.get("properties")
    if not isinstance(props, dict):
        sys.exit(f"FAIL: inputSchema.properties is not an object: {props!r}")
    missing = [f for f in INPUT_FIELDS if f not in props]
    if missing:
        sys.exit(
            f"FAIL: inputSchema.properties missing fields {missing!r}; "
            f"got {sorted(props)!r}"
        )
    print(f"OK: inputSchema declares all 5 fields ({', '.join(INPUT_FIELDS)})")


def resolve_analysis_properties(out_schema: dict) -> dict:
    """Return the flat property map for disputeAnalysis fields.

    Accepts either:
      A) Flattened at the top level — properties contains validity,
         rootCause, etc. directly.
      B) Nested — properties contains a single `disputeAnalysis` object
         whose own properties hold the fields.
    """
    if not isinstance(out_schema, dict):
        sys.exit(f"FAIL: outputSchema must be a dict, got {out_schema!r}")
    props = out_schema.get("properties")
    if not isinstance(props, dict):
        sys.exit(f"FAIL: outputSchema.properties is not an object: {props!r}")

    if "disputeAnalysis" in props and "validity" not in props:
        nested = props["disputeAnalysis"]
        if not isinstance(nested, dict):
            sys.exit(
                "FAIL: outputSchema.properties.disputeAnalysis must be an object, "
                f"got {nested!r}"
            )
        inner = nested.get("properties")
        if not isinstance(inner, dict):
            sys.exit(
                "FAIL: outputSchema.properties.disputeAnalysis.properties missing"
            )
        print("OK: outputSchema uses nested disputeAnalysis object")
        return inner

    print("OK: outputSchema uses flattened disputeAnalysis fields at top level")
    return props


def assert_output_shape(out_schema: dict) -> None:
    props = resolve_analysis_properties(out_schema)
    missing = [f for f in OUTPUT_FIELDS if f not in props]
    if missing:
        sys.exit(
            f"FAIL: outputSchema missing fields {missing!r}; "
            f"got {sorted(props)!r}"
        )
    print(f"OK: outputSchema declares all {len(OUTPUT_FIELDS)} fields")


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
    print(f"OK: user message inlines all 5 inputs with matching contentTokens")


def assert_system_prompt_domain(agent: dict) -> None:
    messages = agent.get("messages", [])
    system = next(
        (m for m in messages if isinstance(m, dict) and m.get("role") == "system"),
        None,
    )
    if system is None:
        sys.exit("FAIL: agent.json.messages has no entry with role == 'system'")
    content = (system.get("content") or "").lower()
    hits = [term for term in DOMAIN_TERMS if term in content]
    if len(hits) < 3:
        sys.exit(
            f"FAIL: system prompt does not look dispute-domain-specific; "
            f"matched {hits!r} out of {DOMAIN_TERMS!r}"
        )
    print(f"OK: system prompt covers dispute-domain terms ({hits})")


def main() -> None:
    agent = load(AGENT)
    entry = load(ENTRY)

    assert_project_id(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    assert_input_shape(in_schema)
    assert_output_shape(out_schema)
    assert_user_message_inlines(agent)
    assert_system_prompt_domain(agent)


if __name__ == "__main__":
    main()
