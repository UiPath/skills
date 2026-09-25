#!/usr/bin/env python3
"""ContractExecution rebuild: deterministic live-binding grader.

The staged SDD pins REAL tenant identities (solution folders, resource IDs,
connection IDs, connector activity type IDs). This grader asserts the build
resolved against them instead of emitting skeletons or placeholder stubs:

  - every resource-backed task fails ``task_is_skeleton``
  - every resource (api-workflow, agent, child case, action app) is bound by
    its SDD name + folder in BOTH caseplan.bindings[] and bindings_v2.json
    (tenant GUIDs are discovery inputs, not runtime binding fields, so their
    placement is deliberately not graded)
  - both HTTP Webhook connection IDs and the activity type ID land in
    caseplan.json; both connections land in bindings_v2.json
  - the `wait-for-connector` TASK resolves against the e-signature connection
  - the `wait-for-connector` STAGE-ENTRY RULE on the withdrawal lane resolves
    against the OTHER connection (real typeId + connectionId, not the minimal
    placeholder stub), so the two webhooks are not collapsed into one

Expectations are parsed from the task's own ``fixtures/sdd.md`` at grade time
(not from the workspace copy the agent can edit), so re-sweeping the fixture
after a tenant reinstall updates agent input and grader in one file.
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
    find_stages,
    iter_tasks,
    read_caseplan,
    task_is_skeleton,
)

EXPECTED_CASEPLAN = os.path.join("ContractExecution", "ContractExecution", "caseplan.json")
FIXTURE_SDD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "sdd.md")

GUID = r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
CONNECTOR_KEY = "uipath-http-webhook"
WITHDRAWN_STAGE = "Contract withdrawn"

# name marker -> following **Folder Path:** / **Deployment Folder:** line.
RESOURCE_RE = re.compile(
    r"\*\*Resolved Resource:\*\*\s*(\S+)[^\n]*\n\*\*Folder Path:\*\*\s*(\S+)"
)
CHILD_CASE_RE = re.compile(
    r"\*\*Child Case:\*\*\s*(\S+)[^\n]*\n\*\*Folder Path:\*\*\s*(\S+)"
)
ACTION_APP_RE = re.compile(
    r"\*\*HITL Implementation:\*\*\s*Action App:\s*(\S+)[^\n]*\n"
    r"\*\*Action App ID:\*\*[^\n]*\n"
    r"\*\*Deployment Folder:\*\*\s*(\S+)"
)


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def parse_fixture() -> dict:
    if not os.path.exists(FIXTURE_SDD):
        _fail(f"fixture SDD not found at {FIXTURE_SDD}")
    with open(FIXTURE_SDD, encoding="utf-8") as stream:
        sdd = stream.read()

    resource_keys = {f"{folder}.{name}" for name, folder in RESOURCE_RE.findall(sdd)}
    child_keys = {f"{folder}.{name}" for name, folder in CHILD_CASE_RE.findall(sdd)}
    app_keys = {f"{folder}.{name}" for name, folder in ACTION_APP_RE.findall(sdd)}
    if len(resource_keys) != 2:
        _fail(
            "fixture parse error: expected 2 distinct Resolved Resource name/folder "
            f"pairs (api-workflow + agent); got {sorted(resource_keys)}"
        )
    if len(child_keys) != 1:
        _fail(f"fixture parse error: expected exactly 1 Child Case; got {sorted(child_keys)}")
    if len(app_keys) != 1:
        _fail(f"fixture parse error: expected exactly 1 Action App; got {sorted(app_keys)}")

    # Connector TASK detail carries a Service Type; the stage-entry rule block is
    # the one nested under "##### Connector Rule Detail".
    rule_block = re.search(
        r"#####\s*Connector Rule Detail(.*?)(?=\n####|\n---|\Z)", sdd, re.DOTALL
    )
    if not rule_block:
        _fail("fixture parse error: no 'Connector Rule Detail' block (withdrawal stage entry)")
    block = rule_block.group(1)
    rule_connection = re.search(rf"Connection ID:\*\*\s*`?{GUID}", block)
    rule_activity = re.search(rf"Activity Type ID:\*\*\s*`?{GUID}", block)
    if not rule_connection or not rule_activity:
        _fail(
            "fixture parse error: Connector Rule Detail lacks Connection ID / "
            "Activity Type ID"
        )

    all_connections = {
        guid.lower() for guid in re.findall(rf"Connection ID:\*\*\s*`?{GUID}", sdd)
    }
    all_activities = {
        guid.lower() for guid in re.findall(rf"Activity Type ID:\*\*\s*`?{GUID}", sdd)
    }
    if len(all_connections) != 2 or not all_activities:
        _fail(
            "fixture parse error: expected 2 distinct Connection IDs and >=1 Activity "
            f"Type ID; got {sorted(all_connections)} / {sorted(all_activities)}"
        )

    rule_connection_id = rule_connection.group(1).lower()
    task_connections = all_connections - {rule_connection_id}
    if len(task_connections) != 1:
        _fail(
            "fixture parse error: could not separate the connector TASK connection from "
            f"the stage-entry RULE connection; got {sorted(all_connections)}"
        )

    return {
        "resource_keys": resource_keys | child_keys | app_keys,
        "connection_ids": all_connections,
        "activity_type_ids": all_activities,
        "rule_connection_id": rule_connection_id,
        "rule_activity_id": rule_activity.group(1).lower(),
        "task_connection_id": task_connections.pop(),
    }


def load_artifacts() -> tuple[dict, str, str]:
    """Return (plan, caseplan_text, bindings_text); texts are lowercased."""
    caseplan_path = (
        EXPECTED_CASEPLAN if os.path.exists(EXPECTED_CASEPLAN) else find_caseplan()
    )
    plan = read_caseplan(caseplan_path)
    with open(caseplan_path, encoding="utf-8") as stream:
        caseplan_text = stream.read().lower()

    bindings_path = os.path.join(os.path.dirname(caseplan_path), "bindings_v2.json")
    if not os.path.exists(bindings_path):
        _fail("bindings_v2.json missing next to caseplan.json")
    with open(bindings_path, encoding="utf-8") as stream:
        bindings_text = stream.read()
    return plan, caseplan_text, bindings_text


def _check_no_skeletons(plan: dict):
    skeletons = []
    for task in iter_tasks(plan):
        if not task_is_skeleton(task):
            continue
        name = (
            task.get("displayName")
            or (task.get("data") or {}).get("label")
            or task.get("id")
        )
        skeletons.append(f"{name} ({task.get('type')})")
    if skeletons:
        _fail(f"skeleton tasks found (resource not resolved): {sorted(skeletons)}")


def _check_resource_keys(plan: dict, bindings_text: str, expected_keys: set[str]):
    wanted = {key.lower() for key in expected_keys}
    caseplan_keys = {
        str(binding.get("resourceKey") or "").lower()
        for binding in (plan.get("bindings") or [])
    }
    missing = sorted(wanted - caseplan_keys)
    if missing:
        _fail(f"caseplan bindings[] missing resource key(s): {missing}")

    try:
        bindings_doc = json.loads(bindings_text)
    except ValueError:
        _fail("bindings_v2.json is not valid JSON")
    resources = bindings_doc.get("resources") or []
    if not resources:
        _fail("bindings_v2.json has no resources[] entries")
    binding_keys = {str(resource.get("key") or "").lower() for resource in resources}
    missing = sorted(wanted - binding_keys)
    if missing:
        _fail(f"bindings_v2.json missing resource key(s): {missing}")


def _connector_context(container: dict) -> dict[str, object]:
    """Flatten a resolved connector ``context[]`` into {name: value}."""
    flat: dict[str, object] = {}
    for entry in container.get("context") or []:
        if isinstance(entry, dict) and entry.get("name"):
            flat[entry["name"]] = entry.get("value", entry.get("body"))
    return flat


def _check_connector_task(plan: dict, expected: dict, caseplan_text: str):
    matches = [t for t in iter_tasks(plan) if t.get("type") == "wait-for-connector"]
    if len(matches) != 1:
        _fail(f"expected exactly 1 wait-for-connector task; got {len(matches)}")
    data = matches[0].get("data") or {}
    if data.get("serviceType") != "Intsvc.WaitForEvent":
        _fail(
            "wait-for-connector task serviceType must be 'Intsvc.WaitForEvent'; got "
            f"{data.get('serviceType')!r}"
        )
    task_text = json.dumps(data, default=str).lower()
    if CONNECTOR_KEY not in task_text:
        _fail(f"wait-for-connector task not bound to connector {CONNECTOR_KEY!r}")
    if expected["task_connection_id"] not in task_text:
        _fail(
            "'Wait for Signature Result' must resolve against the e-signature "
            f"connection {expected['task_connection_id']}; not found in its data"
        )
    if not any(activity in task_text for activity in expected["activity_type_ids"]):
        _fail(
            "wait-for-connector task carries no SDD activity type ID "
            f"({sorted(expected['activity_type_ids'])}) - the connector did not resolve"
        )
    for kind, ids in (
        ("connection ID", expected["connection_ids"]),
        ("activity type ID", expected["activity_type_ids"]),
    ):
        absent = sorted(guid for guid in ids if guid not in caseplan_text)
        if absent:
            _fail(f"{kind}(s) not found in caseplan.json: {absent}")


def _check_connector_entry_rule(plan: dict, expected: dict):
    stage = next(
        (
            node
            for node in find_stages(plan, include_exception=True)
            if _norm((node.get("data") or {}).get("label")) == _norm(WITHDRAWN_STAGE)
        ),
        None,
    )
    if stage is None:
        _fail(f"{WITHDRAWN_STAGE!r} stage node not found")

    rules = [
        rule
        for condition in ((stage.get("data") or {}).get("entryConditions") or [])
        for group in (condition.get("rules") or [])
        for rule in (group or [])
        if (rule or {}).get("rule") == "wait-for-connector"
    ]
    if len(rules) != 1:
        _fail(
            f"{WITHDRAWN_STAGE!r} must be entered by exactly one wait-for-connector "
            f"rule; got {len(rules)}"
        )
    uipath = rules[0].get("uipath")
    if not isinstance(uipath, dict) or not uipath:
        _fail(
            f"{WITHDRAWN_STAGE!r} wait-for-connector rule has no resolved `uipath` block "
            "(bare rule / placeholder stub)"
        )
    if uipath.get("serviceType") != "Intsvc.WaitForEvent":
        _fail(
            f"{WITHDRAWN_STAGE!r} entry rule serviceType must be 'Intsvc.WaitForEvent'; "
            f"got {uipath.get('serviceType')!r}"
        )
    context = _connector_context(uipath)
    if context.get("connectorKey") != CONNECTOR_KEY:
        _fail(
            f"{WITHDRAWN_STAGE!r} entry rule connectorKey must be {CONNECTOR_KEY!r}; got "
            f"{context.get('connectorKey')!r}"
        )
    rule_text = json.dumps(uipath, default=str).lower()
    if expected["rule_connection_id"] not in rule_text:
        _fail(
            f"{WITHDRAWN_STAGE!r} entry rule missing the withdrawal webhook connection "
            f"{expected['rule_connection_id']} (unresolved, or collapsed onto the "
            "e-signature connection)"
        )
    if expected["task_connection_id"] in rule_text:
        _fail(
            f"{WITHDRAWN_STAGE!r} entry rule references the e-signature connection "
            f"{expected['task_connection_id']}; the SDD pins a DIFFERENT connection for "
            "the withdrawal webhook"
        )
    if expected["rule_activity_id"] not in rule_text:
        _fail(
            f"{WITHDRAWN_STAGE!r} entry rule missing the webhook activity type ID "
            f"{expected['rule_activity_id']} (unresolved rule)"
        )


def main():
    expected = parse_fixture()
    plan, caseplan_text, bindings_text = load_artifacts()

    _check_no_skeletons(plan)
    _check_resource_keys(plan, bindings_text, expected["resource_keys"])

    lowered_bindings = bindings_text.lower()
    absent = sorted(
        guid for guid in expected["connection_ids"] if guid not in lowered_bindings
    )
    if absent:
        _fail(f"connection ID(s) not found in bindings_v2.json: {absent}")

    _check_connector_task(plan, expected, caseplan_text)
    _check_connector_entry_rule(plan, expected)

    print(
        "OK: all SDD resource name/folder keys are bound in caseplan.bindings[] and "
        "bindings_v2.json, both HTTP Webhook connections and the activity type ID "
        "resolved, the signature task and the withdrawal stage-entry rule use their "
        "own distinct connections, and no task is a skeleton"
    )


if __name__ == "__main__":
    main()
