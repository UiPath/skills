#!/usr/bin/env python3
"""Verify the escalation BPMN actually creates a Jira ticket.

Ported from Flow's ``uipath-maestro-flow/e2e/escalation_jira_ticket/check_escalation_jira_ticket.py``,
adapted to the BPMN CLI surface the way ``e2e/customer_escalation_triage/``'s
``check_customer_escalation_behavior.py`` adapted the sibling Flow live check:
Flow's ``flow debug`` returns variables inline and addresses outputs by name;
``uip maestro bpmn debug`` returns an instance id whose evidence comes from
``debug-instance variables-all``/``incidents``, with runtime variables
addressed by id. No Slack step here — Flow's ``escalation_jira_ticket`` task
has none either (unlike ``customer_escalation_triage``, which is a different,
Jira+Slack scenario); only Flow's Jira assertions are ported.

Outcome-based, tenant-confirmed:
  1. The submitted BPMN references the uipath-atlassian-jira connector and
     declares the three public outputs plus one Jira Create-Issue activity.
  2. LIVE: the exact submitted project (sha256-pinned through solution
     import) runs the seeded Sev1 case via `uip maestro bpmn debug` inside an
     ephemeral solution under the sandbox CWD (repo-standard
     `_setup/cleanup_solutions.py` post_run sweep finds the .uipx there).
  3. TENANT: re-reading the created Jira key returns an issue whose summary
     carries the seeded correlationId — proof the process created THIS run's
     ticket, not a fabricated key.

Assertion map (Flow -> BPMN):
  I    locate/parse .bpmn (no pinned path -- prompt names only the process)  -> bpmn_check.parse_bpmn("EscalationJiraTicket") + resolve_project()
  F    check_escalation_jira_ticket.py:53-56   .flow references JIRA_KEY     -> .bpmn source text contains JIRA_KEY substring
  I    uipath:variables output ids / Jira Create-Issue element ids /         -> resolve_contract() (mirrors check_customer_escalation_behavior.py's Contract, Jira-only)
       scriptTask ids needed to address runtime evidence by id
  T    flow_check.run_debug(inputs=..., retries=1) -- single attempt,        -> ephemeral solution import (sha256-pinned) + bpmn_live.run_debug();
       finalStatus == "Completed" checked inline                               FinalStatus/incidents asserted explicitly afterward (LIVE-ADDENDUM
                                                                                 canonical live pattern; bpmn debug already makes one attempt, no backoff)
  F    check_escalation_jira_ticket.py:64-68    no whole-run retries          -> bpmn_live.run_debug has no retry/backoff parameter to begin with
       (a retried Create-Issue would duplicate the ticket)
  F    check_escalation_jira_ticket.py:70-90    except-branch: on a debug     -> on subprocess.TimeoutExpired from run_debug, scrape partial
       timeout, best-effort scrape partial output for <PROJECT>-\\d+             stdout/stderr for <PROJECT>-\\d+ candidates, keep only ones whose
       candidates, keep only ones owned (summary carries correlationId)         summary carries correlationId, journal them, then fail
  F    check_escalation_jira_ticket.py:104-106  Jira Create-Issue node        -> Jira Create-Issue element has exactly one Completed
       specifically must have completed (not merely any Jira node)              ElementExecutions record
  F    check_escalation_jira_ticket.py:108-111  candidate keys from           -> connector_response_values() on the Create-Issue element's OWN
       collect_outputs()/raw debug text, ISSUE_KEY_RE-shaped                     Outputs (element_output_records), value "key"
  F    check_escalation_jira_ticket.py:118-123  persist proven-created keys   -> journal the harvested key to `.created_keys` BEFORE the tenant
       BEFORE the fallible tenant reread                                        reread, mirroring the exemplar's harvest-before-assert order
  F    check_escalation_jira_ticket.py:129-140  tenant reread: get_issue(),   -> jira_is.get_issue(conn, key) (copied verbatim from Flow), summary
       summary contains correlationId, never an unrelated pre-existing issue    contains correlationId
  F    check_escalation_jira_ticket.py:143-149  created key must be in the    -> inherent by construction: jira_key is sourced ONLY from the
       executed Create-Issue node's OWN output                                  Create-Issue element's own Outputs (see harvest above)
  F    check_escalation_jira_ticket.py:154-155  assert_named_equals(          -> declared output `jiraIssueKey` resolved via its uipath:variables
       "jiraIssueKey", match, case_sensitive=True)                              output id (root scope Globals), compared case-sensitively
  F    check_escalation_jira_ticket.py:158-160  assert_named_equals per       -> same, via declared output ids; severity case-insensitive,
       seed["expected"] (severity case-insensitive, caseKey case-sensitive)      caseKey case-sensitive (CASE_SENSITIVE set, ported verbatim)
  F    check_escalation_jira_ticket.py:162-186  severity AND engineeringNeeded -> same binding, over bpmn:scriptTask elements' own Outputs
       bound to the SAME executed Script node, not split across two nodes        (element_output_records); a node's response value-pool must
                                                                                  contain both the expected severity and engineeringNeeded value
  T    check_escalation_jira_ticket.py's severity/engineeringNeeded lookup     -> matched against the VALUES of the scriptTask's own response
       is by normalized field NAME (find_node_output_value)                      dict rather than by key name (mirrors check_customer_escalation_
                                                                                  behavior.py's `carries()`, the CI-proven pattern for this exact
                                                                                  runtime shape, since BPMN scriptTask output key-naming is agent-
                                                                                  chosen and not part of the registry contract)

  DROPPED  check_customer_escalation_behavior.py's OUTPUT_TYPES exact_type()  (not in Flow -- assert_named_equals never type-checks output values)
           check on output values
  DROPPED  check_customer_escalation_behavior.py's Jira project.key/          (not in Flow -- Flow only checks the summary contains correlationId)
           issuetype.id remote-field re-check
  DROPPED  assert_live_target() tenant-lock guard                            (not in Flow's jira_is.py, which this task's _setup/jira_is.py is a
                                                                                verbatim copy of; not adding it keeps that copy faithful)

Budget arithmetic (LIVE-ADDENDUM): bpmn_live.debug_budget() default (480) +
SOLUTION_INIT_TIMEOUT (90) + SOLUTION_IMPORT_TIMEOUT (180) +
VARIABLES_ALL_TIMEOUT (120) + INCIDENTS_TIMEOUT (120) + one jira_is.
connection_id() call (120, hardcoded inside jira_is._run) + up to
MAX_CANDIDATE_ISSUE_READS jira_is.get_issue() calls (2 * 120 = 240) = 1350,
plus bpmn_live.CRITERION_MARGIN_SECONDS (60) = 1410 -- under Flow's original
1600s criterion timeout, so it is kept verbatim (see escalation_jira_ticket.yaml).

The confirmed key is written to `.created_keys` so post_run's `teardown_jira.py`
(copied verbatim from Flow) deletes it even if a later assertion fails.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))          # .../uipath-maestro-bpmn/_shared
SUITE_ROOT = os.path.dirname(HERE)                          # .../uipath-maestro-bpmn
TASK_SETUP = os.path.join(SUITE_ROOT, "e2e", "escalation_jira_ticket", "_setup")
sys.path.insert(0, TASK_SETUP)  # jira_is.py, copied verbatim from the Flow task
sys.path.insert(0, SUITE_ROOT)  # _shared package (bpmn_check, bpmn_live)

import jira_is  # noqa: E402
from _shared.bpmn_check import parse_bpmn, resolve_project  # noqa: E402
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    CheckFailure,
    connector_response_values,
    element_output_records,
    get_ci,
    incident_records,
    index_runtime_connectors,
    payload_data,
    q,
    resolve_runtime_key,
    root_scope,
    run_cli,
    run_debug,
    sha256,
    UIPATH_NS,
)

JIRA_CONNECTOR = jira_is.CONNECTOR  # "uipath-atlassian-jira"
JIRA_CREATE_OP = "curated_create_issue"  # matches the catalog op customer_escalation_triage's exemplar graded against
ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
CASE_SENSITIVE = {"caseKey", "jiraIssueKey"}  # opaque ids -- exact-case match
OUTPUT_NAMES = ("severity", "caseKey", "jiraIssueKey")
COMPLETED_STATUSES = {"Completed", "Successful"}

LIVE_RUN_DIR = Path("escalation-jira-live")
SOLUTION_INIT_TIMEOUT = 90
SOLUTION_IMPORT_TIMEOUT = 180
VARIABLES_ALL_TIMEOUT = 120
INCIDENTS_TIMEOUT = 120
MAX_CANDIDATE_ISSUE_READS = 2  # headroom; one Create-Issue node normally executes once


def _fail(msg: str) -> None:
    raise CheckFailure(msg)


def _normalized(value, *, case_fold: bool = True):
    """Mirror flow_check.normalized: trim strings, coerce true/false, fold case
    for enum-like values. Pass case_fold=False for opaque identifiers."""
    if isinstance(value, str):
        text = value.strip()
        lowered = text.casefold()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        return lowered if case_fold else text
    return value


@dataclass(frozen=True)
class Contract:
    output_ids: dict
    jira_create_ids: tuple
    classifier_ids: tuple


def resolve_contract(root: ET.Element) -> Contract:
    process = root.find(q(BPMN_NS, "process"))
    if process is None:
        _fail("BPMN must contain one root process")

    variables = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'variables')}"
    )
    if variables is None:
        _fail("root process is missing uipath:variables")
    output_ids: dict = {}
    for variable in variables:
        name = variable.attrib.get("name")
        identifier = variable.attrib.get("id")
        if (
            variable.tag.rsplit("}", 1)[-1] != "output"
            or not name
            or not identifier
            or name not in OUTPUT_NAMES
        ):
            continue
        if name in output_ids:
            _fail(f"public output {name!r} is declared more than once")
        output_ids[name] = identifier
    missing = sorted(set(OUTPUT_NAMES) - set(output_ids))
    if missing:
        _fail(f"public outputs not declared: {missing}")

    # Every scriptTask that could be the classifier -- Flow binds severity to
    # the executed Script whose own output carries it; without an equivalent, a
    # process that exposes a literal "Sev1" (computing nothing) would satisfy
    # every other criterion here.
    classifier_ids = tuple(
        element.attrib["id"]
        for element in process.iter(q(BPMN_NS, "scriptTask"))
        if element.attrib.get("id")
    )
    if not classifier_ids:
        _fail(
            "no bpmn:scriptTask to classify severity; the value would be a "
            "literal rather than computed"
        )

    connectors = index_runtime_connectors(process)
    jira_create_ids = tuple(
        element_id
        for (key, route), element_ids in connectors.items()
        if key == JIRA_CONNECTOR and JIRA_CREATE_OP in route
        for element_id in element_ids
    )
    if not jira_create_ids:
        _fail(
            f"no {JIRA_CONNECTOR} activity with a registry path containing "
            f"{JIRA_CREATE_OP!r}"
        )

    return Contract(
        output_ids=output_ids,
        jira_create_ids=jira_create_ids,
        classifier_ids=classifier_ids,
    )


def _harvest_jira_keys(contract: Contract, variables_data) -> list:
    """Candidate Jira keys from the Create-Issue element's OWN Outputs.

    Called (and journalled) BEFORE any assertion -- the debug already created
    a real issue, and this read is the only place its key appears.
    """
    outputs = element_output_records(variables_data, contract.jira_create_ids)
    keys = [v for v in connector_response_values(outputs, "key") if isinstance(v, str)]
    return list(dict.fromkeys(keys))


def _journal(keys) -> None:
    if keys:
        Path(".created_keys").write_text("\n".join(keys) + "\n")


def _recover_partial_keys(project_key: str, correlation: str, raw_text: str) -> list:
    """Best-effort: on a client-side debug timeout, the Create-Issue call may
    already have succeeded server-side. Scrape any <PROJECT>-<n> candidates
    from partial CLI output and keep only ones tenant-confirmed as THIS run's
    (summary carries correlationId) -- never an unrelated pre-existing issue.
    Mirrors Flow's except-branch (check_escalation_jira_ticket.py:70-90)."""
    cands = list(dict.fromkeys(re.findall(rf"\b{re.escape(project_key)}-\d+\b", raw_text)))
    if not cands:
        return []
    try:
        conn = jira_is.connection_id()
    except SystemExit:
        return []
    owned = []
    for key in cands:
        try:
            fields = jira_is.get_issue(conn, key)
        except Exception:  # noqa: BLE001 -- best-effort recovery, never mask the real failure
            continue
        if fields is not None and correlation in str(fields.get("summary", "")):
            owned.append(key)
    return owned


