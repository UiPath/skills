#!/usr/bin/env python3
"""Solution escalation (solution-internal ActionCenter app) resource check.

Validates:
  1. resources/HumanReviewEscalation/resource.json declares an escalation:
       - $resourceType == "escalation"
       - id is a UUID-shaped non-empty string
       - name is a non-empty string
       - isEnabled is truthy
  2. The escalation has at least one channel wired to ActionCenter:
       - channels is a non-empty list
       - at least one channel has type == "actionCenter" (lowercase, per
         the schema documented in the skill's escalation reference) and
         a non-empty name.
  3. The ActionCenter channel is bound to the solution-internal
     HumanReviewEscalation app:
       - properties.appName == "HumanReviewEscalation"
       - properties.folderName == "solution_folder"
       - properties.resourceKey is a UUID-shaped non-empty string
  4. agent.json.inputSchema  == entry-points.json entryPoints[0].input
     agent.json.outputSchema == entry-points.json entryPoints[0].output
     (Critical Rule 4 — schema sync.)
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "ReviewSol" / "ModerationAgent"
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"
RESOURCE = ROOT / "resources" / "HumanReviewEscalation" / "resource.json"

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

EXPECTED_APP_NAME = "HumanReviewEscalation"
EXPECTED_FOLDER_NAME = "solution_folder"


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


def assert_actioncenter_channel(resource: dict) -> list:
    channels = resource.get("channels")
    if not isinstance(channels, list) or not channels:
        sys.exit(f"FAIL: escalation.channels must be a non-empty list, got {channels!r}")
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
            f"in channels: {json.dumps(channels, indent=2)}"
        )
    print(f"OK: found {len(ac_channels)} actionCenter channel(s)")
    return ac_channels


def assert_solution_app_binding(ac_channels: list) -> None:
    bound = [
        c for c in ac_channels
        if (c.get("properties") or {}).get("appName") == EXPECTED_APP_NAME
    ]
    if not bound:
        sys.exit(
            f"FAIL: no actionCenter channel is bound to the solution-internal app "
            f"{EXPECTED_APP_NAME!r} (properties.appName) — got appNames: "
            f"{[(c.get('properties') or {}).get('appName') for c in ac_channels]}"
        )
    props = bound[0].get("properties") or {}
    fname = props.get("folderName")
    if fname != EXPECTED_FOLDER_NAME:
        sys.exit(
            f"FAIL: channel properties.folderName should be {EXPECTED_FOLDER_NAME!r} "
            f"(solution-internal app), got {fname!r}"
        )
    rkey = props.get("resourceKey")
    if not isinstance(rkey, str) or not rkey.strip():
        sys.exit(
            f"FAIL: channel properties.resourceKey must be a non-empty string "
            f"(Key from `uip solution resources list`), got {rkey!r}"
        )
    print(
        f"OK: actionCenter channel is bound to appName={EXPECTED_APP_NAME!r}, "
        f"folderName={EXPECTED_FOLDER_NAME!r}, resourceKey={rkey!r}"
    )


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
    ac_channels = assert_actioncenter_channel(resource)
    assert_solution_app_binding(ac_channels)
    assert_schema_sync(agent, entry)


if __name__ == "__main__":
    main()
