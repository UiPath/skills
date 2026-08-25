#!/usr/bin/env python3
"""Guardrail validation fix check — harmful_content threshold key mismatch.

Validates that the skill detected and fixed the misconfigured harmful_content guardrail:
  - A harmful_content builtInValidator exists in agent.json guardrails
  - harmfulContentEntities is a non-empty list
  - harmfulContentEntityThresholds keys exactly match harmfulContentEntities values
  - No extra or missing keys in the threshold dict
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "WebResearchBriefingSolution" / "WebResearchBriefingAgent"
AGENT = ROOT / "agent.json"


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

    # Find harmful_content guardrail
    harmful = [
        g for g in guardrails
        if g.get("$guardrailType") == "builtInValidator"
        and g.get("validatorType") == "harmful_content"
    ]
    if not harmful:
        types = [
            (g.get("$guardrailType"), g.get("validatorType"))
            for g in guardrails
        ]
        sys.exit(
            f"FAIL: no guardrail with validatorType == \"harmful_content\" found. "
            f"Got: {types}"
        )
    g = harmful[0]
    print('OK: found builtInValidator guardrail with validatorType == "harmful_content"')

    params = g.get("validatorParameters")
    if not isinstance(params, list):
        sys.exit(f"FAIL: validatorParameters must be an array, got {params!r}")

    # Check harmfulContentEntities
    entities_param = find_param(params, "harmfulContentEntities")
    if entities_param is None:
        ids = [p.get("id") for p in params if isinstance(p, dict)]
        sys.exit(
            f'FAIL: validatorParameters missing parameter with id == "harmfulContentEntities". '
            f"Got ids: {ids}"
        )
    entities_value = entities_param.get("value")
    if not isinstance(entities_value, list) or len(entities_value) == 0:
        sys.exit(
            f"FAIL: harmfulContentEntities parameter.value must be a non-empty array, "
            f"got {entities_value!r}"
        )
    entities_set = set(entities_value)
    print(f"OK: harmfulContentEntities = {entities_value}")

    # Check harmfulContentEntityThresholds
    thresholds_param = find_param(params, "harmfulContentEntityThresholds")
    if thresholds_param is None:
        ids = [p.get("id") for p in params if isinstance(p, dict)]
        sys.exit(
            f'FAIL: validatorParameters missing parameter with id == "harmfulContentEntityThresholds". '
            f"Got ids: {ids}"
        )
    thresholds_value = thresholds_param.get("value")
    if not isinstance(thresholds_value, dict):
        sys.exit(
            f"FAIL: harmfulContentEntityThresholds parameter.value must be an object, "
            f"got {thresholds_value!r}"
        )
    threshold_keys = set(thresholds_value.keys())

    # Keys must exactly match entities
    extra_keys = threshold_keys - entities_set
    missing_keys = entities_set - threshold_keys

    if extra_keys:
        sys.exit(
            f"FAIL: harmfulContentEntityThresholds has extra keys not in harmfulContentEntities: "
            f"{sorted(extra_keys)}. "
            f"Threshold keys: {sorted(threshold_keys)}, "
            f"Entities: {sorted(entities_set)}"
        )
    if missing_keys:
        sys.exit(
            f"FAIL: harmfulContentEntityThresholds is missing keys that are in harmfulContentEntities: "
            f"{sorted(missing_keys)}. "
            f"Threshold keys: {sorted(threshold_keys)}, "
            f"Entities: {sorted(entities_set)}"
        )

    print(
        f"OK: harmfulContentEntityThresholds keys exactly match harmfulContentEntities: "
        f"{sorted(threshold_keys)}"
    )
    print("OK: harmful_content guardrail validation fix check passed")


if __name__ == "__main__":
    main()
