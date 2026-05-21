#!/usr/bin/env python3
"""Verify raw registry JSON covers agent, queue, and connector wrappers.

The agent stores raw CLI output locally. This checker intentionally ignores
agent-written prose so the task cannot pass by summarizing expected wrapper
names without preserving registry command output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_WRAPPERS = {
    "agent": ("Orchestrator.StartAgentJob",),
    "queue": ("Orchestrator.CreateQueueItem",),
    "connector": ("Intsvc.",),
}

# Patterns that would indicate concrete private values (not documented field
# names). These show up only when the agent invents or pastes secret-looking
# data. Field names like connectionKey on their own are fine in registry docs.
PRIVATE_VALUE_HINTS = (
    "Bearer ey",
    "Authorization: Bearer ",
    "password:",
    "PASSWORD=",
)


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

    missing: list[str] = []
    for label, tokens in REQUIRED_WRAPPERS.items():
        if not any(token in body for token in tokens):
            missing.append(f"{label} (expected one of {tokens})")
    if missing:
        sys.exit(f"FAIL: registry evidence missing wrapper coverage: {missing}")

    leaks = [token for token in PRIVATE_VALUE_HINTS if token in body]
    if leaks:
        sys.exit(f"FAIL: registry evidence contains concrete private values: {leaks}")

    print(
        f"OK: registry-evidence covers agent/queue/connector wrappers across {len(files)} files"
    )


if __name__ == "__main__":
    main()
