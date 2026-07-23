#!/usr/bin/env python3
"""Verify raw registry JSON covers the RPA-job and receive-message types.

The agent saves the raw CLI output of its registry commands into
`registry-evidence/`. This checker parses only that raw output, so the task
cannot pass by writing a prose summary of the expected extension types — the
registry commands must actually have been run and their output preserved.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Expected extension types the discovery loop must surface in raw registry
# output. Not disclosed to the agent in the prompt — it must discover them.
REQUIRED_TYPES = {
    "RPA job": "Orchestrator.StartJob",
    "receive internal message": "Maestro.ReceiveMessageEvent",
}


def main() -> None:
    evidence = Path("registry-evidence")
    if not evidence.is_dir():
        sys.exit("FAIL: registry-evidence directory missing")

    files = [p for p in evidence.rglob("*.json") if p.is_file()]
    if not files:
        sys.exit("FAIL: registry-evidence directory has no raw JSON files")

    body_parts: list[str] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            json.loads(text)
            body_parts.append(text)
        except json.JSONDecodeError as exc:
            sys.exit(f"FAIL: registry evidence file is not valid JSON: {path}: {exc}")
        except OSError as exc:
            sys.exit(f"FAIL: could not read {path}: {exc}")
    body = "\n".join(body_parts)

    missing = [
        f"{label} ({token})"
        for label, token in REQUIRED_TYPES.items()
        if token not in body
    ]
    if missing:
        sys.exit(f"FAIL: registry evidence missing required extension types: {missing}")

    print(
        f"OK: registry-evidence covers {', '.join(REQUIRED_TYPES.values())} "
        f"across {len(files)} raw output files"
    )


if __name__ == "__main__":
    main()
