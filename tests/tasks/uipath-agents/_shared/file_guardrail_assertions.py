"""Assertions for low-code guardrails that inspect files (`detectionScope`).

Each helper exits the process with a `FAIL: ...` message on a failed
assertion and prints one `OK: ...` line when it passes.
"""

from __future__ import annotations

import sys
from typing import Any

JOB_ATTACHMENT_REF = "#/definitions/job-attachment"
DETECTION_SCOPE_VALUES = ("Text", "Files", "Both")


def has_job_attachment_field(schema: Any) -> bool:
    props = schema.get("properties") if isinstance(schema, dict) else None
    if not isinstance(props, dict):
        return False
    return any(
        isinstance(prop, dict)
        and (prop.get("$ref") == JOB_ATTACHMENT_REF or prop.get("x-uipath-resource-kind") == "JobAttachment")
        for prop in props.values()
    )


def require_job_attachment_input(agent: dict, what: str) -> None:
    schema = agent.get("inputSchema") or {}
    if not has_job_attachment_field(schema):
        props = list((schema.get("properties") or {}).keys())
        sys.exit(
            f"FAIL: inputSchema must declare a job-attachment field for the uploaded {what} "
            f'($ref "{JOB_ATTACHMENT_REF}"). Got properties: {props}'
        )
    print("OK: inputSchema declares a job-attachment input")


def require_detection_scope(params: list, expected: str, reason: str) -> None:
    param = next((p for p in params if isinstance(p, dict) and p.get("id") == "detectionScope"), None)
    if param is None:
        ids = [p.get("id") for p in params if isinstance(p, dict)]
        sys.exit(
            'FAIL: validatorParameters missing parameter with id == "detectionScope" — '
            f"without it the file contents are never inspected. Got ids: {ids}"
        )
    if param.get("$parameterType") != "enum":
        sys.exit(f'FAIL: detectionScope parameter.$parameterType must be "enum", got {param.get("$parameterType")!r}')
    value = param.get("value")
    if value not in DETECTION_SCOPE_VALUES:
        sys.exit(
            f"FAIL: detectionScope parameter.value must be one of {', '.join(DETECTION_SCOPE_VALUES)} "
            f"(exact case), got {value!r}"
        )
    if value != expected:
        sys.exit(f'FAIL: {reason}: detectionScope parameter.value must be "{expected}", got {value!r}')
    print(f'OK: detectionScope == "{expected}" (enum)')
