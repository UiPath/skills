#!/usr/bin/env python3
"""Advanced agent built-in tools check (agent-definition.md § Advanced Agents).

With `settings.advancedAgent.builtInTools` present, the runtime turns off every
tool missing from the map, keeps `read_file` on, and treats `task` as always on.
An agent that must not write files needs the full map with only the writing
tools off.

PASS requires ALL of:
  1. `settings.mode` == "advanced"
  2. `builtInTools` lists exactly the eight tools, each with a boolean `enabled`
  3. `write_file`, `edit_file`, `delete` are off; every other tool is on
  4. the root `guardrails` array is absent or empty
"""

import json
import os
import sys
from pathlib import Path

AGENT = Path(os.getcwd()) / "InvoiceSol" / "InvoiceReader" / "agent.json"

TOOLS = {"ls", "read_file", "write_file", "edit_file", "delete", "glob", "grep", "eval"}
OFF = {"write_file", "edit_file", "delete"}


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def main() -> None:
    agent = load(AGENT)
    settings = agent.get("settings") or {}

    if settings.get("mode") != "advanced":
        sys.exit(f"FAIL: settings.mode must be \"advanced\", got {settings.get('mode')!r}")
    print("OK: advanced mode")

    tools = (settings.get("advancedAgent") or {}).get("builtInTools")
    if not isinstance(tools, dict):
        sys.exit(f"FAIL: settings.advancedAgent.builtInTools must be an object, got {tools!r}")
    if set(tools) != TOOLS:
        sys.exit(f"FAIL: builtInTools must list exactly {sorted(TOOLS)}, got {sorted(tools)}")
    print("OK: full eight-tool map")

    for name, entry in tools.items():
        enabled = entry.get("enabled") if isinstance(entry, dict) else None
        if not isinstance(enabled, bool):
            sys.exit(f"FAIL: builtInTools.{name}.enabled must be a boolean, got {entry!r}")
        if enabled is (name in OFF):
            want = "off" if name in OFF else "on"
            sys.exit(f"FAIL: {name} must be {want}")
    print("OK: write_file, edit_file, delete off; the rest on")

    if agent.get("guardrails"):
        sys.exit("FAIL: advanced agents must not have guardrails")
    print("OK: no guardrails")

    print("PASS")


if __name__ == "__main__":
    main()
