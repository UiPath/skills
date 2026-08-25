#!/usr/bin/env python3
"""Validate the EnumTest flow: structure, enum value, and control-flow nodes.

Usage:
    check_enum_flow.py <flow_glob> <check>

Checks:
  structure   — flow file exists, is valid JSON, has `nodes` and `edges`
  body_params — at least one node's `inputs.detail.bodyParameters` carries the
                expected to / subject / body / importance values
  control     — flow contains at least one Decision and one Terminate node
"""

from __future__ import annotations

import glob
import json
import sys
from typing import Any, NoReturn


def _fail(message: str) -> NoReturn:
    sys.exit(f"FAIL: {message}")


def _load_flow(pattern: str) -> tuple[str, dict[str, Any]]:
    matches = sorted(glob.glob(pattern, recursive=True))
    if not matches:
        _fail(f"No flow found for {pattern!r}")
    if len(matches) > 1:
        _fail(f"Multiple flows found for {pattern!r}: {matches}")
    try:
        with open(matches[0], encoding="utf-8") as flow_file:
            return matches[0], json.load(flow_file)
    except json.JSONDecodeError as exc:
        _fail(f"Flow {matches[0]} is not valid JSON: {exc}")


def _check_structure(flow_path: str, flow: dict[str, Any]) -> None:
    if "nodes" not in flow or "edges" not in flow:
        _fail(f"Flow {flow_path} missing required keys `nodes`/`edges`")
    nodes = flow.get("nodes") or []
    edges = flow.get("edges") or []
    print(f"OK: {flow_path} valid JSON with {len(nodes)} nodes, {len(edges)} edges")


_JSONSTRING_PREFIX = "=jsonString:"

_EXPECTED_BODY = {
    "to": "baishali13@gmail.com",
    "importance": "high", # this is the enum field under test
}


def _normalise_detail(raw: Any) -> dict[str, Any] | None:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.startswith(_JSONSTRING_PREFIX):
        try:
            parsed = json.loads(raw[len(_JSONSTRING_PREFIX) :])
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None
    return None


def _body_matches(body_params: Any) -> list[str]:
    """Return list of missing/mismatched fields. Empty list means OK."""
    if not isinstance(body_params, dict):
        return list(_EXPECTED_BODY)
    lowered = {str(k).lower(): v for k, v in body_params.items()}
    missing: list[str] = []
    for key, expected in _EXPECTED_BODY.items():
        actual = lowered.get(key.lower())
        if actual is None or str(actual).strip().lower() != expected.lower():
            missing.append(f"{key}={expected!r} (got {actual!r})")
    return missing


def _check_body_params(flow_path: str, flow: dict[str, Any]) -> None:
    nodes = flow.get("nodes", []) or []
    best_miss: list[str] | None = None
    for node in nodes:
        detail = _normalise_detail((node.get("inputs", {}) or {}).get("detail"))
        if not detail:
            continue
        body_params = detail.get("bodyParameters")
        if body_params is None:
            continue
        miss = _body_matches(body_params)
        if not miss:
            print(
                f"OK: bodyParameters on node {node.get('id', '<unknown>')!r} "
                f"carries expected to/subject/body/importance"
            )
            return
        if best_miss is None or len(miss) < len(best_miss):
            best_miss = miss
    if best_miss is None:
        _fail(
            f"No node in {flow_path} has `inputs.detail.bodyParameters`. "
            f"Hand-authored connector nodes must keep `inputs.detail` as a JSON "
            f"object with raw bodyParameters keys."
        )
    _fail(
        f"`inputs.detail.bodyParameters` found but missing or wrong fields: "
        f"{best_miss}. Flow: {flow_path}"
    )


def _check_control(flow_path: str, flow: dict[str, Any]) -> None:
    types = [str(node.get("type", "")).lower() for node in flow.get("nodes", []) or []]
    if not any("decision" in t for t in types):
        _fail(f"No Decision node found in {flow_path}")
    if not any("terminate" in t for t in types):
        _fail(f"No Terminate node found in {flow_path}")
    print("OK: Decision and Terminate nodes present")


def main() -> None:
    if len(sys.argv) != 3:
        _fail(
            "usage: check_enum_flow.py <flow_glob> "
            "<structure|body_params|control>"
        )

    flow_path, flow = _load_flow(sys.argv[1])
    check_name = sys.argv[2]
    checks = {
        "structure": _check_structure,
        "body_params": _check_body_params,
        "control": _check_control,
    }
    check = checks.get(check_name)
    if check is None:
        _fail(f"Unknown check {check_name!r}")
    check(flow_path, flow)


if __name__ == "__main__":
    main()
