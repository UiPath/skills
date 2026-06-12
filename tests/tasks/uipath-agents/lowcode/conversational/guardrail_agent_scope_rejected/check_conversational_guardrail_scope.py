#!/usr/bin/env python3
"""Conversational guardrail scope check (Rule 26).

Scans the conversational agent's `agent.json` root `guardrails[]` AND every
`resources/<Tool>/resource.json` → `guardrail.policies[]` and asserts that
no guardrail's `selector.scopes` contains `"Agent"` or `"Llm"`. Both
locations must be clean — the runtime build artifact (`uip agent migrate`)
inlines guardrails from the per-tool resource files, so writing a forbidden
scope in resource.json silently ships a runtime no-op even when agent.json
looks clean (or vice versa).

A clean PASS state is either:
  - all guardrails (in both locations) use only `selector.scopes: ["Tool"]`, OR
  - no guardrails were added at all (the skill restrained the agent)

A FAIL state is any guardrail whose scope list contains "Agent" or "Llm".
"""

import json
import os
import sys
from pathlib import Path

FORBIDDEN = {"Agent", "Llm"}
ROOT = Path(os.getcwd()) / "PiiGuardSol" / "ChatGuardAgent"
AGENT = ROOT / "agent.json"
RESOURCES = ROOT / "resources"


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        sys.exit(f"FAIL: Missing {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def scan_guardrails(guardrails: list, source_label: str) -> int:
    """Returns count of guardrails inspected; exits on forbidden scope."""
    violations = []
    for i, g in enumerate(guardrails):
        scopes = (g.get("selector") or {}).get("scopes") or []
        bad = sorted(set(scopes) & FORBIDDEN)
        if bad:
            violations.append((i, g.get("name", "?"), bad, scopes))
    if violations:
        lines = [f"FAIL: forbidden scope(s) found in {source_label}:"]
        for i, name, bad, all_scopes in violations:
            lines.append(f"  - [{i}] name={name!r} scopes={all_scopes} -> contains {bad}")
        sys.exit("\n".join(lines))
    return len(guardrails)


def main() -> None:
    agent = load(AGENT)

    root_guardrails = agent.get("guardrails") or []
    n_root = scan_guardrails(root_guardrails, "agent.json root guardrails[]")
    print(f"OK: agent.json root guardrails[] — {n_root} entries, no Agent/Llm scopes")

    total_tool_policies = 0
    tools_with_policies = 0
    if RESOURCES.is_dir():
        for tool_dir in sorted(RESOURCES.iterdir()):
            resource_json = tool_dir / "resource.json"
            if not resource_json.is_file():
                continue
            r = load(resource_json)
            policies = (r.get("guardrail") or {}).get("policies") or []
            if policies:
                tools_with_policies += 1
            n = scan_guardrails(policies, f"{resource_json.relative_to(ROOT)}")
            total_tool_policies += n
        print(
            f"OK: per-tool resource.json — {total_tool_policies} policies across "
            f"{tools_with_policies} tool(s), no Agent/Llm scopes"
        )
    else:
        print("OK: no resources/ directory — no per-tool guardrails to scan")

    print("\nAll guardrail scope checks passed (Rule 26).")


if __name__ == "__main__":
    main()
