#!/usr/bin/env python3
"""User prompt attacks guardrail check (low-code builtInValidator).

Validates that the agent authored a builtInValidator guardrail for
user_prompt_attacks in agent.json with correct scope constraints:

  - guardrails array exists and is non-empty
  - At least one guardrail has $guardrailType == "builtInValidator"
    and validatorType == "user_prompt_attacks"
  - selector.scopes is exactly ["Llm"] — NOT Agent or Tool
    (user_prompt_attacks is Llm-only, PreExecution-only — anti-pattern 3)
  - validatorParameters is empty OR contains only parameters the live
    guardrail catalog declares for user_prompt_attacks (all its parameters
    are optional today — e.g. appliesTo, added by AL-594 — and a future
    non-breaking catalog addition must not break this test)
  - action.$actionType == "block"
  - id is UUID-shaped

This test specifically validates the most dangerous anti-pattern:
adding user_prompt_attacks to Agent or Tool scope (which is invalid).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "UPASol" / "UPAAgent"
AGENT = ROOT / "agent.json"


def catalog_parameter_ids(validator: str) -> set | None:
    """Parameter ids the live catalog declares for `validator`, or None if
    the catalog is unreachable (not logged in, CLI missing, timeout)."""
    try:
        proc = subprocess.run(
            ["uip", "agent", "guardrails", "list", "--output", "json"],
            capture_output=True, text=True, timeout=20,
        )
        data = json.loads(proc.stdout)
        entries = [e for e in data.get("Data", []) if e.get("Validator") == validator]
        if proc.returncode != 0 or not entries:
            return None
        return {p["Id"] for e in entries for p in e.get("Parameters", []) if "Id" in p}
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, TypeError):
        return None


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

    # --- validatorParameters: empty, or only catalog-declared parameters ---
    # All user_prompt_attacks parameters are optional (appliesTo since AL-594),
    # so both shapes are correct. Validating against the live catalog instead
    # of a hardcoded list keeps future non-breaking catalog additions from
    # failing this test.
    params = g.get("validatorParameters", [])
    if not isinstance(params, list):
        sys.exit(f"FAIL: validatorParameters must be an array, got {params!r}")
    if len(params) == 0:
        print("OK: validatorParameters is empty (all parameters are optional)")
    else:
        ids = []
        for p in params:
            if not isinstance(p, dict) or not isinstance(p.get("id"), str) or "value" not in p:
                sys.exit(
                    "FAIL: each validatorParameters entry must be an object "
                    f"with a string 'id' and a 'value', got {p!r}"
                )
            ids.append(p["id"])
        if len(ids) != len(set(ids)):
            sys.exit(f"FAIL: duplicate validatorParameters ids: {ids}")
        declared = catalog_parameter_ids("user_prompt_attacks")
        if declared is None:
            print(
                "WARN: guardrail catalog unreachable — skipping the "
                f"declared-parameter cross-check for ids {ids}"
            )
        else:
            unknown = [i for i in ids if i not in declared]
            if unknown:
                sys.exit(
                    f"FAIL: validatorParameters ids {unknown} are not declared "
                    f"for user_prompt_attacks in the guardrail catalog "
                    f"(declared: {sorted(declared)})"
                )
            print(f"OK: validatorParameters {ids} are all catalog-declared")

    print("OK: user prompt attacks guardrail is valid with Llm-only scope")


if __name__ == "__main__":
    main()
