#!/usr/bin/env python3
"""External escalation (ActionCenter) resource check.

Validates:
  1. An escalation resource.json exists under FraudTriageAgent/resources/
     and declares:
       - $resourceType == "escalation"
       - id is a UUID-shaped non-empty string
       - name is a non-empty string
       - isEnabled is truthy
  2. The escalation has at least one channel wired to ActionCenter:
       - channels is a non-empty list
       - at least one channel has name == "ActionCenter"
         and type == "ActionCenter"

Note: The escalation resource.json format as documented in
agent-json-format.md does not show a `location` field on escalation
resources. The solution-vs-external distinction is encoded by where
the underlying ActionCenter app actually lives, which is not
observable from the resource.json alone pre-validate. This test
therefore verifies the authored shape and leaves end-to-end discovery
to a future test once RCS discovery lands.

The resource directory name is not prescribed (agent may use any
human-readable name), so we scan every resource.json under the
agent's resources/ directory.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "FraudSol" / "FraudTriageAgent"
RESOURCES_DIR = ROOT / "resources"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def find_escalation_resources() -> list:
    if not RESOURCES_DIR.is_dir():
        sys.exit(f"FAIL: {RESOURCES_DIR} does not exist — no resources/ directory")
    escalations = []
    for f in sorted(RESOURCES_DIR.rglob("resource.json")):
        data = load(f)
        if data.get("$resourceType") == "escalation":
            escalations.append((f, data))
    if not escalations:
        sys.exit(
            f"FAIL: no escalation resource found under {RESOURCES_DIR} — "
            'expected at least one resource.json with $resourceType="escalation"'
        )
    return escalations


def assert_escalation_header(path: Path, resource: dict) -> None:
    eid = resource.get("id")
    if not isinstance(eid, str) or "-" not in eid:
        sys.exit(f"FAIL: {path} escalation id missing or malformed: {eid!r}")
    name = resource.get("name")
    if not isinstance(name, str) or not name.strip():
        sys.exit(f"FAIL: {path} escalation name missing or empty: {name!r}")
    if not resource.get("isEnabled"):
        sys.exit(
            f"FAIL: {path} escalation isEnabled must be truthy, "
            f"got {resource.get('isEnabled')!r}"
        )
    print(f'OK: {path.parent.name} is $resourceType="escalation" (id={eid}, name={name!r}, isEnabled=true)')


def assert_actioncenter_channel(path: Path, resource: dict) -> None:
    channels = resource.get("channels")
    if not isinstance(channels, list) or not channels:
        sys.exit(f"FAIL: {path} escalation.channels must be a non-empty list, got {channels!r}")
    ac_channels = [
        c for c in channels
        if isinstance(c, dict)
        and c.get("name") == "ActionCenter"
        and c.get("type") == "ActionCenter"
    ]
    if not ac_channels:
        sys.exit(
            f"FAIL: {path} has no channel with name=='ActionCenter' and "
            f"type=='ActionCenter' in channels: {json.dumps(channels, indent=2)}"
        )
    print(f"OK: found {len(ac_channels)} ActionCenter channel(s) on {path.parent.name}")


def main() -> None:
    escalations = find_escalation_resources()
    for path, resource in escalations:
        assert_escalation_header(path, resource)
        assert_actioncenter_channel(path, resource)


if __name__ == "__main__":
    main()
