#!/usr/bin/env python3
"""LLM-as-judge guardrail on the Analyze Files tool, reading the file.

Validates that the agent authored, in the pre-seeded Contract Intake agent, a
builtInValidator guardrail for llm_as_judge that:
  - targets the Analyze Files tool: "Tool" in selector.scopes and
    selector.matchNames == ["Analyze Files"] (the tool resource name)
  - has an `enum` model parameter with a non-empty value
  - has a `text` guardrailText parameter with a non-empty value
  - has the file-support parameter {"$parameterType": "enum",
    "id": "detectionScope", "value": "Files"} — the user asked for the file
    contents, not the tool's text arguments
  - uses action.$actionType == "block", PascalCase scopes, a UUID id
  - left the fixture's Analyze Files tool resource in place with an empty
    guardrail.policies (autonomous agents keep guardrails at the root)
"""
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from _shared.file_guardrail_assertions import find_param, load_json, require_detection_scope  # noqa: E402

ROOT = Path(os.getcwd()) / "ContractIntakeSolution" / "ContractIntakeAgent"
AGENT = ROOT / "agent.json"
TOOL = ROOT / "resources" / "Analyze Files" / "resource.json"
VALID_SCOPES = {"Agent", "Llm", "Tool"}


def main() -> None:
    agent = load_json(AGENT)
    guardrails = agent.get("guardrails")
    if not isinstance(guardrails, list) or not guardrails:
        sys.exit(f"FAIL: agent.json.guardrails must be a non-empty array, got {guardrails!r}")
    print(f"OK: guardrails array has {len(guardrails)} entry/entries")

    judges = [
        g for g in guardrails
        if g.get("$guardrailType") == "builtInValidator" and g.get("validatorType") == "llm_as_judge"
    ]
    if not judges:
        types = [(g.get("$guardrailType"), g.get("validatorType")) for g in guardrails]
        sys.exit(f'FAIL: no guardrail with $guardrailType == "builtInValidator" and validatorType == "llm_as_judge". Got: {types}')
    g = judges[0]
    print('OK: found builtInValidator guardrail with validatorType == "llm_as_judge"')

    gid = g.get("id")
    try:
        uuid.UUID(str(gid))
    except ValueError:
        sys.exit(f"FAIL: guardrail id is not a UUID: {gid!r}")
    print(f"OK: guardrail id is a UUID: {gid}")

    action = g.get("action")
    if not isinstance(action, dict) or action.get("$actionType") != "block":
        sys.exit(f'FAIL: action.$actionType must be "block", got {action!r}')
    print('OK: action.$actionType == "block"')

    selector = g.get("selector")
    if not isinstance(selector, dict):
        sys.exit(f"FAIL: guardrail.selector must be an object, got {selector!r}")
    scopes = selector.get("scopes")
    if not isinstance(scopes, list) or not scopes:
        sys.exit(f"FAIL: selector.scopes must be a non-empty array, got {scopes!r}")
    invalid = [s for s in scopes if s not in VALID_SCOPES]
    if invalid:
        sys.exit(f"FAIL: selector.scopes has non-PascalCase or unknown values {invalid}; valid: {sorted(VALID_SCOPES)}")
    if "Tool" not in scopes:
        sys.exit(f'FAIL: the judge must run on the Analyze Files tool: "Tool" missing from selector.scopes {scopes}')
    match_names = selector.get("matchNames")
    if match_names != ["Analyze Files"]:
        sys.exit(f'FAIL: selector.matchNames must be exactly ["Analyze Files"] (the tool resource name), got {match_names!r}')
    print(f"OK: selector = scopes {scopes}, matchNames {match_names}")

    params = g.get("validatorParameters")
    if not isinstance(params, list):
        sys.exit(f"FAIL: validatorParameters must be an array, got {params!r}")

    model = find_param(params, "model")
    if model is None or model.get("$parameterType") != "enum" or not isinstance(model.get("value"), str) or not model["value"].strip():
        sys.exit(f'FAIL: validatorParameters needs an "enum" parameter id == "model" with a non-empty value, got {model!r}')
    print(f"OK: model = {model['value']} (enum)")

    rule = find_param(params, "guardrailText")
    if rule is None or rule.get("$parameterType") != "text" or not isinstance(rule.get("value"), str) or not rule["value"].strip():
        sys.exit(f'FAIL: validatorParameters needs a "text" parameter id == "guardrailText" with a non-empty value, got {rule!r}')
    print("OK: guardrailText present (text)")

    require_detection_scope(params, "Files", "the user asked to judge the file contents, not the tool's text arguments")

    tool = load_json(TOOL)
    if tool.get("properties", {}).get("toolType") != "analyze-attachments":
        sys.exit(f"FAIL: fixture tool resource was altered: properties.toolType = {tool.get('properties', {}).get('toolType')!r}")
    policies = (tool.get("guardrail") or {}).get("policies")
    if policies not in ([], None):
        sys.exit(f"FAIL: guardrail.policies on the Analyze Files resource must stay empty on an autonomous agent (guardrails live at the agent.json root), got {policies!r}")
    print("OK: Analyze Files resource intact, guardrail.policies empty")

    print("OK: LLM-as-judge file guardrail on Analyze Files is valid")


if __name__ == "__main__":
    main()
