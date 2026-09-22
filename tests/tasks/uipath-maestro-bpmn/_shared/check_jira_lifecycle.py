#!/usr/bin/env python3
"""JiraLifecycle (BPMN): structural + live + tenant checks for a
multi-instance-loop-and-gateway process.

Ported from Flow `e2e/jira_lifecycle/_shared/check_jira_lifecycle.py`: same
scenario (a manual-start process iterates a seeded batch of issues and, per
item, creates a Jira issue then routes on the item's `priority` through a
branch node to a branch-specific Add-Comment), translated from a JSON node
walk + inline `flow debug` payload to an XML walk over the BPMN loop/gateway
constructs plus the BPMN live-debug surface (`_shared/bpmn_live.py`, per
LIVE-ADDENDUM's canonical pattern: ephemeral solution import, `bpmn debug`,
`debug-instance variables-all`/`incidents`).

Exits non-zero on the first failure (``FAIL: ...``); prints ``OK: ...`` per
check. Every confirmed key is recorded to ``.created_keys`` as soon as it is
seen, so post_run teardown deletes it even if a later assertion fails.

Assertion map (Flow -> BPMN):
  F check_jira_lifecycle.py:75  JIRA_KEY not in raw or '"nodes"' not in raw
                                 ('"nodes"' marker dropped -- XML has no JSON
                                 "nodes" key, see I below)
                                 -> JIRA_KEY not in raw text of the .bpmn
  F check_jira_lifecycle.py:79  assert_flow_has_node_type(["core.logic.loop"])
                                 -> has_multi_instance_loop(root): a
                                    bpmn:multiInstanceLoopCharacteristics element
                                    is present anywhere in the process
  F check_jira_lifecycle.py:80  assert_flow_has_any_node_type(["core.logic.switch",
                                 "core.logic.decision"])
                                 -> has_conditional_gateway(root): a
                                    bpmn:exclusiveGateway element together with
                                    at least one bpmn:conditionExpression is
                                    present anywhere in the process
  F check_jira_lifecycle.py:84  run_debug(timeout=600) implicitly requires
                                 finalStatus == "Completed" (flow_check.run_debug
                                 raises on a non-Completed status internally;
                                 `bpmn debug` returns only an instance id, so the
                                 check is explicit here)
                                 -> FinalStatus in COMPLETED_STATUSES and
                                    debug-instance incidents is empty
  F check_jira_lifecycle.py:90-92  cands = regex findall of the project's
                                 issue-key pattern over get_last_debug_raw()
                                 (the whole inline flow debug payload text)
                                 -> same regex over json.dumps(variables_data)
                                    (the whole debug-instance variables-all
                                    payload text) -- the create nodes'
                                    responses land there regardless of how the
                                    process mapped its outputs, mirroring
                                    Flow's own comment
  F check_jira_lifecycle.py:108  marker not in comment_blob -> branch routed
                                 the comment correctly
                                 -> same check, same jira_is.get_issue() field
  F check_jira_lifecycle.py:115  missing = [s for s in want_marker if s not in
                                 found] -> the loop created every seeded issue
                                 -> same check
  I                locate/parse .bpmn (file exists, well-formed XML, project
                    directory resolved)
                                 -> bpmn_check.find_bpmn_file()/resolve_project()
  I                ephemeral solution init + `solution projects import` + sha256
                    pin of the imported bytes against the submitted file --
                    `bpmn debug` runs against an imported project, unlike
                    `flow debug`, which runs directly against the discovered
                    project directory
                                 -> LIVE-ADDENDUM canonical live pattern
                                    (mirrors
                                    e2e/customer_escalation_triage/check_customer_escalation_behavior.py
                                    and _shared/check_jira_get_issue.py)
  I                Flow imports the shared `_shared/jira_is.py` helper
                    (connection_id() / get_issue()); no BPMN equivalent shared
                    module exists yet and BATCH1-ADDENDUM asks graders not to
                    add a new one while several tasks port in parallel, so
                    the same two `uip is resources run` calls are inlined
                    below (byte-identical operation names/queries to the
                    task's own `_setup/jira_is.py`)
                                 -> _connection_id() / _get_issue() below
  DROPPED          require_no_private_connector_values / require_sequence_integrity
                    / require_di_for_visible_elements / connection-binding checks
                    / per-node connector-operation classification -- not in
                    Flow (Flow's own structural check never classifies the
                    Create-Issue/Add-Comment node ops either, deferring
                    entirely to the LIVE tenant re-read); the `bpmn validate`
                    criterion covers structure
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# …/uipath-maestro-bpmn (for _shared), same convention as check_jira_get_issue.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_check import find_bpmn_file, resolve_project  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    get_ci,
    incident_records,
    payload_data,
    run_cli,
    sha256,
)

JIRA_KEY = "uipath-atlassian-jira"
# Same tenant target as the task's own _setup/jira_is.py (and the pilot
# e2e/jira_get_issue/_setup/jira_is.py) -- a shared tenant fixture, not Flow
# vocabulary, kept verbatim per LIVE-ADDENDUM.
FOLDER_PATH = "Shared/uipath-maestro-flow"
CONNECTION_NAME = "is-sandboxes-test@uipath.com-uipath-sandbox-380"
NAME_HINT = "JiraLifecycle"

LIVE_RUN_DIR = Path("jira-lifecycle-live")
SOLUTION_INIT_TIMEOUT = 90
SOLUTION_IMPORT_TIMEOUT = 180
VARIABLES_ALL_TIMEOUT = 120
INCIDENTS_TIMEOUT = 120
COMPLETED_STATUSES = {"Completed", "Successful"}
# Worst-case wall clock this checker can spend, priced the way
# _shared/test_criterion_budgets.py prices a run_debug(...) call: the debug
# call below passes a literal timeout=720, so it prices at
# bpmn_live.debug_budget(720) == 720 (one attempt, no backoff).
# The surrounding CLI steps (solution init/import, variables-all, incidents)
# are not priced by that guard, so their sum is added by hand here and the
# criterion `timeout:` in jira_lifecycle.yaml documents the arithmetic:
#   90 (solution init) + 180 (solution import) + 720 (debug)
#   + 120 (variables-all) + 120 (incidents) = 1230
#   + bpmn_live.CRITERION_MARGIN_SECONDS (60) = 1290
# Flow's own criterion timeout (1320) already covers this (30s to spare), so
# it is kept verbatim rather than raised.
#
# The 720 below is passed as a literal (not this comment's named constant) so
# test_criterion_budgets.py's static AST pricer -- which only recognizes
# literal timeout=/retries=/backoff_seconds= arguments on the run_debug(...)
# call itself -- can price it.


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def has_multi_instance_loop(root: ET.Element) -> bool:
    return any(_local(el.tag) == "multiInstanceLoopCharacteristics" for el in root.iter())


def has_conditional_gateway(root: ET.Element) -> bool:
    """A bpmn:exclusiveGateway with at least one bpmn:conditionExpression
    anywhere in the process -- same any-of level of specificity as Flow's own
    ``assert_flow_has_any_node_type(["core.logic.switch", "core.logic.decision"])``,
    which likewise only checks node-type presence, not branch wiring."""
    has_gateway = any(_local(el.tag) == "exclusiveGateway" for el in root.iter())
    has_condition = any(_local(el.tag) == "conditionExpression" for el in root.iter())
    return has_gateway and has_condition


def _run(*args: str) -> dict:
    out = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=120,
    ).stdout
    return json.loads(out)


def _connection_id() -> str:
    folder_key = _run("or", "folders", "get", FOLDER_PATH)["Data"]["Key"]
    conns = _run(
        "is", "connections", "list", JIRA_KEY, "--folder-key", folder_key, "--refresh"
    )["Data"]
    return next(c["Id"] for c in conns if c["Name"] == CONNECTION_NAME)


def _get_issue(conn_id: str, key: str, project: str, issuetype_id: str) -> dict | None:
    """Return the issue's `fields` dict (includes `summary` and `comment`),
    or None if it doesn't exist (404)."""
    env = _run(
        "is", "resources", "run", "get", JIRA_KEY, "curated_get_issue",
        "--connection-id", conn_id,
        "--query", f"project={project}&issuetype={issuetype_id}&issueId={key}",
    )
    if env.get("Result") == "Failure":
        return None
    return env["Data"].get("fields", {})


