#!/usr/bin/env python3
"""Intellectual property guardrail check (low-code builtInValidator).

Validates that the agent authored a builtInValidator guardrail for
intellectual_property in agent.json:

  - guardrails array exists and is non-empty
  - At least one guardrail has $guardrailType == "builtInValidator"
    and validatorType == "intellectual_property"
  - validatorParameters contains an enum-list parameter id "ipEntities"
    whose value includes the PascalCase entities "Text" and "Code"
  - selector.scopes is a subset of {"Llm", "Agent"} and does NOT include
    "Tool" (intellectual_property does not support Tool scope — anti-pattern 4)
  - action.$actionType == "block"
  - id is UUID-shaped
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "IPSol" / "IPAgent"
AGENT = ROOT / "agent.json"

REQUIRED_ENTITIES = {"Text", "Code"}
ALLOWED_SCOPES = {"Llm", "Agent"}


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

    # --- find intellectual_property validator ---
    ip = [
        g for g in guardrails
        if g.get("$guardrailType") == "builtInValidator"
        and g.get("validatorType") == "intellectual_property"
    ]
    if not ip:
        types = [
            (g.get("$guardrailType"), g.get("validatorType"))
            for g in guardrails
        ]
        sys.exit(
            f'FAIL: no guardrail with $guardrailType == "builtInValidator" '
            f'and validatorType == "intellectual_property". Got: {types}'
        )
    g = ip[0]
    print('OK: found builtInValidator guardrail with validatorType == "intellectual_property"')

    # --- id is UUID-shaped ---
    gid = g.get("id")
    if not isinstance(gid, str) or "-" not in gid:
        sys.exit(f"FAIL: guardrail id missing or malformed: {gid!r}")
    print(f"OK: guardrail id is UUID-shaped: {gid}")

    # --- validatorParameters: ipEntities enum-list with Text + Code ---
    params = g.get("validatorParameters")
    if not isinstance(params, list):
        sys.exit(f"FAIL: validatorParameters must be an array, got {params!r}")
    ip_param = next(
        (p for p in params if isinstance(p, dict) and p.get("id") == "ipEntities"),
        None,
    )
    if ip_param is None:
        ids = [p.get("id") for p in params if isinstance(p, dict)]
        sys.exit(
            f'FAIL: validatorParameters missing parameter with id == "ipEntities". '
            f"Got ids: {ids}"
        )
    if ip_param.get("$parameterType") != "enum-list":
        sys.exit(
            f'FAIL: ipEntities parameter.$parameterType must be "enum-list", '
            f"got {ip_param.get('$parameterType')!r}"
        )
    value = ip_param.get("value")
    if not isinstance(value, list):
        sys.exit(f"FAIL: ipEntities value must be an array, got {value!r}")
    missing = REQUIRED_ENTITIES - set(value)
    if missing:
        sys.exit(
            f"FAIL: ipEntities must include PascalCase {sorted(REQUIRED_ENTITIES)}, "
            f"missing {sorted(missing)}. Got: {value}"
        )
    print(f"OK: ipEntities enum-list includes {sorted(REQUIRED_ENTITIES)}: {value}")

    # --- selector.scopes subset of {Llm, Agent}, excludes Tool ---
    selector = g.get("selector")
    if not isinstance(selector, dict):
        sys.exit(f"FAIL: guardrail.selector must be an object, got {selector!r}")
    scopes = selector.get("scopes")
    if not isinstance(scopes, list) or len(scopes) == 0:
        sys.exit(f"FAIL: guardrail.selector.scopes must be a non-empty array, got {scopes!r}")
    if "Tool" in scopes:
        sys.exit(
            f'FAIL: intellectual_property does not support "Tool" scope '
            f"(anti-pattern 4). Got scopes: {scopes}"
        )
    invalid = [s for s in scopes if s not in ALLOWED_SCOPES]
    if invalid:
        sys.exit(
            f"FAIL: scopes {invalid} not valid for intellectual_property. "
            f"Allowed: {sorted(ALLOWED_SCOPES)}. Got: {scopes}"
        )
    print(f"OK: selector.scopes ⊆ {sorted(ALLOWED_SCOPES)} (no Tool): {scopes}")

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

    print("OK: intellectual property guardrail is valid")


if __name__ == "__main__":
    main()
