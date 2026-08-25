#!/usr/bin/env python3
"""LLM as Judge built-in validator guardrail check (low-code).

Validates that the agent authored a builtInValidator guardrail for
llm_as_judge in agent.json with correct structure:

  - guardrails array exists and is non-empty
  - At least one guardrail has $guardrailType == "builtInValidator"
    and validatorType == "llm_as_judge"
  - id is UUID-shaped
  - action.$actionType == "block"
  - selector.scopes uses PascalCase values
  - validatorParameters contains an "enum" parameter with id "model" whose
    value is a non-empty string (a ModelId discovered from LLM Gateway)
  - validatorParameters contains a "text" parameter with id "guardrailText"
    whose value is a non-empty string

The model value is NOT pinned to a specific id — the valid set is tenant- and
LLM-Gateway-specific and comes from `uip agent guardrails llm-as-judge-models`.
We only assert the parameter shape and that a model was actually chosen.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "JudgeGuardSol" / "JudgeAgent"
AGENT = ROOT / "agent.json"

VALID_SCOPES = {"Agent", "Llm", "Tool"}


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

    # --- find builtInValidator with llm_as_judge ---
    judge = [
        g for g in guardrails
        if g.get("$guardrailType") == "builtInValidator"
        and g.get("validatorType") == "llm_as_judge"
    ]
    if not judge:
        types = [
            (g.get("$guardrailType"), g.get("validatorType"))
            for g in guardrails
        ]
        sys.exit(
            f"FAIL: no guardrail with $guardrailType == \"builtInValidator\" "
            f"and validatorType == \"llm_as_judge\". Got: {types}"
        )
    g = judge[0]
    print('OK: found builtInValidator guardrail with validatorType == "llm_as_judge"')

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

    # --- model parameter (enum, non-empty string) ---
    model_param = find_param(params, "model")
    if model_param is None:
        ids = [p.get("id") for p in params if isinstance(p, dict)]
        sys.exit(
            f'FAIL: validatorParameters missing parameter with id == "model". '
            f"Got ids: {ids}"
        )
    if model_param.get("$parameterType") != "enum":
        sys.exit(
            f'FAIL: model parameter.$parameterType must be "enum", '
            f"got {model_param.get('$parameterType')!r}"
        )
    model_value = model_param.get("value")
    if not isinstance(model_value, str) or not model_value.strip():
        sys.exit(
            f"FAIL: model parameter.value must be a non-empty string (a ModelId from "
            f"`uip agent guardrails llm-as-judge-models`), got {model_value!r}"
        )
    print(f"OK: model = {model_value!r} (enum, non-empty)")

    # --- guardrailText parameter (text, non-empty string) ---
    text_param = find_param(params, "guardrailText")
    if text_param is None:
        ids = [p.get("id") for p in params if isinstance(p, dict)]
        sys.exit(
            f'FAIL: validatorParameters missing parameter with id == "guardrailText". '
            f"Got ids: {ids}"
        )
    if text_param.get("$parameterType") != "text":
        sys.exit(
            f'FAIL: guardrailText parameter.$parameterType must be "text", '
            f"got {text_param.get('$parameterType')!r}"
        )
    text_value = text_param.get("value")
    if not isinstance(text_value, str) or not text_value.strip():
        sys.exit(
            f"FAIL: guardrailText parameter.value must be a non-empty string, "
            f"got {text_value!r}"
        )
    print("OK: guardrailText is a non-empty text parameter")

    print("OK: LLM as Judge builtInValidator guardrail is valid")


if __name__ == "__main__":
    main()
