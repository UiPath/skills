#!/usr/bin/env python3
"""Custom guardrail with word rule check.

Validates that the agent authored a custom guardrail in agent.json with
correct discriminator fields and structure:

  - guardrails array exists and is non-empty
  - At least one guardrail has $guardrailType == "custom"
  - That guardrail has a rules array with at least one rule
  - The rule has $ruleType == "word"
  - The rule has a fieldSelector with $selectorType ("all" or "specific")
  - The rule has operator == "contains" and value == "CONFIDENTIAL"
  - The guardrail has action.$actionType == "block"
  - The guardrail has selector.scopes with PascalCase values
  - The guardrail has a UUID-shaped id
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "GuardSol" / "SafeAgent"
AGENT = ROOT / "agent.json"

VALID_SCOPES = {"Agent", "Llm", "Tool"}
VALID_SELECTOR_TYPES = {"all", "specific"}


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def main() -> None:
    agent = load(AGENT)

    # --- guardrails array exists ---
    guardrails = agent.get("guardrails")
    if not isinstance(guardrails, list) or len(guardrails) == 0:
        sys.exit(
            "FAIL: agent.json.guardrails must be a non-empty array, "
            f"got {type(guardrails).__name__}: {guardrails!r}"
        )
    print(f"OK: guardrails array has {len(guardrails)} entry/entries")

    # --- find custom guardrail ---
    custom = [g for g in guardrails if g.get("$guardrailType") == "custom"]
    if not custom:
        types = [g.get("$guardrailType") for g in guardrails]
        sys.exit(
            f'FAIL: no guardrail with $guardrailType == "custom" found. '
            f"Got types: {types}"
        )
    g = custom[0]
    print('OK: found guardrail with $guardrailType == "custom"')

    # --- id is UUID-shaped ---
    gid = g.get("id")
    if not isinstance(gid, str) or "-" not in gid:
        sys.exit(f"FAIL: guardrail id missing or malformed: {gid!r}")
    print(f"OK: guardrail id is UUID-shaped: {gid}")

    # --- action.$actionType == "block" ---
    action = g.get("action")
    if not isinstance(action, dict):
        sys.exit(f"FAIL: guardrail.action must be an object, got {action!r}")
    if action.get("$actionType") != "block":
        sys.exit(
            f'FAIL: guardrail.action.$actionType must be "block", '
            f"got {action.get('$actionType')!r}"
        )
    print('OK: action.$actionType == "block"')

    # --- selector.scopes ---
    selector = g.get("selector")
    if not isinstance(selector, dict):
        sys.exit(f"FAIL: guardrail.selector must be an object, got {selector!r}")
    scopes = selector.get("scopes")
    if not isinstance(scopes, list) or len(scopes) == 0:
        sys.exit(f"FAIL: guardrail.selector.scopes must be a non-empty array, got {scopes!r}")
    invalid = [s for s in scopes if s not in VALID_SCOPES]
    if invalid:
        sys.exit(
            f"FAIL: guardrail.selector.scopes contains invalid values {invalid}. "
            f'Valid PascalCase values: {sorted(VALID_SCOPES)}'
        )
    print(f"OK: selector.scopes = {scopes} (all PascalCase)")

    # --- rules array ---
    rules = g.get("rules")
    if not isinstance(rules, list) or len(rules) == 0:
        sys.exit(f"FAIL: guardrail.rules must be a non-empty array, got {rules!r}")

    # --- first rule: $ruleType == "word" ---
    rule = rules[0]
    if rule.get("$ruleType") != "word":
        sys.exit(
            f'FAIL: rules[0].$ruleType must be "word", '
            f"got {rule.get('$ruleType')!r}"
        )
    print('OK: rules[0].$ruleType == "word"')

    # --- fieldSelector.$selectorType ---
    fs = rule.get("fieldSelector")
    if not isinstance(fs, dict):
        sys.exit(f"FAIL: rules[0].fieldSelector must be an object, got {fs!r}")
    st = fs.get("$selectorType")
    if st not in VALID_SELECTOR_TYPES:
        sys.exit(
            f"FAIL: rules[0].fieldSelector.$selectorType must be one of "
            f"{sorted(VALID_SELECTOR_TYPES)}, got {st!r}"
        )
    print(f'OK: fieldSelector.$selectorType == "{st}"')

    # --- operator == "contains" ---
    if rule.get("operator") != "contains":
        sys.exit(
            f'FAIL: rules[0].operator must be "contains", '
            f"got {rule.get('operator')!r}"
        )
    print('OK: rules[0].operator == "contains"')

    # --- value == "CONFIDENTIAL" ---
    if rule.get("value") != "CONFIDENTIAL":
        sys.exit(
            f'FAIL: rules[0].value must be "CONFIDENTIAL", '
            f"got {rule.get('value')!r}"
        )
    print('OK: rules[0].value == "CONFIDENTIAL"')

    print("OK: custom guardrail with word rule and block action is valid")


if __name__ == "__main__":
    main()
