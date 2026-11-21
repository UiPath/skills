#!/usr/bin/env python3
"""HTTP Request built-in tool guard.

The HTTP Request built-in tool (`type: "internal"`, `properties.toolType:
"http-request"`) is available only to inline agents in a Flow. Agent Builder
has no UI for it, so it must never be authored on a standalone agent — even
though `uip agent validate` accepts the resource there.

Walks the workspace for every resource of that kind — matched on `type` and
`properties.toolType` alone, so a hand-written one without `$resourceType` is
still caught — and fails when one belongs to a standalone agent. An agent is inline when its folder sits directly
inside a Flow project (a folder holding a `*.flow` file); anything else is
standalone.

Passes when no such resource exists, or when every one found is on an inline
agent.
"""

import json
import os
import sys
from pathlib import Path

TOOL_TYPE = "http-request"
SKIP_DIRS = {"node_modules", ".git", ".agent-builder", "dist", "build"}


def is_http_request_tool(path: Path) -> bool:
    try:
        resource = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    if not isinstance(resource, dict):
        return False
    properties = resource.get("properties")
    return (
        resource.get("type") == "internal"
        and isinstance(properties, dict)
        and properties.get("toolType") == TOOL_TYPE
    )


def is_inline_agent(agent_dir: Path) -> bool:
    return any(agent_dir.parent.glob("*.flow"))


def main() -> None:
    root = Path(os.getcwd())
    standalone, inline = [], []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if "resource.json" not in filenames:
            continue
        resource = Path(dirpath) / "resource.json"
        # <agent>/resources/<folder>/resource.json
        if resource.parent.parent.name != "resources":
            continue
        if not is_http_request_tool(resource):
            continue
        agent_dir = resource.parent.parent.parent
        (inline if is_inline_agent(agent_dir) else standalone).append(
            resource.relative_to(root)
        )

    for path in inline:
        print(f"OK: HTTP Request tool on an inline agent: {path}")
    if standalone:
        for path in standalone:
            print(f"FAIL: HTTP Request tool on a standalone agent: {path}")
        sys.exit(
            "FAIL: the HTTP Request built-in tool is available only to inline "
            "agents in a Flow; it must not be authored on a standalone agent."
        )
    print("OK: no standalone agent carries the HTTP Request built-in tool")


if __name__ == "__main__":
    main()
