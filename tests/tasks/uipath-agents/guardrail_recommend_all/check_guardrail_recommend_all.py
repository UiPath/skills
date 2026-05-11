#!/usr/bin/env python3
"""Guardrail recommendation check — Web Research Briefing Agent.

Validates that guardrail recommendation for a web research agent produces:
  - At least 2 guardrails in agent.json
  - At least one Llm-scoped builtInValidator (prompt_injection or user_prompt_attacks)
  - At least one content-safety guardrail (harmful_content or intellectual_property)
  - Each guardrail has: UUID id, non-empty selector.scopes with PascalCase values,
    $actionType set
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "WebBriefSol" / "WebResearchAgent"
AGENT = ROOT / "agent.json"

VALID_SCOPES = {"Agent", "Llm", "Tool"}
LLM_PROTECTION_VALIDATORS = {"prompt_injection", "user_prompt_attacks"}
CONTENT_SAFETY_VALIDATORS = {"harmful_content", "intellectual_property"}


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def get_validator_type(g: dict) -> str | None:
    if g.get("$guardrailType") == "builtInValidator":
        return g.get("validatorType")
    return None


def check_structure(g: dict, idx: int) -> None:
    # id
    gid = g.get("id")
    if not isinstance(gid, str) or "-" not in gid:
        sys.exit(f"FAIL: guardrail[{idx}].id missing or malformed: {gid!r}")

    # action.$actionType
    action = g.get("action")
    if not isinstance(action, dict):
        sys.exit(f"FAIL: guardrail[{idx}].action must be an object, got {action!r}")
    if not action.get("$actionType"):
        sys.exit(f"FAIL: guardrail[{idx}].action.$actionType is missing or empty")

    # selector.scopes
    selector = g.get("selector")
    if not isinstance(selector, dict):
        sys.exit(f"FAIL: guardrail[{idx}].selector must be an object, got {selector!r}")
    scopes = selector.get("scopes")
    if not isinstance(scopes, list) or len(scopes) == 0:
        sys.exit(
            f"FAIL: guardrail[{idx}].selector.scopes must be a non-empty array, got {scopes!r}"
        )
    invalid = [s for s in scopes if s not in VALID_SCOPES]
    if invalid:
        sys.exit(
            f"FAIL: guardrail[{idx}].selector.scopes contains invalid values {invalid}. "
            f"Valid PascalCase values: {sorted(VALID_SCOPES)}"
        )


def main() -> None:
    agent = load(AGENT)

    guardrails = agent.get("guardrails")
    if not isinstance(guardrails, list) or len(guardrails) == 0:
        sys.exit(
            "FAIL: agent.json.guardrails must be a non-empty array, "
            f"got {type(guardrails).__name__}: {guardrails!r}"
        )
    print(f"OK: guardrails array has {len(guardrails)} entry/entries")

    if len(guardrails) < 2:
        sys.exit(
            f"FAIL: expected at least 2 guardrails (recommendation should add multiple), "
            f"got {len(guardrails)}"
        )
    print(f"OK: {len(guardrails)} >= 2 guardrails present")

    # Check structure of each guardrail
    for i, g in enumerate(guardrails):
        check_structure(g, i)
    print("OK: all guardrails have UUID id, $actionType, and PascalCase scopes")

    # Collect validator types
    validator_types = {get_validator_type(g) for g in guardrails} - {None}
    print(f"OK: validator types present: {sorted(validator_types)}")

    # Check for Llm-scoped protection
    llm_guards = [
        g for g in guardrails
        if get_validator_type(g) in LLM_PROTECTION_VALIDATORS
        and "Llm" in (g.get("selector") or {}).get("scopes", [])
    ]
    if not llm_guards:
        validators_found = [get_validator_type(g) for g in guardrails if get_validator_type(g)]
        sys.exit(
            f"FAIL: no Llm-scoped guardrail for prompt injection or user prompt attacks found. "
            f"Expected one of {sorted(LLM_PROTECTION_VALIDATORS)} with scope 'Llm'. "
            f"Validators found: {validators_found}"
        )
    llm_types = [get_validator_type(g) for g in llm_guards]
    print(f"OK: Llm-scoped protection guardrail(s) present: {llm_types}")

    # Check for content-safety guardrail
    content_guards = [
        g for g in guardrails
        if get_validator_type(g) in CONTENT_SAFETY_VALIDATORS
    ]
    if not content_guards:
        sys.exit(
            f"FAIL: no content-safety guardrail found. "
            f"Expected one of {sorted(CONTENT_SAFETY_VALIDATORS)}. "
            f"Validators found: {sorted(validator_types)}"
        )
    content_types = [get_validator_type(g) for g in content_guards]
    print(f"OK: content-safety guardrail(s) present: {content_types}")

    print("OK: guardrail recommendation check passed")


if __name__ == "__main__":
    main()