def main() -> None:
    seed = json.loads(Path("seed.json").read_text(encoding="utf-8"))
    correlation = seed["correlationId"]
    project_key = seed["project_key"]

    bpmn_path, root = parse_bpmn("EscalationJiraTicket")
    bpmn_text = Path(bpmn_path).read_text(encoding="utf-8")
    if JIRA_CONNECTOR not in bpmn_text:
        _fail(f"no .bpmn references the {JIRA_CONNECTOR} connector (found {bpmn_path})")
    print(f"OK: BPMN references {JIRA_CONNECTOR}")

    contract = resolve_contract(root)
    project_dir = resolve_project(os.path.basename(bpmn_path))
    original_hash = sha256(Path(bpmn_path))

    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    solution_dir = LIVE_RUN_DIR / "EscalationJiraLiveEval"
    initialized = run_cli(["uip", "solution", "init", str(solution_dir)], timeout=SOLUTION_INIT_TIMEOUT)
    payload_data(initialized, "initialize ephemeral solution")
    solution_files = sorted(solution_dir.glob("*.uipx"))
    if len(solution_files) != 1:
        _fail(
            f"solution init produced {len(solution_files)} .uipx files in "
            f"{solution_dir}, expected exactly one"
        )
    solution_file = solution_files[0]
    imported = run_cli(
        [
            "uip", "solution", "projects", "import", str(project_dir.resolve()),
            "--solutionFile", str(solution_file),
        ],
        timeout=SOLUTION_IMPORT_TIMEOUT,
    )
    payload_data(imported, "import exact BPMN project")
    imported_project = solution_dir / project_dir.name
    if sha256(imported_project / os.path.basename(bpmn_path)) != original_hash:
        _fail("solution import changed the submitted BPMN bytes")
    print(f"OK: imported exact artifact (sha256={original_hash})")

    # No whole-run retries: this process CREATES a Jira issue, so a retried
    # whole run on a transient error could create a duplicate ticket that this
    # checker (deriving keys from the final attempt) wouldn't see or clean up.
    # bpmn_live.run_debug makes a single attempt with no backoff by design.
    log_file = LIVE_RUN_DIR / "debug.log"
    try:
        debug_data, instance_id = run_debug(imported_project, seed["inputs"], log_file)
    except subprocess.TimeoutExpired as exc:
        partial = "".join(
            s.decode() if isinstance(s, bytes) else (s or "") for s in (exc.stdout, exc.stderr)
        )
        owned = _recover_partial_keys(project_key, correlation, partial)
        _journal(owned)
        _fail(
            f"bpmn debug timed out after {exc.timeout}s"
            + (f"; recorded this-run key(s) {owned} for teardown" if owned else "")
        )
    print(f"OK: debug completed (instance {instance_id})")

    variables = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "variables-all", instance_id],
        timeout=VARIABLES_ALL_TIMEOUT,
    )
    _payload, variables_data = payload_data(variables, "variables-all")

    # Journal the created key BEFORE any assertion -- it was created regardless
    # of the verdict below, and post_run's teardown_jira.py replays the journal
    # even if this process is killed mid-assertion.
    jira_keys = _harvest_jira_keys(contract, variables_data)
    _journal(jira_keys)

    incidents = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "incidents", instance_id],
        timeout=INCIDENTS_TIMEOUT,
    )
    _payload, incidents_data = payload_data(incidents, "incidents")

    final_status = get_ci(debug_data, "FinalStatus")
    if final_status not in COMPLETED_STATUSES:
        faulted = [
            f"{get_ci(item, 'ElementId')}={get_ci(item, 'Status')}"
            for item in get_ci(debug_data, "ElementExecutions", []) or []
            if isinstance(item, dict)
            and str(get_ci(item, "Status") or "").casefold() != "completed"
        ]
        records = incident_records(incidents_data)
        detail = []
        if faulted:
            detail.append(f"non-completed elements: {faulted}")
        if records:
            detail.append(f"incidents: {json.dumps(records)[:1500]}")
        _fail(f"bpmn debug did not complete (finalStatus={final_status})" + ("; " + "; ".join(detail) if detail else ""))
    print("OK: bpmn debug completed")

    records = incident_records(incidents_data)
    if records is None:
        _fail(f"incidents response has an unknown shape: {incidents_data!r}")
    if records:
        _fail(f"unexpected incidents: {records}")

    # Execution evidence: the Jira CREATE-ISSUE element specifically must have
    # executed (not merely any Jira element -- a read op could surface an
    # authoring-time key).
    executions = get_ci(debug_data, "ElementExecutions", [])
    executed_ids = [get_ci(item, "ElementId") for item in executions if isinstance(item, dict)]
    count = sum(executed_ids.count(eid) for eid in contract.jira_create_ids)
    if count < 1:
        _fail(
            "no Jira Create-Issue element completed in the debug trace -- the "
            "debugged BPMN did not execute the Create Issue activity"
        )

    if not jira_keys:
        _fail(
            f"no Jira issue key (e.g. {project_key}-123) in the Create-Issue "
            "element's own output -- the process did not create a ticket"
        )
    print(f"OK: candidate keys from debug: {jira_keys}")

    conn = jira_is.connection_id()

    # Tenant-confirm: the key belongs to THIS run -- an issue whose summary
    # carries this run's correlationId. Never deletes an unrelated
    # pre-existing issue.
    owned = [
        k for k in jira_keys
        for fields in [jira_is.get_issue(conn, k)]
        if fields is not None and correlation in str(fields.get("summary", ""))
    ]
    _journal(owned or jira_keys)  # re-journal narrowed to confirmed-owned when possible
    if not owned:
        _fail(
            f"none of {jira_keys} is a Jira issue whose summary contains "
            f"{correlation!r} -- the process did not create the expected "
            "escalation ticket"
        )
    match = owned[0]
    print(f"OK: Jira ticket {match} exists and its summary carries {correlation!r}")

    # Public outputs, addressed by id in the root scope's globals.
    globals_map = get_ci(root_scope(variables_data), "Globals", {})
    if not isinstance(globals_map, dict):
        _fail(f"root scope Globals is not a map: {globals_map!r}")

    def assert_named_equals(name: str, expected, *, case_sensitive: bool = False) -> None:
        identifier = contract.output_ids[name]
        actual = resolve_runtime_key(globals_map, identifier, name)
        if actual is None or (isinstance(actual, str) and not actual.strip()):
            _fail(f"output {name!r} missing or empty")
        if _normalized(actual, case_fold=not case_sensitive) != _normalized(expected, case_fold=not case_sensitive):
            _fail(f"output {name!r}: expected {expected!r}, got {actual!r}")

    # The exposed jiraIssueKey must be the executed Create-Issue element's OWN
    # response key -- harvesting some other key cannot satisfy this (jira_keys
    # is sourced only from that element's Outputs, so this is inherent).
    assert_named_equals("jiraIssueKey", match, case_sensitive=True)

    for name, expected in (seed.get("expected") or {}).items():
        assert_named_equals(name, expected, case_sensitive=(name in CASE_SENSITIVE))

    # Severity must be COMPUTED, not exposed as a literal, AND bound to the
    # SAME executed scriptTask that also carries engineeringNeeded -- Flow
    # requires both fields from ONE node, not split across two cosmetic Scripts.
    expected_severity = (seed.get("expected") or {}).get("severity")
    expected_script = seed.get("expected_script") or {}

    def node_carries_all(node_id: str) -> bool:
        for record in element_output_records(variables_data, node_id):
            response = get_ci(record, "response")
            pool = list(response.values()) if isinstance(response, dict) else [response]
            if not any(_normalized(v) == _normalized(expected_severity) for v in pool):
                continue
            if all(
                any(_normalized(v) == _normalized(expected_value) for v in pool)
                for expected_value in expected_script.values()
            ):
                return True
        return False

    if not any(node_carries_all(nid) for nid in contract.classifier_ids):
        _fail(
            "no single executed scriptTask carries the expected severity AND "
            f"classification fields together (severity={expected_severity!r}, "
            f"{expected_script})"
        )

    print("PASS: escalation BPMN created a real Jira ticket with the expected classification")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
