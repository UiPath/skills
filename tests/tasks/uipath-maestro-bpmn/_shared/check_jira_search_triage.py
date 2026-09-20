#!/usr/bin/env python3
"""JiraSearchTriage (BPMN): structural + live + tenant checks for a
JQL-search-driven triage process.

Ported from Flow `e2e/jira_search_triage/_shared/check_jira_search_triage.py`:
same scenario (a manual-start process searches Jira by a seeded JQL and, for
each match, adds a triage comment via a loop), translated from a JSON node
walk + inline `flow debug` payload to an XML walk over the registry-driven
`Intsvc.ActivityExecution` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4) plus the
BPMN live-debug surface (`_shared/bpmn_live.py`, per LIVE-ADDENDUM's canonical
pattern: ephemeral solution import, `bpmn debug`, `debug-instance incidents`).
The loop construct is `bpmn:multiInstanceLoopCharacteristics` (see
skills/uipath-maestro-bpmn/references/structural-bpmn.md), the BPMN
translation of Flow's `core.logic.loop` node type.

Exits non-zero on the first failure (``FAIL: ...``); prints ``OK: ...`` per
check. The two issues are created/cleaned up by seed_jira.py /
teardown_jira.py; this check only reads the tenant through the process it
grades, never directly.

Assertion map (Flow → BPMN):
  F check_jira_search_triage.py:40   JIRA_KEY not in raw ('"nodes"' marker dropped -- XML has no JSON "nodes" key, see I below)
                                      → JIRA_KEY not in raw text of the .bpmn
  F check_jira_search_triage.py:43   SEARCH_OP_RE.search(raw) (Search-Issues-by-JQL op referenced)
                                      → find_search_issue_nodes(): a sendTask carrying Intsvc.ActivityExecution
                                        whose connectorKey is uipath-atlassian-jira and whose objectName/method
                                        classify as Search Issues by JQL (curated `issue_search_get` OR a generic
                                        GET node whose serialized XML contains a `jql` token -- catalog checked
                                        via `uip is activities list uipath-atlassian-jira --output json`)
  F check_jira_search_triage.py:45   assert_flow_has_node_type(["core.logic.loop"])
                                      → has_loop(): at least one bpmn:multiInstanceLoopCharacteristics element
                                        (PORTING-BRIEF construct-translation table: Loop → multiInstanceLoopCharacteristics)
  F check_jira_search_triage.py:48   run_debug(timeout=600) implicitly requires finalStatus == "Completed"
                                      (flow_check.run_debug raises on a non-Completed status internally;
                                      `bpmn debug` returns only an instance id, so the check is explicit here)
                                      → FinalStatus in COMPLETED_STATUSES and debug-instance incidents is empty
  F check_jira_search_triage.py:51-60 conn = jira_is.connection_id(); for key in issue_keys: re-read + assert
                                      marker in fields["comment"]
                                      → identical tenant re-read against the same jira_is.py helper, unchanged
  I                 locate/parse .bpmn (file exists, well-formed XML, project directory resolved)
                                      → bpmn_check.find_bpmn_file()/resolve_project()
  I                 ephemeral solution init + `solution projects import` + sha256 pin of the imported
                     bytes against the submitted file -- `bpmn debug` runs against an imported project,
                     unlike `flow debug`, which runs directly against the discovered project directory
                                      → LIVE-ADDENDUM canonical live pattern (mirrors
                                        e2e/jira_get_issue/check_jira_get_issue.py)
  T                 curated OR generic entity-CRUD classification (BATCH1-ADDENDUM); GET/GETBYID
                     equivalence not needed here (search is GET-only), but the same dual-form tolerance
                     (curated objectName vs generic object+method) applies
                                      → is_search_issue_node()
  DROPPED           require_no_private_connector_values / require_sequence_integrity /
                     require_di_for_visible_elements / connection-binding checks -- not in Flow; the
                     `bpmn validate` criterion covers structure. No structural check for the Add-Comment
                     node either -- Flow's own grader never asserts one (it proves the comment landed via
                     the tenant re-read instead), so none is added here.

No output-value assertion is made (unlike the jira_get_issue port): Flow's own
grader never reads `flow debug`'s output payload for this task, only the
tenant re-read, so `debug-instance variables-all` is not called here.
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))  # …/uipath-maestro-bpmn/_shared
# …/uipath-maestro-bpmn (for _shared), same convention as _shared/check_jira_get_issue.py
sys.path.insert(0, os.path.dirname(HERE))  # noqa: E402
# This task's own _setup/ in the repo (not the sandbox mount -- this checker
# runs from $REFERENCE_DIR, so it reads jira_is.py straight off disk here,
# the same way check_customer_escalation_behavior.py reads its own HERE/_setup).
# No new _shared module is added (BATCH1-ADDENDUM: agents write in parallel,
# do not add new shared modules) -- this imports the verbatim per-task copy.
sys.path.insert(0, os.path.join(HERE, "..", "e2e", "jira_search_triage", "_setup"))  # noqa: E402

from _shared.bpmn_check import elements, find_bpmn_file, resolve_project  # noqa: E402
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    connector_context,
    get_ci,
    incident_records,
    payload_data,
    run_cli,
    sha256,
)
import jira_is  # noqa: E402

JIRA_KEY = "uipath-atlassian-jira"
SEARCH_OP_RE = re.compile(r"search[\s_-]?issues?|issue_search_get|search-issues-by-jql", re.IGNORECASE)
GENERIC_SEARCH_OBJECTS = {"issue", "issues"}
GENERIC_SEARCH_METHODS = {"GET"}
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
NAME_HINT = "JiraSearchTriage"

LIVE_RUN_DIR = Path("jira-search-triage-live")
SOLUTION_INIT_TIMEOUT = 90
SOLUTION_IMPORT_TIMEOUT = 180
INCIDENTS_TIMEOUT = 120
COMPLETED_STATUSES = {"Completed", "Successful"}

# Worst-case wall clock this checker can spend, priced the way
# _shared/test_criterion_budgets.py prices a run_debug(...) call: the debug
# call below passes no timeout/retries/backoff kwargs, so it prices at
# bpmn_live.debug_budget() == bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT (480).
# The surrounding CLI steps (solution init/import, incidents) and the tenant
# re-read through jira_is.py (whose `_run` helper hardcodes a 120s subprocess
# timeout per call) are not priced by that guard, so their sum is added by
# hand here and the criterion `timeout:` in jira_search_triage.yaml documents
# the arithmetic:
#   90 (solution init) + 180 (solution import) + 480 (debug) + 120 (incidents)
#   + 240 (connection_id: 2 tenant calls @ up to 120s each)
#   + 240 (2 x get_issue re-read @ up to 120s each, one per seeded issue)
#   = 1350 + bpmn_live.CRITERION_MARGIN_SECONDS (60) = 1410
# Flow's own criterion timeout (1320) does not cover the extra ephemeral-
# solution import + live tenant re-read plumbing this BPMN sequence needs
# beyond Flow's single inline `flow debug` call, so it is raised to 1440
# (the one sanctioned deviation from "criteria identical" per LIVE-ADDENDUM's
# Budgets section -- a property of the CLI surface, not of what is graded).


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def is_search_issue_node(node_name: str, object_name: str, method: str, node_xml: str) -> bool:
    """Curated (`issue_search_get`) OR generic (GET + a `jql` token anywhere
    in the node) form. The `jql` token requirement keeps a generic GET node
    from being mistaken for search: BATCH1-ADDENDUM's dual-form tolerance
    classifies by objectName/method, but Search Issues by JQL has no distinct
    generic object name of its own (unlike Get Issue's `issue`+GETBYID)."""
    if SEARCH_OP_RE.search(object_name or "") or SEARCH_OP_RE.search(node_name or ""):
        return True
    return (
        (object_name or "").strip().lower() in GENERIC_SEARCH_OBJECTS
        and (method or "").strip().upper() in GENERIC_SEARCH_METHODS
        and "jql" in node_xml.lower()
    )


def find_search_issue_nodes(root: ET.Element) -> list[ET.Element]:
    """Every element carrying an Intsvc.ActivityExecution Jira Search-Issues op.

    Scans every descendant, not a fixed tag list (registry templates may emit
    a connector activity as sendTask, serviceTask, or a plain task) --
    mirrors bpmn_live.index_runtime_connectors' own scanning discipline.
    """
    found = []
    for node in root.iter():
        context = connector_context(node)
        if context.get("connectorKey") != JIRA_KEY:
            continue
        node_xml = ET.tostring(node, encoding="unicode")
        if ACTIVITY_TYPE not in node_xml:
            continue
        node_name = node.attrib.get("name", "")
        if is_search_issue_node(node_name, context.get("objectName", ""), context.get("method", ""), node_xml):
            found.append(node)
    return found


def has_loop(root: ET.Element) -> bool:
    return bool(elements(root, "multiInstanceLoopCharacteristics"))


def main() -> None:
    seed_path = Path("seed.json")
    if not seed_path.is_file():
        _fail("seed.json is missing from the sandbox (pre_run seed did not run)")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))

    bpmn_path = find_bpmn_file(NAME_HINT)
    raw = Path(bpmn_path).read_text(encoding="utf-8")
    if JIRA_KEY not in raw:
        _fail(f"{bpmn_path} does not reference the {JIRA_KEY} connector")
    print(f"OK: bpmn references {JIRA_KEY}")

    try:
        root = ET.parse(bpmn_path).getroot()
    except ET.ParseError as exc:
        _fail(f"{bpmn_path} is not well-formed XML: {exc}")

    if not find_search_issue_nodes(root):
        _fail("bpmn does not reference a Jira Search-Issues-by-JQL connector node (Intsvc.ActivityExecution)")
    if not has_loop(root):
        _fail("bpmn does not contain a multiInstanceLoopCharacteristics loop over the search results")
    print("OK: bpmn references a JQL search op and a loop construct")

    project_dir = resolve_project(os.path.basename(bpmn_path))
    original_hash = sha256(Path(bpmn_path))

    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    solution_dir = LIVE_RUN_DIR / "JiraSearchTriageLiveEval"
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
        imported_project, {}, LIVE_RUN_DIR / "debug.log"
    )
    print(f"OK: debug completed (instance {instance_id})")

    final_status = get_ci(debug_data, "FinalStatus")
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

    conn = jira_is.connection_id()
    marker = seed["processed_comment"]
    for key in seed["issue_keys"]:
        fields = jira_is.get_issue(conn, key)
        if not fields:
            _fail(f"seeded issue {key} not found on re-read")
        if marker not in json.dumps(fields.get("comment")):
            _fail(
                f"issue {key} is missing the triage comment {marker!r} — the "
                "search-driven loop did not comment it"
            )
    print(f"OK: all {len(seed['issue_keys'])} matched issues carry the triage comment")
    print("PASS: all JiraSearchTriage checks passed")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
