#!/usr/bin/env python3
"""JiraCreateIssue (BPMN): structural + live + tenant checks.

Ported from Flow `e2e/jira_create_issue/_shared/check_jira_create_issue.py`:
same scenario (a manual-start process creates one Jira issue via the
Atlassian Jira "Create Issue" connector activity using seeded field values,
then exposes the new issue's key), translated from a JSON node walk + inline
`flow debug` payload to an XML walk over the registry-driven
`Intsvc.ActivityExecution` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4) plus the
BPMN live-debug surface (`_shared/bpmn_live.py`, per LIVE-ADDENDUM's
canonical pattern: ephemeral solution import, `bpmn debug`, `debug-instance
variables-all`/`incidents`).

Exits non-zero on the first failure (``FAIL: ...``); prints ``OK: ...`` per
check. Every key the Create-Issue node reported is journaled to
``.created_keys`` so post_run teardown (`teardown_jira.py`) deletes them even
if a later step fails.

Assertion map (Flow -> BPMN):
  F check_jira_create_issue.py:49  JIRA_KEY not in raw or '"nodes"' not in raw
                                    ('"nodes"' marker dropped -- XML has no JSON "nodes" key, see I below)
                                    -> JIRA_KEY not in raw text of the .bpmn
  T                curated OR generic entity-CRUD classification (BATCH1-ADDENDUM);
                    catalog checked via `uip is activities list uipath-atlassian-jira
                    --output json` (CreateIssue -> objectName curated_create_issue,
                    method POST; generic form mirrors sibling script
                    check_jira_get_issue.py's GENERIC_OBJECT="issue" convention)
                                    -> find_create_issue_nodes(): a sendTask carrying
                                       Intsvc.ActivityExecution whose connectorKey is
                                       uipath-atlassian-jira and whose objectName/method
                                       classify as Create Issue
  ADDED (T)        not gated by Flow's own create script (which relies solely on the
                    tenant re-read below); translates the PROMPT requirement shared by
                    both suites ("use project_key/issuetype_id/summary/reporter_id
                    exactly as given") using the same literal-value technique as sibling
                    script check_jira_get_issue.py's F-tagged `issue_key not in raw`
                    check (its line 48) -- fails fast on an invented value before
                    spending the live-debug budget, without narrowing anything Flow's
                    own create script accepts (the tenant re-read below still gates)
                                    -> each of seed["project_key"], seed["issuetype_id"],
                                       seed["summary"], seed["reporter_id"] found
                                       literally, anywhere in the raw .bpmn text
  F check_jira_create_issue.py:53  run_debug(timeout=480) implicitly requires
                                    finalStatus == "Completed" (flow_check.run_debug
                                    raises on a non-Completed status internally; `bpmn
                                    debug` returns only an instance id, so the check is
                                    explicit here)
                                    -> FinalStatus in COMPLETED_STATUSES and
                                       debug-instance incidents is empty
  F check_jira_create_issue.py:58-61  candidate issue keys: clean output leaves
                                    (`collect_outputs(payload)`) + a project-scoped
                                    regex scan of the raw debug payload
                                    (`get_last_debug_raw()`)
                                    -> collect_candidate_keys(): the same project-scoped
                                       regex, narrowed to the Create-Issue element(s)'
                                       own Outputs in `debug-instance variables-all`, so
                                       no other CE issue key reaches the journal
  F check_jira_create_issue.py:62-63  no candidate keys -> fail
                                    -> same
  F check_jira_create_issue.py:66-77  tenant re-read via jira_is.get_issue(conn, key);
                                    first candidate whose `summary` equals the seed
                                    summary wins; confirmed key journaled for teardown
                                    -> same logic; `.created_keys` keeps every key the
                                       Create node reported; jira_is.py (task's own
                                       `_setup/jira_is.py` copy, imported via the
                                       sandbox-mounted path since this checker lives in
                                       `_shared/`, not the task dir)
  I                locate/parse .bpmn (file exists, well-formed XML, project directory
                    resolved); ephemeral solution init + `solution projects import` +
                    sha256 pin of the imported bytes against the submitted file --
                    `bpmn debug` runs against an imported project, unlike `flow debug`,
                    which runs directly against the discovered project directory
                                    -> LIVE-ADDENDUM canonical live pattern (mirrors
                                       e2e/customer_escalation_triage/
                                       check_customer_escalation_behavior.py and
                                       check_jira_get_issue.py)
  T                journal every candidate key BEFORE the status/incident checks and
                    the tenant-confirmation loop (LIVE-ADDENDUM: "side-effect ids go
                    to a flat journal the moment they are visible") -- Flow's own
                    script only journals the confirmed match, but an issue created by
                    a run that later faults is still a real tenant record
                                    -> `.created_keys` written right after variables-all,
                                       one key per line
  DROPPED          require_no_private_connector_values / require_sequence_integrity /
                    require_di_for_visible_elements / connection-binding checks --
                    not in Flow; the `bpmn validate` criterion covers structure
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# …/uipath-maestro-bpmn (for _shared), same convention as check_jira_get_issue.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from _shared.bpmn_check import fail, find_bpmn_file, resolve_project  # noqa: E402
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    DebugEvidence,
    connector_context,
    connector_response_values,
    element_output_records,
    fetch_incidents,
    fetch_variables,
    import_exact,
    require_clean_run,
)

JIRA_KEY = "uipath-atlassian-jira"
CREATE_OP_RE = re.compile(r"create[\s_-]?issue|curated_create_issue", re.IGNORECASE)
GENERIC_OBJECT = "issue"
GENERIC_CREATE_METHODS = {"POST"}
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
NAME_HINT = "JiraCreateIssue"
SEED_LITERAL_FIELDS = ("project_key", "issuetype_id", "summary", "reporter_id")

LIVE_RUN_DIR = Path("jira-create-issue-live")
JOURNAL = Path(".created_keys")

# Worst-case wall clock this checker can spend, priced the way
# _shared/test_criterion_budgets.py prices a run_debug(...) call: the debug
# call below passes no timeout/retries/backoff kwargs, so it prices at
# bpmn_live.debug_budget() == bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT (480).
# The surrounding CLI steps (solution init/import, variables-all, incidents)
# are not priced by that guard, so their sum is added by hand here and the
# criterion `timeout:` in jira_create_issue.yaml documents the arithmetic:
#   90 (solution init) + 180 (solution import) + 480 (debug)
#   + 120 (variables-all) + 120 (incidents) = 990
#   + bpmn_live.CRITERION_MARGIN_SECONDS (60) = 1050
# Flow's own criterion timeout (1080) already covers this, so it is kept
# verbatim rather than raised.


def _import_jira_is():
    """Lazy import so an empty/pre-authoring sandbox fails cleanly on the
    seed.json/bpmn checks above, rather than an ImportError traceback here.

    This checker lives in `_shared/`, not the task dir, so `jira_is` is not a
    sibling module (unlike escalation_is.py, imported from the task's own
    `_setup/`). Grading runs with CWD at the sandbox root, where the task's
    `_setup/jira_is.py` is mounted -- the same file pre_run/post_run use.
    """
    sys.path.insert(0, os.path.abspath("_setup"))
    try:
        import jira_is  # noqa: PLC0415
    except ImportError as exc:
        raise CheckFailure(f"jira_is module not found under _setup/ ({exc})") from exc
    return jira_is


def is_create_issue_node(node_name: str, object_name: str, method: str) -> bool:
    """Curated (`curated_create_issue`) OR generic (`issue` + POST) form."""
    if CREATE_OP_RE.search(object_name or "") or CREATE_OP_RE.search(node_name or ""):
        return True
    return (
        (object_name or "").strip().lower() == GENERIC_OBJECT
        and (method or "").strip().upper() in GENERIC_CREATE_METHODS
    )


def find_create_issue_nodes(root: ET.Element) -> list[ET.Element]:
    """Every element carrying an Intsvc.ActivityExecution Jira Create-Issue op.

    Scans every descendant, not a fixed tag list (registry templates may emit
    a connector activity as sendTask, serviceTask, or a plain task) --
    mirrors check_jira_get_issue.py's find_get_issue_nodes().
    """
    found = []
    for node in root.iter():
        context = connector_context(node)
        if context.get("connectorKey") != JIRA_KEY:
            continue
        if ACTIVITY_TYPE not in ET.tostring(node, encoding="unicode"):
            continue
        node_name = node.attrib.get("name", "")
        if is_create_issue_node(node_name, context.get("objectName", ""), context.get("method", "")):
            found.append(node)
    return found


def collect_candidate_keys(
    variables_data: object, create_ids: tuple[str, ...], project: str
) -> list[str]:
    outputs = element_output_records(variables_data, create_ids)
    key_re = re.compile(rf"{re.escape(project)}-\d+")
    cands = [
        key.strip()
        for key in connector_response_values(outputs, "key")
        if isinstance(key, str) and key_re.fullmatch(key.strip())
    ]
    return list(dict.fromkeys(cands))


def _journal(keys: list[str]) -> None:
    if keys:
        JOURNAL.write_text("\n".join(keys) + "\n")


def main() -> None:
    seed_path = Path("seed.json")
    if not seed_path.is_file():
        fail("seed.json is missing from the sandbox (pre_run seed did not run)")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    project = seed["project_key"]

    bpmn_path = find_bpmn_file(NAME_HINT)
    raw = Path(bpmn_path).read_text(encoding="utf-8")
    if JIRA_KEY not in raw:
        fail(f"{bpmn_path} does not reference the {JIRA_KEY} connector")
    print(f"OK: bpmn references {JIRA_KEY}")

    try:
        root = ET.parse(bpmn_path).getroot()
    except ET.ParseError as exc:
        fail(f"{bpmn_path} is not well-formed XML: {exc}")

    create_nodes = find_create_issue_nodes(root)
    if not create_nodes:
        fail("bpmn does not reference a Jira Create-Issue connector node (Intsvc.ActivityExecution)")
    print("OK: bpmn references a Create-Issue op")

    missing = [field for field in SEED_LITERAL_FIELDS if str(seed[field]) not in raw]
    if missing:
        fail(
            "bpmn does not reference the seeded "
            f"{', '.join(f'{field}={seed[field]!r}' for field in missing)} "
            "(agent must use seed.json values verbatim, not invented ones)"
        )
    print("OK: bpmn references the seeded project_key/issuetype_id/summary/reporter_id")

    project_dir = resolve_project(os.path.basename(bpmn_path))
    imported_project = import_exact(
        Path(bpmn_path), project_dir, LIVE_RUN_DIR / "JiraCreateIssueLiveEval"
    )

    debug_data, instance_id = bpmn_live.run_debug(
        imported_project, {}, LIVE_RUN_DIR / "debug.log"
    )
    print(f"OK: debug completed (instance {instance_id})")

    variables_data, variables_text = fetch_variables(instance_id)
    create_ids = tuple(node.attrib["id"] for node in create_nodes if node.attrib.get("id"))
    cands = collect_candidate_keys(variables_data, create_ids, project)
    _journal(cands)

    incidents, incidents_data = fetch_incidents(instance_id)
    require_clean_run(
        debug_data, DebugEvidence(variables_data, variables_text, incidents, incidents_data)
    )

    if not cands:
        fail(f"no {project}-<n> issue key in the Create-Issue node outputs {list(create_ids)}")
    print(f"OK: candidate keys from debug: {cands}")

    jira_is = _import_jira_is()
    conn = jira_is.connection_id()
    for key in cands:
        fields = jira_is.get_issue(conn, key)
        if fields and fields.get("summary") == seed["summary"]:
            print(f"OK: Jira issue {key} exists with the seed summary")
            print("PASS: all JiraCreateIssue checks passed")
            return
    fail(
        f"none of {cands} carries the seed summary {seed['summary']!r} — the "
        "bpmn process did not create the expected issue in Jira"
    )


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
