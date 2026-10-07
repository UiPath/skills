#!/usr/bin/env python3
"""JiraGetIssue (BPMN): structural + live checks.

Ported from Flow `e2e/jira_get_issue/_shared/check_jira_get_issue.py`: same
scenario (a manual-start process reads one pre-seeded Jira issue by key via
the Atlassian Jira "Get Issue" connector activity and exposes its summary),
translated from a JSON node walk + inline `flow debug` payload to an XML walk
over the registry-driven `Intsvc.ActivityExecution` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4) plus the
BPMN live-debug surface (`_shared/bpmn_live.py`, per LIVE-ADDENDUM's canonical
pattern: ephemeral solution import, `bpmn debug`, `debug-instance
variables-all`/`incidents`).

Exits non-zero on the first failure (``FAIL: ...``); prints ``OK: ...`` per
check. The issue is created/cleaned up by seed_jira.py / teardown_jira.py;
this check only reads the tenant through the process it grades, never
directly.

Assertion map (Flow → BPMN):
  F check_jira_get_issue.py:43   JIRA_KEY not in raw ('"nodes"' marker dropped -- XML has no JSON "nodes" key, see I
  below)
                                  → JIRA_KEY not in raw text of the .bpmn
  F check_jira_get_issue.py:46   GET_OP_RE.search(raw) (Get-Issue op referenced)
                                  → find_get_issue_nodes(): a sendTask carrying Intsvc.ActivityExecution
                                    whose connectorKey is uipath-atlassian-jira and whose objectName/method
                                    classify as Get Issue (curated `curated_get_issue` OR generic object
                                    `issue` + method GETBYID/GET -- catalog checked via
                                    `uip is activities list uipath-atlassian-jira --output json`)
  F check_jira_get_issue.py:48   issue_key not in raw            → issue_key not in raw text of the .bpmn
  F check_jira_get_issue.py:52   run_debug(...) implicitly requires finalStatus == "Completed"
                                  (flow_check.run_debug raises on a non-Completed status internally;
                                  `bpmn debug` returns only an instance id, so the check is explicit here)
                                  → FinalStatus in COMPLETED_STATUSES and debug-instance incidents is empty
  ADDED            a Get-Issue node completed in debug ElementExecutions (Flow's payload only carries
                    outputs of nodes that ran)
  F check_jira_get_issue.py:55   assert_outputs_contain(payload, seed["summary"])
                                  → seeded summary found in the Get-Issue node's own Outputs or the root
                                    Globals minus input echoes in `debug-instance variables-all`
                                    (LIVE-ADDENDUM: a root PUBLIC OUTPUT has read back null even when
                                    mapped correctly, so the search is not scoped to a declared output)
  I                locate/parse .bpmn (file exists, well-formed XML, project directory resolved)
                                  → bpmn_check.find_bpmn_file()/resolve_project()
  I                ephemeral solution init + `solution projects import` + sha256 pin of the imported
                    bytes against the submitted file -- `bpmn debug` runs against an imported project,
                    unlike `flow debug`, which runs directly against the discovered project directory
                                  → LIVE-ADDENDUM canonical live pattern (mirrors
                                    e2e/customer_escalation_triage/check_customer_escalation_behavior.py)
  T                GETBYID/GET equivalence; curated OR generic entity-CRUD classification (BATCH1-ADDENDUM)
                                  → find_get_issue_nodes()
  DROPPED          require_no_private_connector_values / require_sequence_integrity /
                    require_di_for_visible_elements / connection-binding checks -- not in Flow; the
                    `bpmn validate` criterion covers structure

No tenant re-read is performed (unlike the escalation Create-Issue port): this
task only GETs a pre-existing issue, so there is no newly-created record to
verify against the tenant, matching Flow's own grader.
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# …/uipath-maestro-bpmn (for _shared), same convention as _shared/check_drive_to_slack.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from _shared.bpmn_check import fail, find_bpmn_file, resolve_project  # noqa: E402
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    connector_context,
    debug_evidence,
    get_ci,
    import_exact,
    input_echo_ids,
    output_leaves,
    require_clean_run,
)

JIRA_KEY = "uipath-atlassian-jira"
GET_OP_RE = re.compile(r"get[\s_-]?issue|curated_get_issue", re.IGNORECASE)
GENERIC_OBJECT = "issue"
GENERIC_GET_METHODS = {"GETBYID", "GET"}
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
NAME_HINT = "JiraGetIssue"

LIVE_RUN_DIR = Path("jira-get-issue-live")

# Worst-case wall clock this checker can spend, priced the way
# _shared/test_criterion_budgets.py prices a run_debug(...) call: the debug
# call below passes no timeout/retries/backoff kwargs, so it prices at
# bpmn_live.debug_budget() == bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT (480).
# The surrounding CLI steps (solution init/import, variables-all, incidents)
# are not priced by that guard, so their sum is added by hand here and the
# criterion `timeout:` in jira_get_issue.yaml documents the arithmetic:
#   90 (solution init) + 180 (solution import) + 480 (debug)
#   + 120 (variables-all) + 120 (incidents) = 990
#   + bpmn_live.CRITERION_MARGIN_SECONDS (60) = 1050
# Flow's own criterion timeout (1080) already covers this, so it is kept
# verbatim rather than raised.


def is_get_issue_node(node_name: str, object_name: str, method: str) -> bool:
    """Curated (`curated_get_issue`) OR generic (`issue` + GETBYID/GET) form."""
    if GET_OP_RE.search(object_name or "") or GET_OP_RE.search(node_name or ""):
        return True
    return (
        (object_name or "").strip().lower() == GENERIC_OBJECT
        and (method or "").strip().upper() in GENERIC_GET_METHODS
    )


def find_get_issue_nodes(root: ET.Element) -> list[ET.Element]:
    """Every element carrying an Intsvc.ActivityExecution Jira Get-Issue op.

    Scans every descendant, not a fixed tag list (registry templates may emit
    a connector activity as sendTask, serviceTask, or a plain task) --
    mirrors bpmn_live.index_runtime_connectors' own scanning discipline.
    """
    found = []
    for node in root.iter():
        context = connector_context(node)
        if context.get("connectorKey") != JIRA_KEY:
            continue
        if not any(
            token in ET.tostring(node, encoding="unicode") for token in (ACTIVITY_TYPE,)
        ):
            continue
        node_name = node.attrib.get("name", "")
        if is_get_issue_node(node_name, context.get("objectName", ""), context.get("method", "")):
            found.append(node)
    return found


def completed_ids(debug_data: object, element_ids: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            get_ci(item, "ElementId")
            for item in get_ci(debug_data, "ElementExecutions", []) or []
            if isinstance(item, dict)
            and get_ci(item, "ElementId") in element_ids
            and str(get_ci(item, "Status") or "").casefold() == "completed"
        )
    )


def collect_output_haystack(
    variables_data: object, get_ids: tuple[str, ...], skip: set[str]
) -> str:
    """The Get-Issue node's own Outputs plus root Globals that are not input
    echoes, so a summary typed into an input cannot pass without the Get."""
    leaves = output_leaves(variables_data, skip, elements=get_ids)
    return "\n".join(str(v) for v in leaves).lower()


def main() -> None:
    seed_path = Path("seed.json")
    if not seed_path.is_file():
        fail("seed.json is missing from the sandbox (pre_run seed did not run)")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    issue_key = seed["issue_key"]

    bpmn_path = find_bpmn_file(NAME_HINT)
    raw = Path(bpmn_path).read_text(encoding="utf-8")
    if JIRA_KEY not in raw:
        fail(f"{bpmn_path} does not reference the {JIRA_KEY} connector")
    print(f"OK: bpmn references {JIRA_KEY}")

    try:
        root = ET.parse(bpmn_path).getroot()
    except ET.ParseError as exc:
        fail(f"{bpmn_path} is not well-formed XML: {exc}")

    get_issue_nodes = find_get_issue_nodes(root)
    if not get_issue_nodes:
        fail("bpmn does not reference a Jira Get-Issue connector node (Intsvc.ActivityExecution)")
    if issue_key not in raw:
        fail(f"bpmn does not reference the seeded key {issue_key!r} (agent must read it from seed.json)")
    print(f"OK: bpmn references a Get-Issue op and the seeded key {issue_key}")

    project_dir = resolve_project(os.path.basename(bpmn_path))
    imported_project = import_exact(
        Path(bpmn_path), project_dir, LIVE_RUN_DIR / "JiraGetIssueLiveEval"
    )

    debug_data, instance_id = bpmn_live.run_debug(
        imported_project, {}, LIVE_RUN_DIR / "debug.log"
    )
    print(f"OK: debug completed (instance {instance_id})")

    evidence = debug_evidence(instance_id)
    require_clean_run(debug_data, evidence)

    get_ids = tuple(node.attrib["id"] for node in get_issue_nodes if node.attrib.get("id"))
    ran = completed_ids(debug_data, get_ids)
    if not ran:
        fail(
            f"no Get-Issue node among {list(get_ids)} completed in the debug trace; "
            "the issue was not actually read"
        )
    print(f"OK: Get-Issue node(s) {list(ran)} completed")

    haystack = collect_output_haystack(evidence.variables, ran, input_echo_ids(root))
    if seed["summary"].lower() not in haystack:
        fail(
            f"Get-Issue outputs and non-input globals do not contain the seeded "
            f"issue summary {seed['summary']!r}\n"
            f"outputs: {haystack[:1000]}"
        )
    print("OK: bpmn outputs contain the seeded issue summary")
    print("PASS: all JiraGetIssue checks passed")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
