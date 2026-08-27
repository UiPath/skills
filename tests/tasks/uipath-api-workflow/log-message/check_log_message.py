#!/usr/bin/env python3
"""Check native API Workflow Log Message authoring and validator compatibility."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def workflow_path() -> Path:
    matches = sorted(
        path
        for path in Path.cwd().rglob("Workflow.json")
        if "node_modules" not in path.parts and path != Path("Workflow.json")
    )
    if len(matches) != 1:
        fail(f"expected one project Workflow.json, found {len(matches)}")
    return matches[0]


def load_workflow() -> tuple[Path, dict[str, Any]]:
    path = workflow_path()
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read valid JSON from {path}: {exc}")
    if not isinstance(document, dict):
        fail("Workflow.json root must be an object")
    return path, document


def activities(value: Any) -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(child, dict) and isinstance(child.get("metadata"), dict):
                found.append((key, child))
            found.extend(activities(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(activities(child))
    return found


def check_structure(document: dict[str, Any]) -> list[str]:
    input_properties = (
        document.get("input", {})
        .get("schema", {})
        .get("document", {})
        .get("properties", {})
    )
    if input_properties.get("SomeString", {}).get("type") != "string":
        fail("workflow input SomeString must be declared as a string")

    all_activities = activities(document)
    log_nodes = [
        (key, body)
        for key, body in all_activities
        if body["metadata"].get("activityType") == "LogMessage"
    ]
    if len(log_nodes) != 4:
        fail(f"expected four native LogMessage activities, found {len(log_nodes)}")

    serialized = json.dumps(document)
    if "CustomLog" in serialized:
        fail("CustomLog substitute found")

    scripts: list[tuple[str, str]] = []
    expected_arguments = {
        '${{"$context":$context,"$workflow":$workflow,"$input":$input}}',
        '${{"$context":$context,"$workflow":$workflow,"$input":$input,}}',
    }
    for key, body in log_nodes:
        if not re.fullmatch(r"Log_Message_[1-9][0-9]*", key):
            fail(f"non-canonical Log Message key: {key}")
        metadata = body["metadata"]
        if metadata.get("fullName") != "LogMessage":
            fail(f"{key} fullName must be LogMessage")
        if not isinstance(metadata.get("displayName"), str) or not metadata["displayName"]:
            fail(f"{key} needs a non-empty displayName")
        if "export" in body:
            fail(f"{key} must not export an output")

        script = body.get("run", {}).get("script", {})
        if script.get("language") != "javascript":
            fail(f"{key} script language must be javascript")
        arguments = re.sub(r"\s+", "", str(script.get("arguments", "")))
        if arguments not in expected_arguments:
            fail(f"{key} does not use the standard arguments block")
        code = script.get("code")
        if not isinstance(code, str):
            fail(f"{key} needs string script code")
        if re.search(r"\breturn\b", code):
            fail(f"{key} must not return a value")
        match = re.fullmatch(r"\s*console\.(log|warn|error)\((.*)\)\s*;?\s*", code, re.DOTALL)
        if not match:
            fail(f"{key} must contain exactly one supported console call")
        scripts.append((match.group(1), code))

    required_static = {
        ("log", "Order received"),
        ("warn", "Manual review required"),
        ("error", "Order processing failed"),
    }
    for method, message in required_static:
        if not any(actual_method == method and message in code for actual_method, code in scripts):
            fail(f"missing {method} Log Message with text: {message}")

    if not any(
        method == "log" and "$workflow.input.SomeString" in code
        for method, code in scripts
    ):
        fail("dynamic Info message must read $workflow.input.SomeString")
    if any("$input.SomeString" in code for _, code in scripts):
        fail("workflow input incorrectly read through $input")

    for key, body in all_activities:
        if body["metadata"].get("activityType") == "JsInvoke":
            code = body.get("run", {}).get("script", {}).get("code", "")
            if "console." in code:
                fail(f"{key} substitutes JsInvoke for a native Log Message")

    return [key for key, _ in log_nodes]


def check_validation(path: Path, log_keys: list[str]) -> None:
    result = subprocess.run(
        ["uip", "api-workflow", "validate", str(path), "--output", "json"],
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        fail(f"validator did not return JSON: {exc}")

    if result.returncode == 0:
        if payload.get("Data", {}).get("Status") != "Valid":
            fail("validator exited successfully without Data.Status Valid")
        return

    instructions = str(payload.get("Instructions", ""))
    errors = [line.strip() for line in instructions.splitlines() if "- [error]" in line]
    if len(errors) != len(log_keys):
        fail(f"expected only {len(log_keys)} LogMessage validator errors, found {len(errors)}")
    for key in log_keys:
        expected_path = f"/{key}/metadata/activityType]"
        matching = [line for line in errors if expected_path in line]
        if len(matching) != 1 or "Unknown activityType 'LogMessage'" not in matching[0]:
            fail(f"validator returned a non-tolerated error for {key}")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"structure", "validation"}:
        fail("usage: check_log_message.py structure|validation")
    path, document = load_workflow()
    log_keys = check_structure(document)
    if sys.argv[1] == "validation":
        check_validation(path, log_keys)
    print(f"OK: native Log Message {sys.argv[1]} check passed")


if __name__ == "__main__":
    main()
