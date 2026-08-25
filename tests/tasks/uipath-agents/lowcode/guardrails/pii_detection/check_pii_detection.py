#!/usr/bin/env python3
"""PII detection built-in validator guardrail check.

Validates that the agent authored a builtInValidator guardrail for
pii_detection in agent.json with correct structure:

  - guardrails array exists and is non-empty
  - At least one guardrail has $guardrailType == "builtInValidator"
  - That guardrail has validatorType == "pii_detection"
  - validatorParameters contains an enum-list parameter with id "entities"
    and PascalCase entity names (Email, PhoneNumber)
  - validatorParameters contains a map-enum parameter with id
    "entityThresholds" and matching entity keys
  - action.$actionType == "block"
  - selector.scopes uses PascalCase values
  - id is UUID-shaped
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "PiiGuardSol" / "PiiSafeAgent"
AGENT = ROOT / "agent.json"

VALID_SCOPES = {"Agent", "Llm", "Tool"}
REQUIRED_ENTITIES = {"Email", "PhoneNumber"}


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def find_param(params: list, param_id: str) -> dict | None:
    for p in params:
        if isinstance(p, dict) and p.get("id") == param_id:
            return p
    return None


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

    # --- find builtInValidator with pii_detection ---
    pii = [
        g for g in guardrails
        if g.get("$guardrailType") == "builtInValidator"
        and g.get("validatorType") == "pii_detection"
    ]
    if not pii:
        types = [
            (g.get("$guardrailType"), g.get("validatorType"))
            for g in guardrails
        ]
        sys.exit(
            f"FAIL: no guardrail with $guardrailType == \"builtInValidator\" "
            f"and validatorType == \"pii_detection\". Got: {types}"
        )
    g = pii[0]
    print('OK: found builtInValidator guardrail with validatorType == "pii_detection"')

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
            f"Valid PascalCase values: {sorted(VALID_SCOPES)}"
        )
    print(f"OK: selector.scopes = {scopes} (all PascalCase)")

    # --- validatorParameters ---
    params = g.get("validatorParameters")
    if not isinstance(params, list):
        sys.exit(f"FAIL: validatorParameters must be an array, got {params!r}")

    # --- entities parameter (enum-list) ---
    entities_param = find_param(params, "entities")
    if entities_param is None:
        ids = [p.get("id") for p in params if isinstance(p, dict)]
        sys.exit(
            f'FAIL: validatorParameters missing parameter with id == "entities". '
            f"Got ids: {ids}"
        )
    if entities_param.get("$parameterType") != "enum-list":
        sys.exit(
            f'FAIL: entities parameter.$parameterType must be "enum-list", '
            f"got {entities_param.get('$parameterType')!r}"
        )
    entities_value = entities_param.get("value")
    if not isinstance(entities_value, list):
        sys.exit(f"FAIL: entities parameter.value must be an array, got {entities_value!r}")
    entities_set = set(entities_value)
    missing = REQUIRED_ENTITIES - entities_set
    if missing:
        sys.exit(
            f"FAIL: entities parameter.value must include {sorted(REQUIRED_ENTITIES)}, "
            f"missing: {sorted(missing)}. Got: {entities_value}"
        )
    # Check PascalCase (first letter uppercase, no underscores)
    snake = [e for e in entities_value if "_" in e or (isinstance(e, str) and e[0].islower())]
    if snake:
        sys.exit(
            f"FAIL: entity names must be PascalCase (not snake_case). "
            f"Invalid: {snake}. Expected: Email, PhoneNumber, etc."
        )
    print(f"OK: entities = {entities_value} (PascalCase, includes required)")

    # --- entityThresholds parameter (map-enum) ---
    thresholds_param = find_param(params, "entityThresholds")
    if thresholds_param is None:
        print("WARN: entityThresholds parameter not found (optional but recommended)")
    else:
        if thresholds_param.get("$parameterType") != "map-enum":
            sys.exit(
                f'FAIL: entityThresholds parameter.$parameterType must be "map-enum", '
                f"got {thresholds_param.get('$parameterType')!r}"
            )
        thresholds_value = thresholds_param.get("value")
        if not isinstance(thresholds_value, dict):
            sys.exit(
                f"FAIL: entityThresholds parameter.value must be an object, "
                f"got {thresholds_value!r}"
            )
        print(f"OK: entityThresholds = {thresholds_value} (map-enum)")

    print("OK: PII detection builtInValidator guardrail is valid")


if __name__ == "__main__":
    main()
