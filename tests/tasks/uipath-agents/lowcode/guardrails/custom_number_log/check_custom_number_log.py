#!/usr/bin/env python3
"""Custom number-rule guardrail with log action check — Count Sources tool.

Validates that a custom guardrail was added on the Count Sources tool:
  - At least 1 guardrail with $guardrailType == "custom" targeting "Count Sources"
  - selector.scopes contains "Tool" and matchNames contains "Count Sources"
  - rules[0].$ruleType == "number"
  - rules[0].operator is a valid numeric operator
  - rules[0].value is numeric
  - rules[0].fieldSelector has a $selectorType ("all" or "specific")
  - action.$actionType == "log" with a valid severityLevel (Info/Warning/Error)
  - guardrail id is a UUID
"""

import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(os.getcwd()) / "WebResearchBriefingSolution" / "WebResearchBriefingAgent"
AGENT = ROOT / "agent.json"

TARGET_TOOL = "Count Sources"
NUMBER_OPERATORS = {
    "equals", "doesNotEqual", "greaterThan", "greaterThanOrEqual",
    "lessThan", "lessThanOrEqual",
}
VALID_SEVERITIES = {"Info", "Warning", "Error"}
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

    guardrails = agent.get("guardrails")
    if not isinstance(guardrails, list) or len(guardrails) == 0:
        sys.exit(
            "FAIL: agent.json.guardrails must be a non-empty array, "
            f"got {type(guardrails).__name__}: {guardrails!r}"
        )
    print(f"OK: guardrails array has {len(guardrails)} entry/entries")

    # --- find custom guardrail targeting Count Sources ---
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

    # --- rules: a number rule ---
    rules = g.get("rules")
    if not isinstance(rules, list) or len(rules) == 0:
        sys.exit(f"FAIL: guardrail.rules must be a non-empty array, got {rules!r}")
    number_rules = [r for r in rules if isinstance(r, dict) and r.get("$ruleType") == "number"]
    if not number_rules:
        rule_types = [r.get("$ruleType") for r in rules if isinstance(r, dict)]
        sys.exit(
            f'FAIL: no rule with $ruleType == "number". Got rule types: {rule_types}'
        )
    rule = number_rules[0]
    print('OK: found rule with $ruleType == "number"')

    # fieldSelector
    fs = rule.get("fieldSelector")
    if not isinstance(fs, dict) or fs.get("$selectorType") not in VALID_SELECTOR_TYPES:
        sys.exit(
            f"FAIL: number rule fieldSelector.$selectorType must be one of "
            f"{sorted(VALID_SELECTOR_TYPES)}, got {fs!r}"
        )
    print(f'OK: fieldSelector.$selectorType == "{fs.get("$selectorType")}"')

    # operator
    op = rule.get("operator")
    if op not in NUMBER_OPERATORS:
        sys.exit(
            f"FAIL: number rule operator must be one of {sorted(NUMBER_OPERATORS)}, "
            f"got {op!r}"
        )
    print(f'OK: number rule operator == "{op}"')

    # numeric value (bool is a subclass of int — reject it explicitly)
    val = rule.get("value")
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        sys.exit(f"FAIL: number rule value must be numeric, got {val!r}")
    print(f"OK: number rule value is numeric: {val}")

    # --- action.$actionType == "log" with valid severityLevel ---
    action = g.get("action")
    if not isinstance(action, dict):
        sys.exit(f"FAIL: guardrail.action must be an object, got {action!r}")
    if action.get("$actionType") != "log":
        sys.exit(
            f'FAIL: action.$actionType must be "log", got {action.get("$actionType")!r}'
        )
    sev = action.get("severityLevel")
    if sev not in VALID_SEVERITIES:
        sys.exit(
            f"FAIL: log action severityLevel must be one of {sorted(VALID_SEVERITIES)}, "
            f"got {sev!r}"
        )
    print(f'OK: action.$actionType == "log" with severityLevel == "{sev}"')

    print("OK: custom number-rule guardrail with log action is valid")


if __name__ == "__main__":
    main()
