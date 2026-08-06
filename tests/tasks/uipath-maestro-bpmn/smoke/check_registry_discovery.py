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
    payloads: list[object] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            payloads.append(json.loads(text))
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

    def contains_template(value: object, extension_type: str) -> bool:
        if isinstance(value, dict):
            normalized = {str(key).lower(): item for key, item in value.items()}
            if (
                normalized.get("extensiontype") == extension_type
                and isinstance(normalized.get("xmltemplate"), str)
                and normalized["xmltemplate"].strip()
            ):
                return True
            return any(contains_template(item, extension_type) for item in value.values())
        if isinstance(value, list):
            return any(contains_template(item, extension_type) for item in value)
        return False

    missing_templates = [
        f"{label} ({token})"
        for label, token in REQUIRED_TYPES.items()
        if not any(contains_template(payload, token) for payload in payloads)
    ]
    if missing_templates:
        sys.exit(
            "FAIL: registry evidence missing populated templates for required "
            f"extension types: {missing_templates}"
        )

    print(
        f"OK: registry-evidence covers populated templates for "
        f"{', '.join(REQUIRED_TYPES.values())} "
        f"across {len(files)} raw output files"
    )


if __name__ == "__main__":
    main()
