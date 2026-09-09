#!/usr/bin/env python3
"""End state after removing a resource-bound task and adding a timer task.

The removed task ("Estimate Age") is an api-workflow bound to NameToAgeFixed.
Removing it must cascade all the way out of the solution:

    caseplan task -> caseplan bindings[] -> bindings_v2 resources[]
                  -> resources/solution_folder/ declarations

`uip solution resources refresh` is additive-only, so the last hop only happens
if the agent runs `uip solution resources remove`. Everything else can look
correct while the declarations linger.

Also guards the opposite failure: the case project's own package +
caseManagement declarations are absent from bindings_v2.json by design and MUST
survive. A naive "not in bindings_v2 -> orphan" sweep deletes the case itself.
"""

import json
import sys
from pathlib import Path

SOLUTION = Path("LinearThreeStages")
PROJECT = SOLUTION / "LinearThreeStages"
RESOURCES = SOLUTION / "resources" / "solution_folder"

REMOVED_TASK = "Estimate Age"
ADDED_TASK = "Final Hold"
DECISION_STAGE = "Stage_Vw2hJc"

ORPHANED = [
    (RESOURCES / "process" / "Api" / "NameToAgeFixed.json", "api-workflow declaration"),
    (
        RESOURCES / "package" / "NameToAgeFixed.api.NameToAgeFixed.json",
        "its package declaration",
    ),
]

MUST_SURVIVE = [
    (RESOURCES / "package" / "LinearThreeStages.json", "case project's package"),
    (
        RESOURCES / "process" / "caseManagement" / "LinearThreeStages.json",
        "case project's caseManagement process",
    ),
]

failures = []


def load(path):
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001 - surfaced as a graded failure
        failures.append(f"could not read {path}: {exc}")
        return None


caseplan = load(PROJECT / "caseplan.json")
bindings_v2 = load(PROJECT / "bindings_v2.json")

if caseplan is not None:
    tasks = [
        t
        for node in caseplan.get("nodes", [])
        for lane in node.get("data", {}).get("tasks", [])
        for t in lane
    ]
    names = [t.get("displayName") for t in tasks]

    if REMOVED_TASK in names:
        failures.append(f'task "{REMOVED_TASK}" is still in caseplan.json')

    if caseplan.get("bindings"):
        ids = [b.get("id") for b in caseplan["bindings"]]
        failures.append(f"caseplan.json still carries bindings {ids} - expected none")

    added = [
        t
        for node in caseplan.get("nodes", [])
        if node.get("id") == DECISION_STAGE
        for lane in node.get("data", {}).get("tasks", [])
        for t in lane
        if t.get("displayName") == ADDED_TASK
    ]
    if not added:
        failures.append(
            f'task "{ADDED_TASK}" was not added to the Decision stage ({DECISION_STAGE})'
        )
    elif added[0].get("type") != "wait-for-timer":
        failures.append(
            f'"{ADDED_TASK}" has type {added[0].get("type")!r}, expected "wait-for-timer"'
        )

if bindings_v2 is not None and bindings_v2.get("resources"):
    keys = [r.get("key") for r in bindings_v2["resources"]]
    failures.append(f"bindings_v2.json still declares resources {keys} - expected none")

for path, label in ORPHANED:
    if path.exists():
        failures.append(f"orphaned {label} was NOT pruned - {path} still exists")

for path, label in MUST_SURVIVE:
    if not path.exists():
        failures.append(f"over-pruned: {label} was deleted - {path} is missing")

if failures:
    print("FAIL:", file=sys.stderr)
    for f in failures:
        print(f"  - {f}", file=sys.stderr)
    sys.exit(1)

print("PASS: bound task removed end-to-end, timer task added, case project intact")
sys.exit(0)
