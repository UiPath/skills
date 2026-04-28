#!/usr/bin/env python3
"""Solution escalation (ActionCenter) resource check.

Validates:
  1. resources/HumanReview/resource.json declares an escalation:
       - $resourceType == "escalation"
       - id is a UUID-shaped non-empty string
       - name is a non-empty string
       - isEnabled is truthy
  2. The escalation has at least one channel wired to ActionCenter:
       - channels is a non-empty list
       - at least one channel has name == "ActionCenter"
         and type == "ActionCenter"
  3. agent.json.inputSchema  == entry-points.json entryPoints[0].input
     agent.json.outputSchema == entry-points.json entryPoints[0].output
     (Critical Rule 4 — schema sync.)
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "ReviewSol" / "ModerationAgent"
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"
RESOURCE = ROOT / "resources" / "HumanReview" / "resource.json"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def assert_escalation_header(resource: dict) -> None:
    rtype = resource.get("$resourceType")
    if rtype != "escalation":
        sys.exit(f'FAIL: $resourceType should be "escalation", got {rtype!r}')
    eid = resource.get("id")
    if not isinstance(eid, str) or "-" not in eid:
        sys.exit(f"FAIL: escalation id missing or malformed: {eid!r}")
    name = resource.get("name")
    if not isinstance(name, str) or not name.strip():
        sys.exit(f"FAIL: escalation name missing or empty: {name!r}")
    if not resource.get("isEnabled"):
        sys.exit(f"FAIL: escalation isEnabled must be truthy, got {resource.get('isEnabled')!r}")
    print(f'OK: resource.json is $resourceType="escalation" (id={eid}, name={name!r}, isEnabled=true)')


def assert_actioncenter_channel(resource: dict) -> None:
    channels = resource.get("channels")
    if not isinstance(channels, list) or not channels:
        sys.exit(f"FAIL: escalation.channels must be a non-empty list, got {channels!r}")
    ac_channels = [
        c for c in channels
        if isinstance(c, dict)
        and c.get("name") == "ActionCenter"
        and c.get("type") == "ActionCenter"
    ]
    if not ac_channels:
        sys.exit(
            "FAIL: no channel with name=='ActionCenter' and type=='ActionCenter' "
            f"in channels: {json.dumps(channels, indent=2)}"
        )
    print(f"OK: found {len(ac_channels)} ActionCenter channel(s)")


def assert_schema_sync(agent: dict, entry: dict) -> None:
    entry_points = entry.get("entryPoints")
    if not isinstance(entry_points, list) or not entry_points:
        sys.exit("FAIL: entry-points.json has no entryPoints[0]")
    ep = entry_points[0]
    if agent.get("inputSchema") != ep.get("input"):
        sys.exit("FAIL: agent.json.inputSchema != entry-points.json entryPoints[0].input")
    if agent.get("outputSchema") != ep.get("output"):
        sys.exit("FAIL: agent.json.outputSchema != entry-points.json entryPoints[0].output")
    print("OK: inputSchema and outputSchema are in sync with entry-points.json")


def main() -> None:
    agent = load(AGENT)
    entry = load(ENTRY)
    resource = load(RESOURCE)

    assert_escalation_header(resource)
    assert_actioncenter_channel(resource)
    assert_schema_sync(agent, entry)


if __name__ == "__main__":
    main()
