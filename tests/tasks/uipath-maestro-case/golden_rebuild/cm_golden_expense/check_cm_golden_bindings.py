#!/usr/bin/env python3
"""CM-Golden rebuild: deterministic live-binding grader.

The staged SDD pins REAL tenant identities (solution folder, resource IDs,
connection IDs, connector activity type IDs). This grader asserts the build
resolved against them instead of emitting skeletons or placeholder stubs:

  - every resource-backed task fails ``task_is_skeleton``
  - every non-connector resource is bound by its SDD name + folder in both
    caseplan and bindings_v2 (tenant GUIDs are discovery inputs, not runtime
    binding fields, so their placement is deliberately not graded)
  - both connection IDs and both activity type IDs land in caseplan.json
  - connector tasks carry the right serviceType + connectorKey
  - the Stage 5 connector ENTRY RULE is resolved (real webhook typeId +
    connectionId, not the minimal stub)
  - bindings_v2 carries both connection bindings

Expectations are parsed from the task's own ``fixtures/sdd.md`` at grade
time (not from the workspace copy the agent can edit), so re-sweeping the
fixture after a golden-solution reinstall updates agent input and grader
in one file.
"""

from __future__ import annotations

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


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def parse_fixture() -> dict:
    if not os.path.exists(FIXTURE_SDD):
        _fail(f"fixture SDD not found at {FIXTURE_SDD}")
    with open(FIXTURE_SDD, encoding="utf-8") as f:
        sdd = f.read()

    expected: dict = {"folder": None}
    resource_names = set(re.findall(r"\*\*Resolved Resource:\*\*\s*([^\n]+)", sdd))
    if len(resource_names) != 5:
        _fail(
            "fixture parse error: expected 5 distinct Resolved Resource names; "
            f"got {sorted(resource_names)!r}"
        )
    expected["resource_names"] = resource_names

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


def load_artifacts() -> tuple[dict, str, str | None]:
    """Return (plan, caseplan_text, bindings_text); texts are lowercased."""
    caseplan_path = (
        EXPECTED_CASEPLAN if os.path.exists(EXPECTED_CASEPLAN) else find_caseplan()
    )
    plan = read_caseplan(caseplan_path)
    with open(caseplan_path, encoding="utf-8") as f:
        caseplan_text = f.read().lower()

    project_dir = os.path.dirname(caseplan_path)
    bindings_path = os.path.join(project_dir, "bindings_v2.json")
    bindings_text = None
    if os.path.exists(bindings_path):
        with open(bindings_path, encoding="utf-8") as f:
            bindings_text = f.read().lower()
    return plan, caseplan_text, bindings_text


def main():
    expected = parse_fixture()
    plan, caseplan_text, bindings_text = load_artifacts()

    # -- live connector identities present ---------------------------------
    for kind, ids in (
        ("connection ID", expected["connection_ids"]),
        ("activity type ID", expected["activity_type_ids"]),
    ):
        absent = sorted(g for g in ids if g not in caseplan_text)
        if absent:
            _fail(f"{kind}(s) not found in caseplan.json: {absent}")
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

    # -- name/folder resource bindings + bindings_v2 -----------------------------
    if bindings_text is None:
        _fail("bindings_v2.json missing next to caseplan.json")
    try:
        bindings_doc = json.loads(bindings_text)
    except ValueError:
        _fail("bindings_v2.json is not valid JSON")
    if not (bindings_doc.get("resources") or []):
        _fail("bindings_v2.json has no resources[] entries")
    expected_keys = {
        f"{expected['folder']}.{name}".lower()
        for name in expected["resource_names"] | {expected["app_name"]}
    }
    caseplan_keys = {
        str(binding.get("resourceKey") or "").lower()
        for binding in (plan.get("bindings") or [])
    }
    missing_caseplan_keys = sorted(expected_keys - caseplan_keys)
    if missing_caseplan_keys:
        _fail(f"caseplan bindings[] missing resource key(s): {missing_caseplan_keys}")
    binding_keys = {
        str(resource.get("key") or "").lower()
        for resource in (bindings_doc.get("resources") or [])
    }
    missing_binding_keys = sorted(expected_keys - binding_keys)
    if missing_binding_keys:
        _fail(f"bindings_v2.json missing resource key(s): {missing_binding_keys}")
    for kind, ids in (
        ("connection ID", expected["connection_ids"]),
    ):
        absent = sorted(g for g in ids if g not in bindings_text)
        if absent:
            _fail(f"{kind}(s) not found in bindings_v2.json: {absent}")
    # -- connector tasks: serviceType + connectorKey -------------------------------
    for ttype, svc, key in (
        ("wait-for-connector", "intsvc.waitforevent", "uipath-http-webhook"),
        ("execute-connector-activity", "intsvc.activityexecution", "uipath-microsoft-outlook365"),
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
        "OK: all resource name/folder keys, both connections, both activity "
        "types, connector task contracts, and the Stage 5 connector entry rule "
        "are resolved against the live tenant; no skeleton tasks"
    )


if __name__ == "__main__":
    main()
