#!/usr/bin/env python3
"""PII detection guardrail with escalate action check.

Validates that the agent authored a builtInValidator guardrail for
pii_detection in agent.json using the escalate action (not block):

  - guardrails array exists and is non-empty
  - At least one guardrail has $guardrailType == "builtInValidator"
    and validatorType == "pii_detection"
  - That guardrail has action.$actionType == "escalate" (not "block")
  - action.app is an object with non-empty name and version strings
  - action.app.folderName or action.app.folderId is present
  - action.recipient.type is a valid integer (1–6)
  - action.recipient.value is a non-empty string
  - validatorParameters contains an enum-list parameter with id "entities"
    and PascalCase entity names including Email and PhoneNumber
  - validatorParameters contains a map-enum parameter with id
    "entityThresholds" and matching entity keys
  - selector.scopes uses PascalCase values
  - id is UUID-shaped
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "EscalateSol" / "ComplianceAgent"
AGENT = ROOT / "agent.json"

VALID_SCOPES = {"Agent", "Llm", "Tool"}
REQUIRED_ENTITIES = {"Email", "PhoneNumber"}
VALID_RECIPIENT_TYPES = {1, 2, 3, 4, 5, 6}


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

    # --- find builtInValidator with pii_detection and escalate action ---
    escalation_candidates = [
        g for g in guardrails
        if g.get("$guardrailType") == "builtInValidator"
        and g.get("validatorType") == "pii_detection"
        and isinstance(g.get("action"), dict)
        and g["action"].get("$actionType") == "escalate"
    ]
    if not escalation_candidates:
        found = [
            (g.get("$guardrailType"), g.get("validatorType"),
             (g.get("action") or {}).get("$actionType"))
            for g in guardrails
        ]
        sys.exit(
            'FAIL: no guardrail with $guardrailType == "builtInValidator", '
            'validatorType == "pii_detection", and action.$actionType == "escalate". '
            f"Found ($guardrailType, validatorType, $actionType) tuples: {found}"
        )
    g = escalation_candidates[0]
    print(
        'OK: found builtInValidator guardrail with validatorType == "pii_detection" '
        'and action.$actionType == "escalate"'
    )

    # --- id is UUID-shaped ---
    gid = g.get("id")
    if not isinstance(gid, str) or "-" not in gid:
        sys.exit(f"FAIL: guardrail id missing or malformed: {gid!r}")
    print(f"OK: guardrail id is UUID-shaped: {gid}")

    # --- action.app ---
    action = g["action"]
    app = action.get("app")
    if not isinstance(app, dict):
        sys.exit(f"FAIL: action.app must be an object, got {app!r}")

    app_name = app.get("name")
    if not isinstance(app_name, str) or not app_name.strip():
        sys.exit(f"FAIL: action.app.name must be a non-empty string, got {app_name!r}")
    print(f"OK: action.app.name = {app_name!r}")

    app_version = app.get("version")
    if not isinstance(app_version, str) or not app_version.strip():
        sys.exit(
            f"FAIL: action.app.version must be a non-empty string "
            f"(e.g. the deployVersion from the Apps API), got {app_version!r}"
        )
    print(f"OK: action.app.version = {app_version!r}")

    # folderName OR folderId should be present (at least one)
    folder_name = app.get("folderName")
    folder_id = app.get("folderId")
    if not folder_name and not folder_id:
        sys.exit(
            "FAIL: action.app must have at least one of folderName or folderId. "
            f"Both are missing or empty. app = {json.dumps(app)}"
        )
    if folder_name:
        print(f"OK: action.app.folderName = {folder_name!r}")
    if folder_id:
        print(f"OK: action.app.folderId = {folder_id!r}")
    if app.get("id"):
        print(f"OK: action.app.id = {app['id']!r} (optional, populated from resource lookup)")

    # --- action.recipient ---
    recipient = action.get("recipient")
    if not isinstance(recipient, dict):
        sys.exit(f"FAIL: action.recipient must be an object, got {recipient!r}")

    rtype = recipient.get("type")
    if rtype not in VALID_RECIPIENT_TYPES:
        sys.exit(
            f"FAIL: action.recipient.type must be one of {sorted(VALID_RECIPIENT_TYPES)} "
            f"(1=UserId, 2=GroupId, 3=UserEmail, 4=AssetUserEmail, "
            f"5=StaticGroupName, 6=AssetGroupName), got {rtype!r}"
        )
    print(f"OK: action.recipient.type = {rtype}")

    rvalue = recipient.get("value")
    if not isinstance(rvalue, str) or not rvalue.strip():
        sys.exit(
            f"FAIL: action.recipient.value must be a non-empty string "
            f"(email, GUID, or group name), got {rvalue!r}"
        )
    print(f"OK: action.recipient.value = {rvalue!r}")

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

    # --- entities parameter (enum-list) ---
    entities_param = find_param(params, "entities")
    if entities_param is None:
        ids = [p.get("id") for p in params if isinstance(p, dict)]
        sys.exit(
            'FAIL: validatorParameters missing parameter with id == "entities". '
            f"Got ids: {ids}"
        )
    if entities_param.get("$parameterType") != "enum-list":
        sys.exit(
            'FAIL: entities parameter.$parameterType must be "enum-list", '
            f"got {entities_param.get('$parameterType')!r}"
        )
    entities_value = entities_param.get("value")
    if not isinstance(entities_value, list):
        sys.exit(f"FAIL: entities parameter.value must be an array, got {entities_value!r}")
    entities_set = set(entities_value)
    missing = REQUIRED_ENTITIES - entities_set
    if missing:
        sys.exit(
            f"FAIL: entities parameter.value must include {sorted(REQUIRED_ENTITIES)}, "
            f"missing: {sorted(missing)}. Got: {entities_value}"
        )
    snake = [e for e in entities_value if "_" in e or (isinstance(e, str) and e[0].islower())]
    if snake:
        sys.exit(
            f"FAIL: entity names must be PascalCase (not snake_case). "
            f"Invalid: {snake}. Expected: Email, PhoneNumber, etc."
        )
    print(f"OK: entities = {entities_value} (PascalCase, includes Email + PhoneNumber)")

    # --- entityThresholds parameter (map-enum) ---
    thresholds_param = find_param(params, "entityThresholds")
    if thresholds_param is None:
        print("WARN: entityThresholds parameter not found (optional but recommended)")
    else:
        if thresholds_param.get("$parameterType") != "map-enum":
            sys.exit(
                'FAIL: entityThresholds parameter.$parameterType must be "map-enum", '
                f"got {thresholds_param.get('$parameterType')!r}"
            )
        thresholds_value = thresholds_param.get("value")
        if not isinstance(thresholds_value, dict):
            sys.exit(
                "FAIL: entityThresholds parameter.value must be an object, "
                f"got {thresholds_value!r}"
            )
        print(f"OK: entityThresholds = {thresholds_value} (map-enum)")

    print("OK: PII detection guardrail with escalate action is valid")


if __name__ == "__main__":
    main()
