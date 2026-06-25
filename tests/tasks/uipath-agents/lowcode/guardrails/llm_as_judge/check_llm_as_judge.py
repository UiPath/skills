#!/usr/bin/env python3
"""LLM-as-judge built-in validator guardrail check.

Validates that the agent authored a builtInValidator guardrail for
llm_as_judge in agent.json with correct structure:

  - guardrails array exists and is non-empty
  - At least one guardrail has $guardrailType == "builtInValidator"
  - That guardrail has validatorType == "llm_as_judge"
  - validatorParameters contains a text parameter with id "guardrailText"
    whose value is a non-empty string
  - validatorParameters contains an enum parameter with id "model"
    whose value is a non-empty string
  - If threshold present, it uses the discrete 0/2/4/6 scale (number)
  - If positive/negative examples present, they use the text-list type
  - action.$actionType == "block"
  - selector.scopes uses PascalCase values
  - id is UUID-shaped
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "OnTopicGuardSol" / "OnTopicAgent"
AGENT = ROOT / "agent.json"

VALID_SCOPES = {"Agent", "Llm", "Tool"}
VALID_THRESHOLDS = {0, 2, 4, 6}


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

    judges = [
        g for g in guardrails
        if g.get("$guardrailType") == "builtInValidator"
        and g.get("validatorType") == "llm_as_judge"
    ]
    if not judges:
        types = [
            (g.get("$guardrailType"), g.get("validatorType"))
            for g in guardrails
        ]
        sys.exit(
            f"FAIL: no guardrail with $guardrailType == \"builtInValidator\" "
            f"and validatorType == \"llm_as_judge\". Got: {types}"
        )
    g = judges[0]
    print('OK: found builtInValidator guardrail with validatorType == "llm_as_judge"')

    gid = g.get("id")
    if not isinstance(gid, str) or "-" not in gid:
        sys.exit(f"FAIL: guardrail id missing or malformed: {gid!r}")
    print(f"OK: guardrail id is UUID-shaped: {gid}")

    action = g.get("action")
    if not isinstance(action, dict):
        sys.exit(f"FAIL: guardrail.action must be an object, got {action!r}")
    if action.get("$actionType") != "block":
        sys.exit(
            f'FAIL: guardrail.action.$actionType must be "block", '
            f"got {action.get('$actionType')!r}"
        )
    print('OK: action.$actionType == "block"')

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

    params = g.get("validatorParameters")
    if not isinstance(params, list):
        sys.exit(f"FAIL: validatorParameters must be an array, got {params!r}")

    text_param = find_param(params, "guardrailText")
    if text_param is None:
        ids = [p.get("id") for p in params if isinstance(p, dict)]
        sys.exit(
            f'FAIL: validatorParameters missing required parameter id "guardrailText". '
            f"Got ids: {ids}"
        )
    if text_param.get("$parameterType") != "text":
        sys.exit(
            f'FAIL: guardrailText parameter.$parameterType must be "text", '
            f"got {text_param.get('$parameterType')!r}"
        )
    text_value = text_param.get("value")
    if not isinstance(text_value, str) or not text_value.strip():
        sys.exit(f"FAIL: guardrailText parameter.value must be a non-empty string, got {text_value!r}")
    print(f"OK: guardrailText (text) is non-empty ({len(text_value)} chars)")

    model_param = find_param(params, "model")
    if model_param is None:
        ids = [p.get("id") for p in params if isinstance(p, dict)]
        sys.exit(
            f'FAIL: validatorParameters missing required parameter id "model". '
            f"Got ids: {ids}"
        )
    if model_param.get("$parameterType") != "enum":
        sys.exit(
            f'FAIL: model parameter.$parameterType must be "enum", '
            f"got {model_param.get('$parameterType')!r}"
        )
    model_value = model_param.get("value")
    if not isinstance(model_value, str) or not model_value.strip():
        sys.exit(f"FAIL: model parameter.value must be a non-empty string, got {model_value!r}")
    print(f"OK: model (enum) = {model_value}")

    threshold_param = find_param(params, "threshold")
    if threshold_param is not None:
        if threshold_param.get("$parameterType") != "number":
            sys.exit(
                f'FAIL: threshold parameter.$parameterType must be "number", '
                f"got {threshold_param.get('$parameterType')!r}"
            )
        threshold_value = threshold_param.get("value")
        if threshold_value not in VALID_THRESHOLDS:
            sys.exit(
                f"FAIL: threshold parameter.value must be one of {sorted(VALID_THRESHOLDS)} "
                f"(discrete 0/2/4/6 scale, Step=2, Min=0, Max=6). Got {threshold_value!r}"
            )
        print(f"OK: threshold (number) = {threshold_value}")

    for examples_id in ("positiveExamples", "negativeExamples"):
        ex_param = find_param(params, examples_id)
        if ex_param is None:
            continue
        if ex_param.get("$parameterType") != "text-list":
            sys.exit(
                f'FAIL: {examples_id} parameter.$parameterType must be "text-list", '
                f"got {ex_param.get('$parameterType')!r}"
            )
        ex_value = ex_param.get("value")
        if not isinstance(ex_value, list):
            sys.exit(f"FAIL: {examples_id} parameter.value must be an array, got {ex_value!r}")
        if len(ex_value) > 2:
            sys.exit(
                f"FAIL: {examples_id} parameter.value exceeds MaxItems=2 "
                f"(got {len(ex_value)} items)"
            )
        print(f"OK: {examples_id} (text-list) has {len(ex_value)} items")

    print("OK: llm_as_judge builtInValidator guardrail is valid")


if __name__ == "__main__":
    main()
