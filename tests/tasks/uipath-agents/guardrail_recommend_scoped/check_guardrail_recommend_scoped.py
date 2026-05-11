#!/usr/bin/env python3
"""Scoped guardrail recommendation check — Llm scope only.

Validates that scoped guardrail recommendation for Llm scope produces:
  - At least 1 guardrail in agent.json
  - All guardrails include "Llm" in selector.scopes
  - No guardrail has ONLY "Agent" or ONLY "Tool" in scopes (without "Llm")
  - Each guardrail has: UUID id, $actionType set, PascalCase scopes
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "WebBriefSol" / "WebResearchAgent"
AGENT = ROOT / "agent.json"

VALID_SCOPES = {"Agent", "Llm", "Tool"}


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def check_structure(g: dict, idx: int) -> None:
    gid = g.get("id")
    if not isinstance(gid, str) or "-" not in gid:
        sys.exit(f"FAIL: guardrail[{idx}].id missing or malformed: {gid!r}")

    action = g.get("action")
    if not isinstance(action, dict):
        sys.exit(f"FAIL: guardrail[{idx}].action must be an object, got {action!r}")
    if not action.get("$actionType"):
        sys.exit(f"FAIL: guardrail[{idx}].action.$actionType is missing or empty")

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

    for i, g in enumerate(guardrails):
        check_structure(g, i)
    print("OK: all guardrails have valid structure")

    # Every guardrail must include "Llm" in its scopes
    non_llm = []
    for i, g in enumerate(guardrails):
        scopes = (g.get("selector") or {}).get("scopes", [])
        if "Llm" not in scopes:
            validator = g.get("validatorType") or g.get("$guardrailType") or "unknown"
            non_llm.append((i, validator, scopes))

    if non_llm:
        details = "; ".join(
            f"guardrail[{i}] validator={v!r} scopes={s}" for i, v, s in non_llm
        )
        sys.exit(
            f"FAIL: {len(non_llm)} guardrail(s) do not include 'Llm' in scopes "
            f"(expected Llm-scope-only recommendations). {details}"
        )
    print("OK: all guardrails include 'Llm' in selector.scopes")

    validators = [
        g.get("validatorType") or g.get("$guardrailType")
        for g in guardrails
    ]
    print(f"OK: validators present: {validators}")
    print("OK: scoped guardrail recommendation check passed")


if __name__ == "__main__":
    main()