def _record_key(key: str) -> None:
    """Append a confirmed key to .created_keys (dedup) for teardown."""
    kf = Path(".created_keys")
    seen = set(kf.read_text().split()) if kf.is_file() else set()
    if key not in seen:
        with kf.open("a") as f:
            f.write(key + "\n")


def main() -> None:
    seed_path = Path("seed.json")
    if not seed_path.is_file():
        _fail("seed.json is missing from the sandbox (pre_run seed did not run)")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    issues = seed["issues"]
    project = seed["project_key"]
    issuetype_id = seed["issuetype_id"]
    # summary -> expected comment marker for that item's branch
    want_marker = {
        i["summary"]: (seed["escalated_marker"] if i["priority"] == "High" else seed["routine_marker"])
        for i in issues
    }

    # 1. STRUCTURAL ----------------------------------------------------------
    bpmn_path = find_bpmn_file(NAME_HINT)
    raw = Path(bpmn_path).read_text(encoding="utf-8")
    if JIRA_KEY not in raw:
        _fail(f"{bpmn_path} does not reference the {JIRA_KEY} connector")
    print(f"OK: bpmn references {JIRA_KEY}")

    try:
        root = ET.parse(bpmn_path).getroot()
    except ET.ParseError as exc:
        _fail(f"{bpmn_path} is not well-formed XML: {exc}")

    if not has_multi_instance_loop(root):
        _fail("bpmn does not contain a bpmn:multiInstanceLoopCharacteristics loop")
    if not has_conditional_gateway(root):
        _fail("bpmn does not contain a bpmn:exclusiveGateway with a conditionExpression")
    print("OK: bpmn contains a multi-instance loop and a conditional exclusive gateway")

    # 2. LIVE ------------------------------------------------------------------
    project_dir = resolve_project(os.path.basename(bpmn_path))
    original_hash = sha256(Path(bpmn_path))

    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    solution_dir = LIVE_RUN_DIR / "JiraLifecycleLiveEval"
    initialized = run_cli(
        ["uip", "solution", "init", str(solution_dir)], timeout=SOLUTION_INIT_TIMEOUT
    )
    payload_data(initialized, "initialize ephemeral solution")
    solution_files = sorted(solution_dir.glob("*.uipx"))
    if len(solution_files) != 1:
        raise CheckFailure(
            f"solution init produced {len(solution_files)} .uipx files in "
            f"{solution_dir}, expected exactly one"
        )
    solution_file = solution_files[0]
    imported = run_cli(
        [
            "uip",
            "solution",
            "projects",
            "import",
            str(project_dir.resolve()),
            "--solutionFile",
            str(solution_file),
        ],
        timeout=SOLUTION_IMPORT_TIMEOUT,
    )
    payload_data(imported, "import exact BPMN project")
    imported_project = solution_dir / project_dir.name
    if sha256(imported_project / os.path.basename(bpmn_path)) != original_hash:
        raise CheckFailure("solution import changed the submitted BPMN bytes")
    print(f"OK: imported exact artifact (sha256={original_hash})")

    debug_data, instance_id = bpmn_live.run_debug(
        imported_project, {}, LIVE_RUN_DIR / "debug.log", timeout=720
    )
    print(f"OK: debug completed (instance {instance_id})")

    final_status = get_ci(debug_data, "FinalStatus")
    variables = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "variables-all", instance_id],
        timeout=VARIABLES_ALL_TIMEOUT,
    )
    _payload, variables_data = payload_data(variables, "variables-all")

    incidents = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "incidents", instance_id],
        timeout=INCIDENTS_TIMEOUT,
    )
    _payload, incidents_data = payload_data(incidents, "incidents")
    incidents_list = incident_records(incidents_data)

    if final_status not in COMPLETED_STATUSES:
        detail = []
        faulted = [
            f"{get_ci(item, 'ElementId')}={get_ci(item, 'Status')}"
            for item in get_ci(debug_data, "ElementExecutions", []) or []
            if isinstance(item, dict)
            and str(get_ci(item, "Status") or "").casefold() != "completed"
        ]
        if faulted:
            detail.append(f"non-completed elements: {faulted}")
        if incidents_list:
            detail.append(f"incidents: {json.dumps(incidents_list)[:1500]}")
        raise CheckFailure(
            f"final status was {final_status!r}"
            + ("; " + "; ".join(detail) if detail else "")
        )
    if incidents_list is None:
        raise CheckFailure(f"incidents response has an unknown shape: {incidents_data!r}")
    if incidents_list:
        raise CheckFailure(f"unexpected incidents: {incidents_list}")
    print("OK: bpmn debug completed (FinalStatus=%s, no incidents)" % final_status)

    # Every CE-<n> key that appears anywhere in the variables-all payload --
    # the create nodes' responses land in the runtime scopes/element outputs
    # regardless of how the process mapped them, mirroring Flow's own
    # whole-payload scan.
    variables_text = json.dumps(variables_data)
    cands = list(dict.fromkeys(re.findall(rf"\b{re.escape(project)}-\d+\b", variables_text)))
    if not cands:
        _fail(f"no issue key (e.g. {project}-123) in debug-instance variables-all -- the loop created nothing")
    print(f"OK: candidate keys from debug: {cands}")

    # 3. TENANT ------------------------------------------------------------
    conn = _connection_id()
    found: dict[str, str] = {}  # summary -> key, for issues that are ours
    for key in cands:
        fields = _get_issue(conn, key, project, issuetype_id)
        if not fields:
            continue
        _record_key(key)  # real issue this run created -- always clean it up
        summary = fields.get("summary")
        if summary in want_marker:
            found[summary] = key
            marker = want_marker[summary]
            comment_blob = json.dumps(fields.get("comment"))
            if marker not in comment_blob:
                _fail(
                    f"issue {key} ({summary!r}) is missing its expected branch "
                    f"comment {marker!r} -- the gateway routed it to the wrong "
                    f"branch (or no comment was posted)"
                )

    missing = [s for s in want_marker if s not in found]
    if missing:
        _fail(
            f"the loop did not create every seeded issue -- missing {missing}; "
            f"created and matched: {list(found.values())}"
        )

    print(f"OK: all {len(want_marker)} issues created and each carries its correct branch comment")
    print("PASS: all JiraLifecycle checks passed")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
