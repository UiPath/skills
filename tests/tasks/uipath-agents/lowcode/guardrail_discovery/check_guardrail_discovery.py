#!/usr/bin/env python3
"""Guardrail discovery check.

Validates that the agent added at least one builtInValidator guardrail
to agent.json after using `uip agent guardrails list` to discover
available validators. The YAML success_criteria already verifies the
CLI command was executed; this script validates the resulting agent.json.

Checks:
  - guardrails array exists and is non-empty
  - At least one guardrail has $guardrailType == "builtInValidator"
  - That guardrail has a non-empty validatorType string
  - That guardrail has action with $actionType == "block"
  - selector.scopes uses PascalCase values
  - id is UUID-shaped
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "DiscoverSol" / "DiscoverAgent"
AGENT = ROOT / "agent.json"

VALID_SCOPES = {"Agent", "Llm", "Tool"}


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

    # --- find builtInValidator ---
    validators = [
        g for g in guardrails
        if g.get("$guardrailType") == "builtInValidator"
    ]
    if not validators:
        types = [g.get("$guardrailType") for g in guardrails]
        sys.exit(
            f'FAIL: no guardrail with $guardrailType == "builtInValidator" found. '
            f"Got types: {types}"
        )
    g = validators[0]
    print('OK: found guardrail with $guardrailType == "builtInValidator"')

    # --- validatorType is a non-empty string ---
    vt = g.get("validatorType")
    if not isinstance(vt, str) or not vt:
        sys.exit(f"FAIL: guardrail.validatorType must be a non-empty string, got {vt!r}")
    print(f"OK: validatorType = {vt!r}")

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

    # --- validatorParameters exists ---
    params = g.get("validatorParameters")
    if not isinstance(params, list):
        sys.exit(f"FAIL: validatorParameters must be an array, got {params!r}")
    print(f"OK: validatorParameters has {len(params)} entries")

    print("OK: builtInValidator guardrail discovered and authored correctly")


if __name__ == "__main__":
    main()
