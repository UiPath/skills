#!/usr/bin/env python3
"""CM-Golden rebuild: live-resolution grader.

The staged SDD pins REAL tenant identities (solution folder, resource IDs,
connection IDs, connector activity type IDs). This grader asserts the build
resolved against them instead of emitting skeletons or placeholder stubs:

  - every resource-backed task fails ``task_is_skeleton``
  - the 5 core resource IDs from the SDD appear in the build artifacts
    (caseplan / bindings_v2 / refresh-imported manifests)
  - the action app is bound by NAME on both action tasks and its manifest
    was imported (stub acceptable - alpha's cross-solution app lookup gap)
  - both connection IDs and both activity type IDs land in caseplan.json
  - connector tasks carry the right serviceType + connectorKey
  - the Stage 5 connector ENTRY RULE is resolved (real webhook typeId +
    connectionId, not the minimal stub)
  - no ``placeholder`` stub survives anywhere in the caseplan

Expectations are parsed from the task's own ``fixtures/sdd.md`` at grade
time (not from the workspace copy the agent can edit), so re-sweeping the
fixture after a golden-solution reinstall updates agent input and grader
in one file.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.case_check import (  # noqa: E402
    find_caseplan,
    iter_tasks,
    read_caseplan,
    task_is_skeleton,
)

EXPECTED_CASEPLAN = os.path.join("CMGoldenExpense", "CMGoldenExpense", "caseplan.json")
FIXTURE_SDD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "sdd.md")

GUID = r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"

# label -> regex over the fixture SDD; every one MUST parse (loud failure on
# a bad re-sweep) and MUST appear in the build artifacts.
#
# The action app is deliberately ABSENT here: a correct build binds
# SimpleApprovalApp by NAME + folder (run2-oracle-verified — neither the app
# ID nor the actionDefinitionId appears anywhere in a legitimate build), and
# on alpha the cross-solution app lookup is a known gap, so `resources
# refresh` writes a thin stub manifest with no GUID. The app is graded by
# name binding + manifest existence instead (see main()).
RESOURCE_ID_PATTERNS = {
    "agent (agentId)": rf"agentId\s+`{GUID}`",
    "agentic process (processOrchestrationId)": rf"processOrchestrationId\s+`{GUID}`",
    "rpa (processId)": rf"processId\s+`{GUID}`",
    "api workflow (apiWorkflowId)": rf"apiWorkflowId\s+`{GUID}`",
    "child case (caseManagementId)": rf"caseManagementId\s+`{GUID}`",
}


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def parse_fixture() -> dict:
    if not os.path.exists(FIXTURE_SDD):
        _fail(f"fixture SDD not found at {FIXTURE_SDD}")
    with open(FIXTURE_SDD, encoding="utf-8") as f:
        sdd = f.read()

    expected: dict = {"resources": {}, "folder": None}
    for label, pattern in RESOURCE_ID_PATTERNS.items():
        m = re.search(pattern, sdd)
        if not m:
            _fail(f"fixture parse error: no {label} matched {pattern!r} in fixtures/sdd.md")
        expected["resources"][label] = m.group(1).lower()

    conn_ids = {g.lower() for g in re.findall(rf"Connection ID[^`\n]*`{GUID}`", sdd)}
    act_ids = {g.lower() for g in re.findall(rf"Activity Type ID[^`\n]*`{GUID}`", sdd)}
    if len(conn_ids) != 2 or len(act_ids) != 2:
        _fail(
            "fixture parse error: expected 2 connection IDs and 2 activity type "
            f"IDs in fixtures/sdd.md; got {sorted(conn_ids)} / {sorted(act_ids)}"
        )
    expected["connection_ids"] = conn_ids
    expected["activity_type_ids"] = act_ids

    folders = set(re.findall(r"\*\*Folder Path:\*\*\s*(\S+)", sdd))
    if len(folders) != 1:
        _fail(f"fixture parse error: expected exactly 1 Folder Path value; got {sorted(folders)}")
    expected["folder"] = folders.pop()

    app_names = set(re.findall(r"Action App:\s*([A-Za-z0-9_-]+)", sdd))
    if len(app_names) != 1:
        _fail(f"fixture parse error: expected exactly 1 Action App name; got {sorted(app_names)}")
    expected["app_name"] = app_names.pop()

    rule_block = re.search(r"\*\*Connector Rule Detail:\*\*(.*?)(?=\n#|\Z)", sdd, re.DOTALL)
    if not rule_block:
        _fail("fixture parse error: no 'Connector Rule Detail' block (Stage 5 entry rule)")
    block = rule_block.group(1)
    rule_act = re.search(rf"Activity Type ID:\s*`{GUID}`", block)
    rule_conn = re.search(rf"Connection ID:\s*`{GUID}`", block)
    if not rule_act or not rule_conn:
        _fail("fixture parse error: Connector Rule Detail lacks Activity Type ID / Connection ID")
    expected["rule_activity_id"] = rule_act.group(1).lower()
    expected["rule_connection_id"] = rule_conn.group(1).lower()
    return expected


def load_artifacts() -> tuple[dict, str, str, str]:
    """Return (plan, caseplan_text, combined_text, solution_root); texts lowercased."""
    caseplan_path = (
        EXPECTED_CASEPLAN if os.path.exists(EXPECTED_CASEPLAN) else find_caseplan()
    )
    plan = read_caseplan(caseplan_path)
    with open(caseplan_path, encoding="utf-8") as f:
        caseplan_text = f.read().lower()

    parts = [caseplan_text]
    project_dir = os.path.dirname(caseplan_path)
    bindings_path = os.path.join(project_dir, "bindings_v2.json")
    bindings_text = None
    if os.path.exists(bindings_path):
        with open(bindings_path, encoding="utf-8") as f:
            bindings_text = f.read().lower()
        parts.append(bindings_text)
    solution_root = os.path.dirname(project_dir)
    for manifest in glob.glob(
        os.path.join(solution_root, "resources", "**", "*.json"), recursive=True
    ):
        try:
            with open(manifest, encoding="utf-8") as f:
                parts.append(f.read().lower())
        except OSError:
            continue
    return plan, caseplan_text, "\n".join(parts), solution_root, bindings_text


def main():
    expected = parse_fixture()
    plan, caseplan_text, combined, solution_root, bindings_text = load_artifacts()

    # -- real identities present -------------------------------------------
    missing = [
        label
        for label, guid in expected["resources"].items()
        if guid not in combined
    ]
    if missing:
        _fail(
            "resource IDs from fixtures/sdd.md not found in caseplan/bindings/"
            f"manifests (unresolved or fabricated): {missing}"
        )
    for kind, ids in (
        ("connection ID", expected["connection_ids"]),
        ("activity type ID", expected["activity_type_ids"]),
    ):
        absent = sorted(g for g in ids if g not in caseplan_text)
        if absent:
            _fail(f"{kind}(s) not found in caseplan.json: {absent}")
    if expected["folder"].lower() not in combined:
        _fail(f"solution folder path {expected['folder']!r} not found in build artifacts")

    # -- no placeholder stubs -------------------------------------------------
    if "placeholder" in caseplan_text:
        _fail(
            "caseplan contains a 'placeholder' stub - a connector task or "
            "connector rule was not resolved against the live tenant"
        )

    # -- no skeleton tasks ------------------------------------------------------
    skeletons, timer_empty = [], []
    for task in iter_tasks(plan):
        ttype = task.get("type")
        name = task.get("displayName") or (task.get("data") or {}).get("label") or task.get("id")
        if ttype == "wait-for-timer":
            if not task.get("data"):
                timer_empty.append(name)
        elif task_is_skeleton(task):
            skeletons.append(f"{name} ({ttype})")
    if skeletons:
        _fail(f"skeleton tasks found (resource not resolved): {skeletons}")
    if timer_empty:
        _fail(f"wait-for-timer tasks with empty data: {timer_empty}")

    # -- action app: bound by NAME, manifest present (stub OK) ------------------
    # Correct builds bind the app by name+folder (no GUID anywhere), and the
    # alpha cross-solution app lookup gap means refresh may write a stub
    # manifest - existence is the requirement, fullness is not.
    app_name = expected["app_name"]
    actions = [t for t in iter_tasks(plan) if t.get("type") == "action"]
    if len(actions) != 2:
        _fail(f"expected exactly 2 action tasks; got {len(actions)}")
    # Tasks reference the app through top-level bindings[] entries (resourceKey
    # "<folder>.<app>"), not by carrying the name in the task dict.
    app_bindings = [
        b
        for b in (plan.get("bindings") or [])
        if app_name.lower() in json.dumps(b, default=str).lower()
    ]
    if not app_bindings:
        _fail(
            f"no caseplan bindings[] entry references app {app_name!r} - "
            "action tasks are not bound to the app by name"
        )
    manifests = glob.glob(
        os.path.join(solution_root, "resources", "**", f"{app_name}.json"),
        recursive=True,
    )
    if not manifests:
        _fail(
            f"no {app_name}.json manifest under resources/ - solution "
            "resources refresh did not import the app (a stub is acceptable)"
        )

    # -- bindings_v2.json: refresh/deploy binding manifest ------------------------
    # The functional oracle carries one entry per external resource plus both
    # connection bindings; refresh and deploy resolve through this file.
    if bindings_text is None:
        _fail("bindings_v2.json missing next to caseplan.json")
    try:
        bindings_doc = json.loads(bindings_text)
    except ValueError:
        _fail("bindings_v2.json is not valid JSON")
    if not (bindings_doc.get("resources") or []):
        _fail("bindings_v2.json has no resources[] entries")
    for kind, ids in (
        ("connection ID", expected["connection_ids"]),
    ):
        absent = sorted(g for g in ids if g not in bindings_text)
        if absent:
            _fail(f"{kind}(s) not found in bindings_v2.json: {absent}")
    app_key = f"{expected['folder']}.{app_name}".lower()
    if app_key not in bindings_text:
        _fail(f"bindings_v2.json missing app resourceKey {app_key!r}")

    # -- connector tasks: serviceType + connectorKey -------------------------------
    for ttype, svc, key in (
        ("wait-for-connector", "intsvc.waitforevent", "uipath-http-webhook"),
        ("execute-connector-activity", "intsvc.activityexecution", "uipath-mock-element"),
    ):
        matches = [t for t in iter_tasks(plan) if t.get("type") == ttype]
        if len(matches) != 1:
            _fail(f"expected exactly 1 {ttype} task; got {len(matches)}")
        task_text = json.dumps(matches[0], default=str).lower()
        if svc not in task_text:
            _fail(f"{ttype} task missing serviceType {svc!r}")
        if key not in task_text:
            _fail(f"{ttype} task not bound to connector {key!r}")

    # -- Stage 5 connector entry rule resolved --------------------------------------
    stage5 = next(
        (
            n
            for n in plan.get("nodes") or []
            if "Stage" in (n.get("type") or "") and _norm((n.get("data") or {}).get("label")).startswith("stage5")
        ),
        None,
    )
    if stage5 is None:
        _fail("Stage 5 node not found")
    entry_text = json.dumps(
        (stage5.get("data") or {}).get("entryConditions") or [], default=str
    ).lower()
    if expected["rule_activity_id"] not in entry_text:
        _fail("Stage 5 entry rule missing the webhook activity type ID (unresolved rule)")
    if expected["rule_connection_id"] not in entry_text:
        _fail("Stage 5 entry rule missing the webhook connection ID (unresolved rule)")

    print(
        "OK: all resource IDs, app name binding + manifest, both connections, "
        "both activity types, and the Stage 5 connector entry rule resolved "
        "against the live tenant; no skeletons, no placeholder stubs"
    )


if __name__ == "__main__":
    main()
