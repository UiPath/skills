#!/usr/bin/env python3
"""Conversational memory unavailability check.

Walks the agent project and asserts that no autonomous memory pattern
appears in the enabled state. Memory is Not Yet Available for
conversational agents per agent-definition.md § Not Yet Available.

Patterns scanned (any one triggers FAIL):
  - `"agentMemory": true` in any JSON file (process tool spec flag)
  - `"isAgentMemoryEnabled": true` in any JSON file (escalation channel)
  - `"agentMemoryEnabled": true` in any JSON file (eval set config)
  - `"uipath.agent.resource.memory.` substring (memory-space resource type)
  - Any resource directory under resources/ whose name suggests memory
    (case-insensitive contains "memory")

`"agentMemory": false` and the keys absent entirely both PASS — the
intent is that no memory artifact is ENABLED, not that the keys must be
omitted.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "MemorySol" / "MemoryAgent"

ENABLED_BOOL_KEYS = {
    "agentMemory",
    "isAgentMemoryEnabled",
    "agentMemoryEnabled",
}
RESOURCE_TYPE_SUBSTRING = "uipath.agent.resource.memory."


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def scan_json_value(value, key_path: str, file_label: str, violations: list) -> None:
    """Recursively walks JSON, flagging memory-enabled patterns."""
    if isinstance(value, dict):
        for k, v in value.items():
            sub_path = f"{key_path}.{k}" if key_path else k
            if k in ENABLED_BOOL_KEYS and v is True:
                violations.append(
                    f"{file_label}: {sub_path} == true (memory enabled — Not Yet Available for conversational)"
                )
            scan_json_value(v, sub_path, file_label, violations)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            scan_json_value(item, f"{key_path}[{i}]", file_label, violations)
    elif isinstance(value, str):
        if RESOURCE_TYPE_SUBSTRING in value:
            violations.append(
                f"{file_label}: {key_path} contains {RESOURCE_TYPE_SUBSTRING!r} (memory-space resource type)"
            )


def main() -> None:
    if not ROOT.is_dir():
        fail(f"Missing agent project at {ROOT}")

    violations: list = []

    for json_path in sorted(ROOT.rglob("*.json")):
        try:
            data = json.loads(json_path.read_text())
        except json.JSONDecodeError:
            continue
        scan_json_value(data, "", str(json_path.relative_to(ROOT)), violations)

    resources_dir = ROOT / "resources"
    if resources_dir.is_dir():
        for child in resources_dir.iterdir():
            if child.is_dir() and "memory" in child.name.lower():
                violations.append(
                    f"resources/{child.name}/: directory name suggests memory resource (Not Yet Available)"
                )

    if violations:
        lines = ["FAIL: autonomous memory pattern enabled on conversational agent:"]
        for v in violations:
            lines.append(f"  - {v}")
        sys.exit("\n".join(lines))

    print("OK: no memory artifacts enabled in agent.json, entry-points.json, or any resource.json")
    print("OK: no memory-named resource directories under resources/")
    print("\nAll memory-unavailability checks passed.")


if __name__ == "__main__":
    main()
