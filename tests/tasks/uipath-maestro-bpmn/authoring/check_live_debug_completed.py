#!/usr/bin/env python3
"""Verify that the ScriptNormalizer live BPMN debug session completed."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def parse_json(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for index, line in enumerate(text.splitlines()):
            if line.lstrip().startswith(("{", "[")):
                try:
                    return json.loads("\n".join(text.splitlines()[index:]))
                except json.JSONDecodeError:
                    continue
    return None


def values_for_key(value, wanted: str):
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and key.lower() == wanted:
                yield child
            yield from values_for_key(child, wanted)
    elif isinstance(value, list):
        for child in value:
            yield from values_for_key(child, wanted)


def main() -> None:
    evidence = Path("debug-evidence/debug.json")
    if not evidence.is_file():
        fail("missing debug-evidence/debug.json; save the raw BPMN debug response")
    payload = parse_json(evidence)
    if payload is None:
        fail("debug-evidence/debug.json is not parseable JSON")
    if not any(
        isinstance(status, str) and status.strip().lower() == "completed"
        for status in values_for_key(payload, "finalstatus")
    ):
        fail("debug evidence does not contain finalStatus == Completed")
    print("OK: live BPMN debug reached finalStatus Completed")


if __name__ == "__main__":
    main()
