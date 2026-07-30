#!/usr/bin/env python3
"""Check exact, bounded, provider-neutral BPMN resource resolution."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def strings(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, str):
        found.add(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            found.add(str(key))
            found.update(strings(item))
    elif isinstance(value, list):
        for item in value:
            found.update(strings(item))
    elif value is not None:
        found.add(str(value))
    return found


def request_by_id(payload: dict[str, Any], request_id: str) -> dict[str, Any]:
    requests = payload.get("requests")
    if not isinstance(requests, list):
        fail("bindings.resolved.json must preserve the requests list")
    for request in requests:
        if isinstance(request, dict) and request.get("requestId") == request_id:
            return request
    fail(f"missing request {request_id}")


def require_tokens(value: Any, expected: set[str], label: str) -> None:
    actual = strings(value)
    missing = expected - actual
    if missing:
        fail(f"{label} is missing exact discovered values: {sorted(missing)}")


def read_calls() -> list[str]:
    path = Path("mocks/.calls.jsonl")
    if not path.is_file():
        fail("mock CLI call log is missing")
    calls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        calls.append(str(record.get("args", "")))
    return calls


def is_local_help_call(call: str) -> bool:
    """Help output is CLI introspection; it does not select or access a tenant."""
    return bool({"--help", "-h"} & set(call.split()))


def main() -> None:
    output = Path("bindings.resolved.json")
    if not output.is_file():
        fail("bindings.resolved.json is missing")
    try:
        payload = json.loads(output.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"bindings.resolved.json is not valid JSON: {exc}")
    if not isinstance(payload, dict):
        fail("bindings.resolved.json must contain an object")

    context = payload.get("context")
    if not isinstance(context, dict):
        fail("bindings.resolved.json must preserve the context object")
    require_tokens(context.get("profile"), {"resource-review"}, "requested profile")
    require_tokens(
        context.get("actual"),
        {
            "https://cloud.example.invalid",
            "automation-lab",
            "operations",
        },
        "verified active context",
    )

    process = request_by_id(payload, "process-risk-classifier")
    if str(process.get("status", "")).lower() != "resolved":
        fail("the exact Function process should be resolved")
    require_tokens(
        process.get("selected"),
        {"release-function-001", "folder-automation-001", "Function"},
        "process selection",
    )
    process_text = json.dumps(process)
    if "release-process-001" in process_text or "release-function-other-folder" in process_text:
        fail("process selection retained a wrong-type or wrong-folder candidate")

    queue = request_by_id(payload, "queue-review-items")
    if str(queue.get("status", "")).lower() != "resolved":
        fail("the exact folder-scoped queue should be resolved")
    require_tokens(
        queue.get("selected"),
        {"queue-review-001"},
        "queue selection",
    )
    if "queue-review-other-folder" in json.dumps(queue):
        fail("queue selection retained the same-named queue from another folder")

    connection = request_by_id(payload, "connection-neutral-records")
    status = str(connection.get("status", "")).lower()
    if "blocked" not in status and "ambiguous" not in status:
        fail("multiple enabled exact connections must remain blocked/ambiguous")
    if connection.get("selected") not in (None, {}, ""):
        fail("ambiguous connection must not have a selected resource")
    require_tokens(
        connection.get("viableCandidates"),
        {"conn-enabled-a", "conn-enabled-b"},
        "connection candidates",
    )
    connection_text = json.dumps(connection)
    if "conn-disabled" in connection_text or "conn-other-connector" in connection_text:
        fail("disabled or wrong-connector rows were treated as viable")
    if "connection-stale-000" in json.dumps(connection.get("selected")):
        fail("the stale connection id was retained")

    draft = request_by_id(payload, "draft-hitl-shell")
    if str(draft.get("mode", "")).lower() != "portable-draft":
        fail("intent-only HITL request must preserve portable-draft mode")
    draft_status = (
        str(draft.get("status", "")).lower().replace("_", "-").replace(" ", "-")
    )
    explicit_draft = draft_status == "draft" or (
        "draft" in draft_status
        and any(
            marker in draft_status
            for marker in ("portable", "unresolved", "non-runnable")
        )
    )
    if not explicit_draft:
        fail("intent-only HITL request must remain an explicit portable draft")
    if draft.get("selected") not in (None, {}, ""):
        fail("portable HITL draft must not select a live resource")
    if draft.get("viableCandidates") not in ([], None):
        fail("portable HITL draft must not retain live candidates")

    calls = read_calls()
    queue_calls = [call for call in calls if "or queues list" in call]
    if not any(
        "--folder-path Shared/Operations" in call
        or "--folder-path \"Shared/Operations\"" in call
        or "--folder-key folder-operations-001" in call
        for call in queue_calls
    ):
        fail("aggregate queue discovery was not confirmed in the requested folder")

    connection_calls = [
        call
        for call in calls
        if "is connections list uipath-neutral-records" in call
    ]
    if len(connection_calls) != 2:
        fail(
            "stale connection discovery must be attempted once and refreshed "
            f"once; observed {len(connection_calls)} calls"
        )
    if sum("--refresh" in call for call in connection_calls) != 1:
        fail("exactly one connection discovery call must use --refresh")
    if sum("maestro bpmn registry pull" in call for call in calls) != 1:
        fail("registry pull must run exactly once")

    required_gets = {
        "maestro bpmn registry get Orchestrator.StartJob",
        "maestro bpmn registry get Orchestrator.CreateQueueItem",
        "maestro bpmn registry get Intsvc.ActivityExecution",
        "maestro bpmn registry get Actions.HITL",
    }
    for required in required_gets:
        if not any(required in call for call in calls):
            fail(f"missing authoritative binding lookup: {required}")

    hitl_indices = [
        index
        for index, call in enumerate(calls)
        if "maestro bpmn registry get Actions.HITL" in call
    ]
    if len(hitl_indices) != 1:
        fail("portable HITL phase must retrieve its built-in contract exactly once")
    if "--profile" in calls[hitl_indices[0]]:
        fail("portable built-in lookup must not depend on a live login profile")

    live_calls = [
        (index, call)
        for index, call in enumerate(calls)
        if not is_local_help_call(call)
        if any(
            marker in call
            for marker in (
                "login status",
                "maestro bpmn registry pull",
                "maestro bpmn registry list",
                "maestro bpmn registry search",
                "maestro bpmn registry get Orchestrator.",
                "maestro bpmn registry get Intsvc.",
                "or queues list",
                "is connections list",
            )
        )
    ]
    if not live_calls:
        fail("live resource phase did not execute")
    if hitl_indices[0] > min(index for index, _ in live_calls):
        fail("tenant-dependent discovery began before the portable draft phase")

    for _, call in live_calls:
        if (
            "--profile resource-review" not in call
            and "--profile=resource-review" not in call
        ):
            fail(f"live command did not propagate the requested profile: {call}")

    print(
        "OK: named-profile live resolution, bounded ambiguity, and portable draft boundary"
    )


if __name__ == "__main__":
    main()
