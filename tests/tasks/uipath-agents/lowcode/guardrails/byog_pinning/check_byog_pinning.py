#!/usr/bin/env python3
"""BYO guardrail pinning check.

Validates that the agent authored a builtInValidator guardrail for
pii_detection in agent.json that is pinned to the BYO configuration the
mocked discovery served (see mock_template/mocks/uip):

  - guardrails array exists and is non-empty
  - At least one guardrail has $guardrailType == "builtInValidator"
    and validatorType == "pii_detection"
  - That guardrail carries byoValidatorName == "byog-smoke-agent-pin" —
    NOT byoConfigurationId, which is not a field the guardrail schema
    uses. The mocked list also contains a built-in entry with the same
    Validator name, so a missing/wrong byoValidatorName means the agent
    failed to disambiguate and pinned the built-in instead.
  - entities are PascalCase and include Email + PhoneNumber
  - action.$actionType == "block"

Pure agent.json assertions — no tenant call. The expected name is the
constant the mock serves; keep the two in sync.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "WebResearchBriefingSolution" / "WebResearchBriefingAgent"
AGENT = ROOT / "agent.json"

VALIDATOR_NAME = "byog-smoke-agent-pin"
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

    guardrails = agent.get("guardrails")
    if not isinstance(guardrails, list) or len(guardrails) == 0:
        sys.exit(
            "FAIL: agent.json.guardrails must be a non-empty array, "
            f"got {type(guardrails).__name__}: {guardrails!r}"
        )
    print(f"OK: guardrails array has {len(guardrails)} entry/entries")

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
            'FAIL: no guardrail with $guardrailType == "builtInValidator" '
            f'and validatorType == "pii_detection". Got: {types}'
        )

    # --- the BYO pin (the point of this test) ---
    pinned = [g for g in pii if g.get("byoValidatorName") == VALIDATOR_NAME]
    if not pinned:
        pins = [g.get("byoValidatorName") for g in pii]
        sys.exit(
            f"FAIL: no pii_detection guardrail pinned to the BYO "
            f"configuration. Expected byoValidatorName == {VALIDATOR_NAME!r}, "
            f"got: {pins} — the agent likely authored the built-in validator "
            "instead of the BYO-backed one, or invented a name."
        )
    g = pinned[0]
    print(f"OK: guardrail pinned to BYO configuration {VALIDATOR_NAME!r}")

    action = g.get("action")
    if not isinstance(action, dict) or action.get("$actionType") != "block":
        sys.exit(
            'FAIL: guardrail.action.$actionType must be "block", '
            f"got {action!r}"
        )
    print('OK: action.$actionType == "block"')

    params = g.get("validatorParameters")
    if not isinstance(params, list):
        sys.exit(f"FAIL: validatorParameters must be an array, got {params!r}")
    entities_param = find_param(params, "entities")
    if entities_param is None:
        ids = [p.get("id") for p in params if isinstance(p, dict)]
        sys.exit(
            'FAIL: validatorParameters missing parameter with id == "entities". '
            f"Got ids: {ids}"
        )
    entities_value = entities_param.get("value")
    if not isinstance(entities_value, list):
        sys.exit(f"FAIL: entities parameter.value must be an array, got {entities_value!r}")
    missing = REQUIRED_ENTITIES - set(entities_value)
    if missing:
        sys.exit(
            f"FAIL: entities must include {sorted(REQUIRED_ENTITIES)}, "
            f"missing: {sorted(missing)}. Got: {entities_value}"
        )
    snake = [
        e for e in entities_value
        if isinstance(e, str) and ("_" in e or e[:1].islower())
    ]
    if snake:
        sys.exit(
            f"FAIL: entity names must be PascalCase (not snake_case). Invalid: {snake}"
        )
    print(f"OK: entities = {entities_value} (PascalCase, includes required)")

    print("OK: BYO-pinned pii_detection guardrail is valid")


if __name__ == "__main__":
    main()
