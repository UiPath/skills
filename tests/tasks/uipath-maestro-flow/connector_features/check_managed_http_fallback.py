#!/usr/bin/env python3
"""Validate native connector use or task-specific managed HTTP fallback."""

from __future__ import annotations

import glob
import json
import sys
from typing import Any, NoReturn


def _fail(message: str) -> NoReturn:
    sys.exit(f"FAIL: {message}")


def _load_flow(pattern: str) -> dict[str, Any]:
    matches = sorted(glob.glob(pattern, recursive=True))
    if not matches:
        _fail(f"No flow found for {pattern!r}")
    if len(matches) > 1:
        _fail(f"Multiple flows found for {pattern!r}: {matches}")
    with open(matches[0], encoding="utf-8") as flow_file:
        return json.load(flow_file)


def _require_all(haystack: str, needles: list[str], label: str) -> None:
    missing = [needle for needle in needles if needle.lower() not in haystack]
    if missing:
        _fail(f"{label} missing expected evidence: {missing}")


def _http_fallback_text(flow: dict[str, Any]) -> str:
    http_nodes = [
        node
        for node in flow.get("nodes", [])
        if "core.action.http.v2" in str(node.get("type", "")).lower()
    ]
    if not http_nodes:
        _fail("Neither native connector nor managed HTTP fallback found")
    return json.dumps(http_nodes, sort_keys=True).lower()


def _check_generate_schema(flow: dict[str, Any]) -> None:
    http_text = _http_fallback_text(flow)
    _require_all(
        http_text,
        ["api.applicationinsights.io", "/query", "method", "post", "query", "timespan"],
        "Application Insights HTTP fallback",
    )
    _require_all(
        json.dumps(flow, sort_keys=True).lower(),
        ["schema", "columns"],
        "Generate-schema post-processing",
    )


def _check_path_params(flow: dict[str, Any]) -> None:
    _require_all(
        _http_fallback_text(flow),
        [
            "engce-00000",
            "method",
            "get",
        ],
        "Jira Get Issue path-params HTTP fallback",
    )


def _check_query_params(flow: dict[str, Any]) -> None:
    _require_all(
        _http_fallback_text(flow),
        [
            "tasks.googleapis.com/tasks/v1/lists",
            "/tasks",
            "method",
            "get",
            "showhidden",
            "true",
        ],
        "Google Tasks query-params HTTP fallback",
    )


def _check_enum(flow: dict[str, Any]) -> None:
    _require_all(
        _http_fallback_text(flow),
        [
            "gmail.googleapis.com",
            "method",
            "post",
            "importance",
            "medium",
        ],
        "Gmail send-mail enum HTTP fallback",
    )


def main() -> None:
    if len(sys.argv) != 4:
        _fail(
            "usage: check_managed_http_fallback.py <flow_glob> <connector_key> "
            "<generate_schema|path_params|query_params|enum>"
        )

    flow = _load_flow(sys.argv[1])
    connector_key = sys.argv[2]
    check_name = sys.argv[3]
    full_text = json.dumps(flow, sort_keys=True).lower()

    if connector_key.lower() in full_text:
        print(f"OK: native connector present ({connector_key})")
        return

    checks = {
        "generate_schema": _check_generate_schema,
        "path_params": _check_path_params,
        "query_params": _check_query_params,
        "enum": _check_enum,
    }
    check = checks.get(check_name)
    if check is None:
        _fail(f"Unknown check {check_name!r}")
    check(flow)
    print(f"OK: managed HTTP fallback has {check_name} evidence")


if __name__ == "__main__":
    main()
