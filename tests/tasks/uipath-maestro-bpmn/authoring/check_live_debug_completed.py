#!/usr/bin/env python3
"""Verify that the ScriptNormalizer live BPMN debug session completed.

The agent's saved response is the primary evidence.  If it omitted that file,
recover by running one bounded debug session against Alpha instead of grading
file-saving discipline.  This mirrors the existing BPMN live-debug evaluator.
"""

from __future__ import annotations

import json
import subprocess
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


def completed(payload) -> bool:
    return any(
        isinstance(status, str) and status.strip().lower() == "completed"
        for status in values_for_key(payload, "finalstatus")
    )


def recover_live_debug() -> bool:
    """Run at most one fresh debug session for the authored project."""
    candidates = sorted(
        {path.parent for path in Path(".").glob("**/ScriptNormalizer.bpmn")},
        key=lambda path: (len(path.parts), str(path)),
    )
    for project in candidates[:2]:
        try:
            result = subprocess.run(
                ["uip", "maestro", "bpmn", "debug", str(project), "--output", "json"],
                capture_output=True,
                text=True,
                timeout=300,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"note: live recovery could not debug {project}: {error}", file=sys.stderr)
            continue
        payload = parse_json_text(result.stdout)
        if result.returncode == 0 and payload is not None and completed(payload):
            print("OK: live recovery debug reached finalStatus Completed")
            return True
    return False


def parse_json_text(text: str):
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


def main() -> None:
    evidence = Path("debug-evidence/debug.json")
    if evidence.is_file():
        payload = parse_json(evidence)
        if payload is not None and completed(payload):
            print("OK: live BPMN debug reached finalStatus Completed")
            return
        print("note: saved debug evidence is absent or incomplete; recovering live", file=sys.stderr)
    if not recover_live_debug():
        fail("no completed BPMN debug response from saved evidence or live recovery")


if __name__ == "__main__":
    main()
