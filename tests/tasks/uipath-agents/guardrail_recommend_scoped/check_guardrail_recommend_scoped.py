#!/usr/bin/env python3
"""Tool-scoped deterministic guardrail check — Send message to channel.

Validates that a custom guardrail was added for the Slack tool:
  - At least 1 guardrail with $guardrailType == "custom" exists
  - It targets Tool scope with matchNames containing "Send message to channel"
  - It has a non-empty rules array, each rule has a $ruleType discriminator
  - It has a UUID id, a $actionType set on action
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "WebResearchBriefingSolution" / "WebResearchBriefingAgent"
AGENT = ROOT / "agent.json"

TARGET_TOOL = "Send message to channel"


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

    # Find custom guardrails
    custom = [g for g in guardrails if g.get("$guardrailType") == "custom"]
    if not custom:
        types = [(g.get("$guardrailType"), g.get("validatorType")) for g in guardrails]
        sys.exit(
            f'FAIL: no guardrail with $guardrailType == "custom" found. Got: {types}'
        )
    print(f"OK: found {len(custom)} custom guardrail(s)")

    # Find one targeting the Slack tool
    slack_guards = []
    for g in custom:
        match_names = (g.get("selector") or {}).get("matchNames", [])
        if TARGET_TOOL in match_names:
            slack_guards.append(g)

    if not slack_guards:
        all_match_names = [
            (g.get("selector") or {}).get("matchNames", []) for g in custom
        ]
        sys.exit(
            f'FAIL: no custom guardrail targets "{TARGET_TOOL}". '
            f"matchNames found across custom guardrails: {all_match_names}"
        )
    g = slack_guards[0]
    print(f'OK: custom guardrail targets "{TARGET_TOOL}"')

    # UUID id
    gid = g.get("id")
    if not isinstance(gid, str) or "-" not in gid:
        sys.exit(f"FAIL: guardrail.id missing or malformed: {gid!r}")
    print(f"OK: guardrail id is a UUID: {gid}")

    # action.$actionType
    action = g.get("action")
    if not isinstance(action, dict) or not action.get("$actionType"):
        sys.exit(f"FAIL: guardrail.action.$actionType missing. action={action!r}")
    print(f"OK: action.$actionType = {action['$actionType']!r}")

    # selector.scopes contains "Tool"
    scopes = (g.get("selector") or {}).get("scopes", [])
    if "Tool" not in scopes:
        sys.exit(
            f'FAIL: guardrail selector.scopes must contain "Tool", got {scopes!r}'
        )
    print(f"OK: selector.scopes includes 'Tool': {scopes}")

    # rules array
    rules = g.get("rules")
    if not isinstance(rules, list) or len(rules) == 0:
        sys.exit(
            f"FAIL: guardrail.rules must be a non-empty array, got {rules!r}"
        )
    for i, rule in enumerate(rules):
        if not rule.get("$ruleType"):
            sys.exit(
                f"FAIL: rules[{i}] missing $ruleType discriminator. rule={rule!r}"
            )
    print(f"OK: rules array has {len(rules)} rule(s), all have $ruleType")

    print("OK: custom tool-scoped guardrail check passed")


if __name__ == "__main__":
    main()
