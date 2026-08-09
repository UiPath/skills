#!/usr/bin/env python3
"""Custom word-rule guardrail with block action check — Create Issue.

Validates that a custom guardrail was added on the "Create Issue" tool:
  - At least 1 guardrail with $guardrailType == "custom" targeting
    "Create Issue"
  - selector.scopes contains "Tool" and matchNames contains the tool
  - rules[0].$ruleType == "word", operator == "contains", value ==
    "CONFIDENTIAL"
  - rules[0].fieldSelector has a $selectorType ("all" or "specific")
  - action.$actionType == "block"
  - guardrail id is a UUID

Note: custom deterministic rules only support Tool scope — Agent/Llm scopes
are valid only for builtInValidator guardrails (guardrails.md Selector /
"What NOT to Do" #15). This task targets a named tool so the request stays
satisfiable under that constraint.
"""

import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(os.getcwd()) / "WebResearchBriefingSolution" / "WebResearchBriefingAgent"
AGENT = ROOT / "agent.json"

TARGET_TOOL = "Create Issue"
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

    # --- find custom guardrail targeting the Jira tool ---
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

    # --- id is a UUID ---
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

    # --- rules: a word rule ---
    rules = g.get("rules")
    if not isinstance(rules, list) or len(rules) == 0:
        sys.exit(f"FAIL: guardrail.rules must be a non-empty array, got {rules!r}")
    word_rules = [r for r in rules if isinstance(r, dict) and r.get("$ruleType") == "word"]
    if not word_rules:
        rule_types = [r.get("$ruleType") for r in rules if isinstance(r, dict)]
        sys.exit(f'FAIL: no rule with $ruleType == "word". Got rule types: {rule_types}')
    rule = word_rules[0]
    print('OK: found rule with $ruleType == "word"')

    # --- fieldSelector.$selectorType ---
    fs = rule.get("fieldSelector")
    if not isinstance(fs, dict) or fs.get("$selectorType") not in VALID_SELECTOR_TYPES:
        sys.exit(
            f"FAIL: word rule fieldSelector.$selectorType must be one of "
            f"{sorted(VALID_SELECTOR_TYPES)}, got {fs!r}"
        )
    print(f'OK: fieldSelector.$selectorType == "{fs.get("$selectorType")}"')

    # --- operator == "contains" ---
    if rule.get("operator") != "contains":
        sys.exit(f'FAIL: word rule operator must be "contains", got {rule.get("operator")!r}')
    print('OK: word rule operator == "contains"')

    # --- value == "CONFIDENTIAL" ---
    if rule.get("value") != "CONFIDENTIAL":
        sys.exit(f'FAIL: word rule value must be "CONFIDENTIAL", got {rule.get("value")!r}')
    print('OK: word rule value == "CONFIDENTIAL"')

    # --- action.$actionType == "block" ---
    action = g.get("action")
    if not isinstance(action, dict):
        sys.exit(f"FAIL: guardrail.action must be an object, got {action!r}")
    if action.get("$actionType") != "block":
        sys.exit(f'FAIL: action.$actionType must be "block", got {action.get("$actionType")!r}')
    print('OK: action.$actionType == "block"')

    print("OK: custom word-rule guardrail with block action is valid")


if __name__ == "__main__":
    main()
