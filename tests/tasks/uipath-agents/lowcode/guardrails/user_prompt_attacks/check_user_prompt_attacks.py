#!/usr/bin/env python3
"""User prompt attacks guardrail check (low-code builtInValidator).

Validates that the agent authored a builtInValidator guardrail for
user_prompt_attacks in agent.json with correct scope constraints:

  - guardrails array exists and is non-empty
  - At least one guardrail has $guardrailType == "builtInValidator"
    and validatorType == "user_prompt_attacks"
  - selector.scopes is exactly ["Llm"] — NOT Agent or Tool
    (user_prompt_attacks is Llm-only, PreExecution-only — anti-pattern 3)
  - validatorParameters is empty (this validator takes no parameters)
  - action.$actionType == "block"
  - id is UUID-shaped

This test specifically validates the most dangerous anti-pattern:
adding user_prompt_attacks to Agent or Tool scope (which is invalid).
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "UPASol" / "UPAAgent"
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

    # --- find user_prompt_attacks validator ---
    upa = [
        g for g in guardrails
        if g.get("$guardrailType") == "builtInValidator"
        and g.get("validatorType") == "user_prompt_attacks"
    ]
    if not upa:
        types = [
            (g.get("$guardrailType"), g.get("validatorType"))
            for g in guardrails
        ]
        sys.exit(
            f'FAIL: no guardrail with $guardrailType == "builtInValidator" '
            f'and validatorType == "user_prompt_attacks". Got: {types}'
        )
    g = upa[0]
    print('OK: found builtInValidator guardrail with validatorType == "user_prompt_attacks"')

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

    forbidden = {"Agent", "Tool"}
    bad = [s for s in scopes if s in forbidden]
    if bad:
        sys.exit(
            f"FAIL: user_prompt_attacks guardrail must NOT include {bad} in scopes. "
            f'Only "Llm" is supported. Got scopes: {scopes}'
        )
    if scopes != ["Llm"]:
        sys.exit(
            f'FAIL: user_prompt_attacks scopes should be exactly ["Llm"]. '
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

    # --- validatorParameters: must be empty (no parameters for this validator) ---
    params = g.get("validatorParameters", [])
    if not isinstance(params, list):
        sys.exit(f"FAIL: validatorParameters must be an array, got {params!r}")
    if len(params) != 0:
        sys.exit(
            "FAIL: user_prompt_attacks takes no parameters — validatorParameters "
            f"must be empty, got {params!r}"
        )
    print("OK: validatorParameters is empty (correct — validator takes no params)")

    print("OK: user prompt attacks guardrail is valid with Llm-only scope")


if __name__ == "__main__":
    main()
