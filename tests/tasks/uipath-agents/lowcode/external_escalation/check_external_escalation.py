#!/usr/bin/env python3
"""External escalation (ActionCenter) resource check.

Validates that the agent authored an escalation wired to the deployed
external "FraudEscalation" Action Center app, regardless of what it named
the escalation resource folder:

  1. Some resources/<Name>/resource.json under FraudTriageAgent declares an
     escalation:
       - $resourceType == "escalation"
       - id is a UUID-shaped non-empty string
       - name is a non-empty string
       - isEnabled is truthy
  2. The escalation has at least one channel wired to ActionCenter and
     bound to the deployed app named "FraudEscalation":
       - type == "actionCenter" with a non-empty name
       - properties.appName == "FraudEscalation"

The escalation resource folder name is the agent's choice (the prompt names
the *app* "FraudEscalation", not the resource), so this check locates the
escalation by content and verifies the app binding — it does NOT assume a
specific folder name.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "FraudSol" / "FraudTriageAgent"
RESOURCES_DIR = ROOT / "resources"
EXPECTED_APP_NAME = "FraudEscalation"


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def find_escalation() -> tuple[Path, dict]:
    if not RESOURCES_DIR.is_dir():
        sys.exit(f"FAIL: no resources/ directory under {ROOT}")
    candidates = sorted(RESOURCES_DIR.glob("*/resource.json"))
    if not candidates:
        sys.exit(f"FAIL: no resources/*/resource.json found under {RESOURCES_DIR}")
    escalations = [
        (p, d) for p in candidates
        for d in [load(p)]
        if d.get("$resourceType") == "escalation"
    ]
    if not escalations:
        found = ", ".join(sorted({load(p).get("$resourceType", "?") for p in candidates}))
        sys.exit(
            f'FAIL: no resource.json with $resourceType=="escalation" under {RESOURCES_DIR} '
            f"(found resource types: {found})"
        )
    return escalations[0]


def assert_escalation_header(path: Path, resource: dict) -> None:
    eid = resource.get("id")
    if not isinstance(eid, str) or "-" not in eid:
        sys.exit(f"FAIL: escalation id missing or malformed at {path}: {eid!r}")
    name = resource.get("name")
    if not isinstance(name, str) or not name.strip():
        sys.exit(f"FAIL: escalation name missing or empty at {path}: {name!r}")
    if not resource.get("isEnabled"):
        sys.exit(f"FAIL: escalation isEnabled must be truthy at {path}, got {resource.get('isEnabled')!r}")
    print(f'OK: {path.parent.name}/resource.json is $resourceType="escalation" (id={eid}, name={name!r}, isEnabled=true)')


def assert_actioncenter_channel_bound(path: Path, resource: dict) -> None:
    channels = resource.get("channels")
    if not isinstance(channels, list) or not channels:
        sys.exit(f"FAIL: escalation.channels must be a non-empty list at {path}, got {channels!r}")
    ac_channels = [
        c for c in channels
        if isinstance(c, dict)
        and c.get("type") == "actionCenter"
        and isinstance(c.get("name"), str)
        and c["name"].strip()
    ]
    if not ac_channels:
        sys.exit(
            'FAIL: no channel with type=="actionCenter" and non-empty name '
            f"in {path}: {json.dumps(channels, indent=2)}"
        )
    bound = [c for c in ac_channels if (c.get("properties") or {}).get("appName") == EXPECTED_APP_NAME]
    if not bound:
        got = [(c.get("properties") or {}).get("appName") for c in ac_channels]
        sys.exit(
            f"FAIL: no actionCenter channel is bound to the deployed app {EXPECTED_APP_NAME!r} "
            f"(properties.appName) — got appNames: {got}"
        )
    print(f"OK: found {len(ac_channels)} actionCenter channel(s); bound to appName={EXPECTED_APP_NAME!r}")


def main() -> None:
    path, resource = find_escalation()
    assert_escalation_header(path, resource)
    assert_actioncenter_channel_bound(path, resource)


if __name__ == "__main__":
    main()
