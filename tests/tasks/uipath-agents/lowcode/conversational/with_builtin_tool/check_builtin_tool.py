#!/usr/bin/env python3
"""Conversational + built-in tool wiring check.

Walks `DocSol/DocAgent/resources/<Tool>/resource.json` and verifies
exactly one resource exists with:
  - `$resourceType: "tool"`
  - `type: "internal"` (built-in tool marker, per Critical Rule 20)
  - `properties.toolType: "analyze-attachments"` (the discriminator —
    fixed per built-in tool type, not invented)

Also asserts `inputSchema` / `outputSchema` exist on the tool resource
(every tool needs both — the agent invokes the tool with `inputSchema`
shaped args and consumes the `outputSchema` shape).

Conversational-specific: `agent.json` root must NOT contain a
`resources` field (Critical Rule 1 — resources live in their own files,
not inline in agent.json).
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "DocSol" / "DocAgent"
RESOURCES = ROOT / "resources"
AGENT = ROOT / "agent.json"

EXPECTED_TOOL_TYPE = "analyze-attachments"


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def main() -> None:
    if not AGENT.is_file():
        fail(f"Missing {AGENT}")

    with open(AGENT) as f:
        agent = json.load(f)

    if "resources" in agent:
        fail(
            "agent.json root contains a `resources` field — resources must live in "
            "resources/<Name>/resource.json files, not inline (Critical Rule 1)"
        )
    print("OK: agent.json root has no `resources` field (Rule 1)")

    if not RESOURCES.is_dir():
        fail(f"Missing resources/ directory at {RESOURCES}")

    matching = []
    for tool_dir in sorted(RESOURCES.iterdir()):
        rj = tool_dir / "resource.json"
        if not rj.is_file():
            continue
        with open(rj) as f:
            r = json.load(f)
        tool_type = (r.get("properties") or {}).get("toolType")
        if tool_type == EXPECTED_TOOL_TYPE:
            matching.append((tool_dir.name, r))

    if not matching:
        found = []
        for tool_dir in sorted(RESOURCES.iterdir()):
            rj = tool_dir / "resource.json"
            if rj.is_file():
                with open(rj) as f:
                    r = json.load(f)
                tt = (r.get("properties") or {}).get("toolType")
                found.append(f"{tool_dir.name} (toolType={tt!r})")
        fail(
            f"No resource with properties.toolType == {EXPECTED_TOOL_TYPE!r}. "
            f"Resources found: {found or '(none)'}"
        )

    if len(matching) > 1:
        fail(
            f"Multiple resources match properties.toolType == {EXPECTED_TOOL_TYPE!r}: "
            f"{[name for name, _ in matching]}"
        )

    name, r = matching[0]
    print(f"OK: found analyze-attachments tool resource at resources/{name}/")

    if r.get("$resourceType") != "tool":
        fail(f"$resourceType is {r.get('$resourceType')!r}, expected 'tool'")
    print('OK: $resourceType == "tool"')

    if r.get("type") != "internal":
        fail(
            f"type is {r.get('type')!r}, expected 'internal' (built-in tools use "
            f"type: 'internal' per Critical Rule 20)"
        )
    print('OK: type == "internal" (built-in tool)')

    if not r.get("inputSchema"):
        fail("resource.json missing inputSchema — every tool needs one")
    if not r.get("outputSchema"):
        fail("resource.json missing outputSchema — every tool needs one")
    print("OK: inputSchema and outputSchema both present")

    print("\nAll built-in tool wiring checks passed.")


if __name__ == "__main__":
    main()
