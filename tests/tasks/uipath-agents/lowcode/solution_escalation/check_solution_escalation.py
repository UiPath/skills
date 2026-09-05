#!/usr/bin/env python3
"""Solution escalation (solution-internal ActionCenter app) resource check.

Validates that the agent authored an escalation wired to the solution-internal
"HumanReviewEscalation" Action Center app, regardless of what it named the
escalation resource folder:

  1. Some resources/<Name>/resource.json under ModerationAgent declares an
     escalation:
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

The escalation resource folder name is the agent's choice (the prompt names
the *app* "HumanReviewEscalation", not the resource, and the skill documents
the path as resources/<EscalationName>/resource.json), so this check locates
the escalation by content and verifies the app binding — it does NOT assume a
specific folder name. Mirrors external_escalation/check_external_escalation.py.
"""

import json
import os
import re
import sys
from pathlib import Path

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-agents")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, _shared_root)
from _shared.project_files import find_project_dir  # noqa: E402

ROOT = find_project_dir("ReviewSol", "ModerationAgent")
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"
RESOURCES_DIR = ROOT / "resources"

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


def find_escalation() -> tuple[Path, dict]:
    if not RESOURCES_DIR.is_dir():
        sys.exit(f"FAIL: no resources/ directory under {ROOT}")
    candidates = sorted(RESOURCES_DIR.glob("*/resource.json"))
    if not candidates:
        sys.exit(f"FAIL: no resources/*/resource.json found under {RESOURCES_DIR}")
    loaded = [(p, load(p)) for p in candidates]
    escalations = [(p, d) for p, d in loaded if d.get("$resourceType") == "escalation"]
    if not escalations:
        found = ", ".join(sorted({str(d.get("$resourceType", "?")) for _, d in loaded}))
        sys.exit(
            f'FAIL: no resource.json with $resourceType=="escalation" under {RESOURCES_DIR} '
            f"(found resource types: {found})"
        )
    return escalations[0]


def assert_escalation_header(path: Path, resource: dict) -> None:
    eid = resource.get("id")
    if not isinstance(eid, str) or not UUID_RE.match(eid):
        sys.exit(f"FAIL: escalation id missing or malformed at {path}: {eid!r}")
    name = resource.get("name")
    if not isinstance(name, str) or not name.strip():
        sys.exit(f"FAIL: escalation name missing or empty at {path}: {name!r}")
    if not resource.get("isEnabled"):
        sys.exit(
            f"FAIL: escalation isEnabled must be truthy at {path}, "
            f"got {resource.get('isEnabled')!r}"
        )
    print(
        f'OK: {path.parent.name}/resource.json is $resourceType="escalation" '
        f"(id={eid}, name={name!r}, isEnabled=true)"
    )


def assert_actioncenter_channel(path: Path, resource: dict) -> list:
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
    print(f"OK: found {len(ac_channels)} actionCenter channel(s)")
    return ac_channels


def assert_solution_app_binding(path: Path, ac_channels: list) -> None:
    bound = [
        c for c in ac_channels
        if (c.get("properties") or {}).get("appName") == EXPECTED_APP_NAME
    ]
    if not bound:
        got = [(c.get("properties") or {}).get("appName") for c in ac_channels]
        sys.exit(
            f"FAIL: no actionCenter channel in {path} is bound to the solution-internal app "
            f"{EXPECTED_APP_NAME!r} (properties.appName) — got appNames: {got}"
        )
    props = bound[0].get("properties") or {}
    fname = props.get("folderName")
    if fname != EXPECTED_FOLDER_NAME:
        sys.exit(
            f"FAIL: channel properties.folderName should be {EXPECTED_FOLDER_NAME!r} "
            f"(solution-internal app), got {fname!r}"
        )
    rkey = props.get("resourceKey")
    if not isinstance(rkey, str) or not UUID_RE.match(rkey):
        sys.exit(
            f"FAIL: channel properties.resourceKey must be a UUID-shaped string "
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
    path, resource = find_escalation()

    assert_escalation_header(path, resource)
    ac_channels = assert_actioncenter_channel(path, resource)
    assert_solution_app_binding(path, ac_channels)
    assert_schema_sync(agent, entry)


if __name__ == "__main__":
    main()
