#!/usr/bin/env python3
"""BYO guardrail pinning check.

Validates that the agent authored a builtInValidator guardrail for
pii_detection in agent.json that is pinned to the seeded BYOG
configuration:

  - guardrails array exists and is non-empty
  - At least one guardrail has $guardrailType == "builtInValidator"
    and validatorType == "pii_detection"
  - That guardrail carries byoConfigurationId == the Id of the tenant's
    "byog-smoke-agent-pin" configuration (re-fetched live at check time —
    the pin must reference the real seeded record, not an invented GUID)
  - entities are PascalCase and include Email + PhoneNumber
  - action.$actionType == "block"

The expected configuration id comes from `uip guardrails
byo-configurations list` rather than a seed file, so the agent's workspace
carries no artifact it could shortcut discovery with.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "ByogPinSol" / "ByogPinAgent"
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


def seeded_configuration_id() -> str:
    r = subprocess.run(
        ["uip", "guardrails", "byo-configurations", "list", "--output", "json"],
        capture_output=True, text=True, timeout=120,
    )
    try:
        env = json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        env = {}
    for c in env.get("Data") or []:
        if isinstance(c, dict) and c.get("ValidatorName") == VALIDATOR_NAME:
            return str(c.get("Id"))
    sys.exit(
        f'FAIL: tenant has no BYOG configuration named "{VALIDATOR_NAME}" '
        "(seed missing or swept early) — cannot verify the pin"
    )


def find_param(params: list, param_id: str) -> dict | None:
    for p in params:
        if isinstance(p, dict) and p.get("id") == param_id:
            return p
    return None


def main() -> None:
    agent = load(AGENT)
    expected_id = seeded_configuration_id()

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
    pinned = [g for g in pii if g.get("byoConfigurationId") == expected_id]
    if not pinned:
        pins = [g.get("byoConfigurationId") for g in pii]
        sys.exit(
            f"FAIL: no pii_detection guardrail pinned to the seeded BYOG "
            f"configuration. Expected byoConfigurationId == {expected_id!r}, "
            f"got: {pins}"
        )
    g = pinned[0]
    print(f"OK: guardrail pinned to seeded BYOG configuration {expected_id}")

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
