#!/usr/bin/env python3
"""Verify a deterministic path-parameter value is wired into the flow.

Usage:
    check_path_param_value.py <flow_glob> <expected_value>

Looks for <expected_value> in either:
  - Any node's `inputs.detail.pathParameters` dict values (native connector path)
  - Any node's `inputs.detail.url` or `inputs.detail.endpoint` (managed HTTP path)

`inputs.detail` may be a dict (CLI-authored via `node configure`) or a
JSON-encoded string prefixed with `=jsonString:` (hand-authored fallback).
Both shapes are accepted; anything else produces a clear failure message
rather than a stack trace.
"""

from __future__ import annotations

import glob
import json
import sys
from typing import Any, NoReturn


_JSONSTRING_PREFIX = "=jsonString:"


def _fail(message: str) -> NoReturn:
    sys.exit(f"FAIL: {message}")


def _load_flow(pattern: str) -> tuple[str, dict[str, Any]]:
    matches = sorted(glob.glob(pattern, recursive=True))
    if not matches:
        _fail(f"No flow found for {pattern!r}")
    if len(matches) > 1:
        _fail(f"Multiple flows found for {pattern!r}: {matches}")
    with open(matches[0], encoding="utf-8") as flow_file:
        return matches[0], json.load(flow_file)


def _normalise_detail(raw: Any, node_id: str) -> dict[str, Any] | None:
    """Coerce inputs.detail to a dict, or return None with a printed warning.

    Accepts:
      - dict — returned as-is
      - str  — if prefixed with `=jsonString:`, parsed as JSON
      - None / missing — treated as empty dict
    """
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        if raw.startswith(_JSONSTRING_PREFIX):
            payload = raw[len(_JSONSTRING_PREFIX) :]
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError as exc:
                print(
                    f"WARN: node {node_id!r} inputs.detail is malformed =jsonString: {exc}",
                    file=sys.stderr,
                )
                return None
            if not isinstance(parsed, dict):
                print(
                    f"WARN: node {node_id!r} inputs.detail =jsonString payload is not an object",
                    file=sys.stderr,
                )
                return None
            return parsed
        print(
            f"WARN: node {node_id!r} inputs.detail is a bare string (expected dict or "
            f"'{_JSONSTRING_PREFIX}...' envelope)",
            file=sys.stderr,
        )
        return None
    print(
        f"WARN: node {node_id!r} inputs.detail has unexpected type {type(raw).__name__}",
        file=sys.stderr,
    )
    return None


def _search_detail(detail: dict[str, Any], needle: str, node_id: str) -> str | None:
    """Return a human-readable location string if needle is found, else None."""
    path_params = detail.get("pathParameters", {}) or {}
    if isinstance(path_params, dict):
        for value in path_params.values():
            if str(value) == needle:
                return f"pathParameters of node {node_id!r}"
    for key in ("url", "endpoint"):
        target = str(detail.get(key, "") or "")
        if needle in target:
            return f"{key} of node {node_id!r}"
    return None


def main() -> None:
    if len(sys.argv) != 3:
        _fail("usage: check_path_param_value.py <flow_glob> <expected_value>")

    flow_path, flow = _load_flow(sys.argv[1])
    needle = sys.argv[2]

    nodes = flow.get("nodes", []) or []
    malformed_nodes: list[str] = []

    for node in nodes:
        node_id = node.get("id", "<unknown>")
        raw_detail = (node.get("inputs", {}) or {}).get("detail")
        detail = _normalise_detail(raw_detail, node_id)
        if detail is None:
            malformed_nodes.append(node_id)
            continue
        location = _search_detail(detail, needle, node_id)
        if location is not None:
            print(f"OK: {needle!r} found in {location}")
            return

    if malformed_nodes:
        _fail(
            f"{needle!r} not found in any node's pathParameters, url, or endpoint. "
            f"Note: inputs.detail was malformed (non-dict, non-=jsonString:) on "
            f"node(s) {malformed_nodes}. "
            f"Hand-authored connector nodes must keep `inputs.detail` as a JSON object "
            f"with raw pathParameters/queryParameters/bodyParameters keys — do NOT "
            f"wrap the whole `detail` in a '=jsonString:' envelope (that prefix applies "
            f"only to `detail.configuration`). Flow: {flow_path}"
        )

    _fail(
        f"{needle!r} not found in any node's pathParameters, url, or endpoint "
        f"across {len(nodes)} node(s) in {flow_path}"
    )


if __name__ == "__main__":
    main()
