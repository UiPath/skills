#!/usr/bin/env python3
"""Prompt injection guardrail check.

Validates that the agent authored a builtInValidator guardrail for
prompt_injection in agent.json with correct scope constraints:

  - guardrails array exists and is non-empty
  - At least one guardrail has $guardrailType == "builtInValidator"
    and validatorType == "prompt_injection"
  - selector.scopes is exactly ["Llm"] — NOT ["Agent"], ["Tool"],
    or any combination including Agent or Tool
  - validatorParameters contains a number parameter with id "threshold"
  - action.$actionType == "block"
  - id is UUID-shaped

This test specifically validates the most dangerous anti-pattern:
adding prompt_injection to Agent or Tool scope (which is invalid).
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "InjGuardSol" / "InjSafeAgent"
AGENT = ROOT / "agent.json"


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

    # --- find prompt_injection validator ---
    pi = [
        g for g in guardrails
        if g.get("$guardrailType") == "builtInValidator"
        and g.get("validatorType") == "prompt_injection"
    ]
    if not pi:
        types = [
            (g.get("$guardrailType"), g.get("validatorType"))
            for g in guardrails
        ]
        sys.exit(
            f"FAIL: no guardrail with $guardrailType == \"builtInValidator\" "
            f"and validatorType == \"prompt_injection\". Got: {types}"
        )
    g = pi[0]
    print('OK: found builtInValidator guardrail with validatorType == "prompt_injection"')

    # --- id is UUID-shaped ---
    gid = g.get("id")
    if not isinstance(gid, str) or "-" not in gid:
        sys.exit(f"FAIL: guardrail id missing or malformed: {gid!r}")
    print(f"OK: guardrail id is UUID-shaped: {gid}")

    # --- selector.scopes must be exactly ["Llm"] ---
    selector = g.get("selector")
    if not isinstance(selector, dict):
        sys.exit(f"FAIL: guardrail.selector must be an object, got {selector!r}")
    scopes = selector.get("scopes")
    if not isinstance(scopes, list):
        sys.exit(f"FAIL: guardrail.selector.scopes must be an array, got {scopes!r}")

    # prompt_injection only supports Llm scope
    forbidden = {"Agent", "Tool"}
    bad = [s for s in scopes if s in forbidden]
    if bad:
        sys.exit(
            f"FAIL: prompt_injection guardrail must NOT include {bad} in scopes. "
            f"Only \"Llm\" is supported. Got scopes: {scopes}"
        )
    if "Llm" not in scopes:
        sys.exit(
            f'FAIL: prompt_injection guardrail must include "Llm" in scopes. '
            f"Got: {scopes}"
        )
    # Check PascalCase
    if scopes != ["Llm"]:
        sys.exit(
            f'FAIL: prompt_injection scopes should be exactly ["Llm"]. '
            f"Got: {scopes}"
        )
    print('OK: selector.scopes == ["Llm"] (correct Llm-only constraint)')

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

    # --- validatorParameters: threshold (number) ---
    params = g.get("validatorParameters")
    if not isinstance(params, list):
        sys.exit(f"FAIL: validatorParameters must be an array, got {params!r}")

    threshold_param = None
    for p in params:
        if isinstance(p, dict) and p.get("id") == "threshold":
            threshold_param = p
            break

    if threshold_param is None:
        ids = [p.get("id") for p in params if isinstance(p, dict)]
        sys.exit(
            f'FAIL: validatorParameters missing parameter with id == "threshold". '
            f"Got ids: {ids}"
        )
    if threshold_param.get("$parameterType") != "number":
        sys.exit(
            f'FAIL: threshold parameter.$parameterType must be "number", '
            f"got {threshold_param.get('$parameterType')!r}"
        )
    val = threshold_param.get("value")
    if not isinstance(val, (int, float)):
        sys.exit(f"FAIL: threshold parameter.value must be a number, got {val!r}")
    if not (0.0 <= val <= 1.0):
        sys.exit(
            f"FAIL: threshold parameter.value must be between 0.0 and 1.0, "
            f"got {val}"
        )
    print(f"OK: threshold parameter = {val} (number, in range)")

    print("OK: prompt injection guardrail is valid with Llm-only scope")


if __name__ == "__main__":
    main()
