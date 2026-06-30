#!/usr/bin/env python3
"""Custom boolean-rule guardrail with filter action check — Send message to channel.

Validates that a custom guardrail was added on the Slack send tool:
  - At least 1 guardrail with $guardrailType == "custom" targeting
    "Send message to channel"
  - selector.scopes contains "Tool" and matchNames contains the tool
  - rules[0].$ruleType == "boolean", operator == "equals", value is a bool
  - rules[0].fieldSelector has a $selectorType ("all" or "specific")
  - action.$actionType == "filter" with a non-empty fields array; each field
    has path / source / title
  - guardrail id is a UUID

Note: filter is only valid on custom (deterministic) guardrails — never on
built-in validators (anti-pattern 7). This test exercises that legal pairing.
"""

import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(os.getcwd()) / "WebResearchBriefingSolution" / "WebResearchBriefingAgent"
AGENT = ROOT / "agent.json"

TARGET_TOOL = "Send message to channel"
VALID_SELECTOR_TYPES = {"all", "specific"}
VALID_SOURCES = {"input", "output"}


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def main() -> None:
    agent = load(AGENT)

    guardrails = agent.get("guardrails")
    if not isinstance(guardrails, list) or len(guardrails) == 0:
        sys.exit(
            "FAIL: agent.json.guardrails must be a non-empty array, "
            f"got {type(guardrails).__name__}: {guardrails!r}"
        )
    print(f"OK: guardrails array has {len(guardrails)} entry/entries")

    # --- find custom guardrail targeting the Slack tool ---
    custom = [g for g in guardrails if g.get("$guardrailType") == "custom"]
    if not custom:
        types = [(g.get("$guardrailType"), g.get("validatorType")) for g in guardrails]
        sys.exit(f'FAIL: no guardrail with $guardrailType == "custom". Got: {types}')

    targeted = [
        g for g in custom
        if TARGET_TOOL in ((g.get("selector") or {}).get("matchNames") or [])
    ]
    if not targeted:
        all_match = [(g.get("selector") or {}).get("matchNames") or [] for g in custom]
        sys.exit(
            f'FAIL: no custom guardrail targets "{TARGET_TOOL}". '
            f"matchNames across custom guardrails: {all_match}"
        )
    g = targeted[0]
    print(f'OK: custom guardrail targets "{TARGET_TOOL}"')

    # --- UUID id ---
    gid = g.get("id")
    try:
        if not isinstance(gid, str):
            raise ValueError
        uuid.UUID(gid)
    except (ValueError, AttributeError):
        sys.exit(f"FAIL: guardrail.id is not a valid UUID: {gid!r}")
    print(f"OK: guardrail id is a UUID: {gid}")

    # --- selector.scopes contains Tool ---
    scopes = (g.get("selector") or {}).get("scopes") or []
    if "Tool" not in scopes:
        sys.exit(f'FAIL: selector.scopes must contain "Tool", got {scopes!r}')
    print(f"OK: selector.scopes includes 'Tool': {scopes}")

    # --- rules: a boolean rule ---
    rules = g.get("rules")
    if not isinstance(rules, list) or len(rules) == 0:
        sys.exit(f"FAIL: guardrail.rules must be a non-empty array, got {rules!r}")
    bool_rules = [r for r in rules if isinstance(r, dict) and r.get("$ruleType") == "boolean"]
    if not bool_rules:
        rule_types = [r.get("$ruleType") for r in rules if isinstance(r, dict)]
        sys.exit(
            f'FAIL: no rule with $ruleType == "boolean". Got rule types: {rule_types}'
        )
    rule = bool_rules[0]
    print('OK: found rule with $ruleType == "boolean"')

    # fieldSelector
    fs = rule.get("fieldSelector")
    if not isinstance(fs, dict) or fs.get("$selectorType") not in VALID_SELECTOR_TYPES:
        sys.exit(
            f"FAIL: boolean rule fieldSelector.$selectorType must be one of "
            f"{sorted(VALID_SELECTOR_TYPES)}, got {fs!r}"
        )
    print(f'OK: fieldSelector.$selectorType == "{fs.get("$selectorType")}"')

    # operator must be "equals" (only operator supported for boolean rules)
    if rule.get("operator") != "equals":
        sys.exit(
            f'FAIL: boolean rule operator must be "equals", got {rule.get("operator")!r}'
        )
    print('OK: boolean rule operator == "equals"')

    # value must be a real bool
    val = rule.get("value")
    if not isinstance(val, bool):
        sys.exit(f"FAIL: boolean rule value must be true/false, got {val!r}")
    print(f"OK: boolean rule value is a bool: {val}")

    # --- action.$actionType == "filter" with a non-empty fields array ---
    action = g.get("action")
    if not isinstance(action, dict):
        sys.exit(f"FAIL: guardrail.action must be an object, got {action!r}")
    if action.get("$actionType") != "filter":
        sys.exit(
            f'FAIL: action.$actionType must be "filter", got {action.get("$actionType")!r}'
        )
    fields = action.get("fields")
    if not isinstance(fields, list) or len(fields) == 0:
        sys.exit(f"FAIL: filter action.fields must be a non-empty array, got {fields!r}")
    for i, fld in enumerate(fields):
        if not isinstance(fld, dict):
            sys.exit(f"FAIL: filter fields[{i}] must be an object, got {fld!r}")
        if not fld.get("path"):
            sys.exit(f"FAIL: filter fields[{i}] missing path. field={fld!r}")
        if fld.get("source") not in VALID_SOURCES:
            sys.exit(
                f"FAIL: filter fields[{i}].source must be one of {sorted(VALID_SOURCES)}, "
                f"got {fld.get('source')!r}"
            )
        if not fld.get("title"):
            sys.exit(f"FAIL: filter fields[{i}] missing title. field={fld!r}")
    print(f"OK: action.$actionType == 'filter' with {len(fields)} field(s) to redact")

    print("OK: custom boolean-rule guardrail with filter action is valid")


if __name__ == "__main__":
    main()
