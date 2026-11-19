#!/usr/bin/env python3
"""EscalationJiraTicket: run the agent's process once with the seeded Sev1
case, from the grader's own sandbox, and assert what the run did.

Asserted on the run:
- it completed with no incidents;
- a Jira step completed and its own response carries the created issue's key;
- re-reading that key from Jira returns a Task in project CE whose summary
  carries this run's correlationId: the ticket really exists and is this
  run's (a real external effect). The "[Sev1] ..." summary format is only the
  request's example, so it is not required;
- the outputs the request names read back by name: severity=Sev1,
  caseKey=<correlationId>, jiraIssueKey=<that key>.

Static, layout-free guard: the process names all three severities, so it
encodes the rule rather than returning the one answer the seeded case expects.

The Jira step is found by its connector key, whatever its operation (curated
Create Issue, the generic `issue` object the Studio Web builder emits),
element type or id; no script task or variable name is required. Every
created key is journalled to `.created_keys` before any assertion;
post_run's teardown_jira.py deletes them.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_setup"))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "_setup"))

import escalation_is  # noqa: E402
import jira_is  # noqa: E402
from _shared import bpmn_check  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    CheckFailure,
    DebugEvidence,
    assert_rule_encoded,
    completed_ids,
    connector_response_values,
    element_output_records,
    fetch_incidents,
    fetch_variables,
    get_ci,
    import_exact,
    index_runtime_connectors,
    named_values,
    q,
    require_clean_run,
    run_debug,
)

NAME = "EscalationJiraTicket"
LIVE_RUN_DIR = Path("escalation-jira-live")
JOURNAL = Path(".created_keys")
UNJOURNALED_NOTE = "NOTE: not journaled, delete by hand if this run created them: "


def assert_named(process, variables_data, name: str, expected, *, case_sensitive: bool = False) -> None:
    values = named_values(process, variables_data, name)
    if case_sensitive:
        ok = any(isinstance(v, str) and v.strip() == expected for v in values)
    else:
        ok = any(isinstance(v, str) and v.strip().casefold() == str(expected).casefold() for v in values)
    if not ok:
        raise CheckFailure(f"output {name!r}: expected {expected!r}, got {values!r}")


def jira_ids(process: ET.Element) -> set[str]:
    ids = {
        element_id
        for (key, _path, _obj), element_ids in index_runtime_connectors(process).items()
        if key == jira_is.CONNECTOR
        for element_id in element_ids
    }
    if not ids:
        raise CheckFailure(f"the process has no {jira_is.CONNECTOR} step")
    return ids


def created_keys(variables_data, element_ids) -> list[str]:
    outputs = element_output_records(variables_data, tuple(sorted(element_ids)))
    keys = [v for v in connector_response_values(outputs, "key") if isinstance(v, str) and v.strip()]
    return list(dict.fromkeys(keys))


def journal(keys) -> None:
    known = JOURNAL.read_text().split() if JOURNAL.is_file() else []
    merged = list(dict.fromkeys([*known, *keys]))
    if merged:
        JOURNAL.write_text("\n".join(merged) + "\n")


def note_unjournaled(keys, journaled) -> None:
    missing = [key for key in dict.fromkeys(keys) if key not in journaled]
    if missing:
        print(UNJOURNALED_NOTE + ", ".join(missing))


def partial_text(log_file: Path) -> str:
    return log_file.read_text(encoding="utf-8") if log_file.is_file() else ""


def journal_owned_in(text: str, seed: dict) -> None:
    """The issue may exist although the CLI stopped waiting or a read failed:
    journal any key in `text` that is provably this run's, best effort."""
    found = list(dict.fromkeys(re.findall(rf"\b{re.escape(seed['project_key'])}-\d+\b", text)))
    if not found:
        return
    owned = {}
    try:
        owned = owned_keys(found, seed["correlationId"])
        journal(owned)
    except (SystemExit, Exception):  # noqa: BLE001 -- keep the real failure
        pass
    note_unjournaled(found, owned)


def owned_keys(keys, correlation: str) -> dict[str, dict]:
    """key -> fields for the keys whose Jira issue's summary carries this run's
    correlationId."""
    conn = jira_is.connection_id()
    owned = {}
    for key in keys:
        fields = jira_is.get_issue(conn, key)
        if fields is not None and correlation in str(fields.get("summary", "")):
            owned[key] = fields
    return owned


def assert_task_in_project(key: str, fields: dict, seed: dict) -> None:
    """The request: "Open the ticket as a Task in our Jira project CE"."""
    project = get_ci(fields.get("project"), "key")
    if project != seed["project_key"]:
        raise CheckFailure(f"Jira issue {key} is in project {project!r}, expected {seed['project_key']!r}")
    issuetype = fields.get("issuetype")
    type_id, type_name = get_ci(issuetype, "id"), get_ci(issuetype, "name")
    if str(type_id) != seed["issuetype_id"] and str(type_name).casefold() != jira_is.ISSUETYPE_NAME.casefold():
        raise CheckFailure(
            f"Jira issue {key} is a {type_name!r} (id {type_id!r}), expected a {jira_is.ISSUETYPE_NAME!r}"
        )


def assert_outputs(process, seed: dict, variables_data, issue_key: str) -> None:
    assert_named(process, variables_data, "jiraIssueKey", issue_key, case_sensitive=True)
    expected = seed["expected"]
    assert_named(process, variables_data, "severity", expected["severity"])
    assert_named(process, variables_data, "caseKey", expected["caseKey"], case_sensitive=True)


def main() -> None:
    escalation_is.assert_live_target()
    seed = json.loads(Path("seed.json").read_text(encoding="utf-8"))
    correlation = seed["correlationId"]

    bpmn_path = bpmn_check.locate_bpmn(f"{NAME}.bpmn", [LIVE_RUN_DIR])
    bpmn_text = bpmn_path.read_text(encoding="utf-8")
    process = ET.fromstring(bpmn_text.encode("utf-8")).find(q(BPMN_NS, "process"))
    if process is None:
        raise CheckFailure(f"{bpmn_path} has no bpmn:process")
    step_ids = jira_ids(process)
    assert_rule_encoded(bpmn_text)

    imported = import_exact(bpmn_path, bpmn_path.parent, LIVE_RUN_DIR / f"{NAME}LiveEval")
    # Creates a real issue, so no whole-run retry (a retry could leave a
    # duplicate this grader never sees).
    log_file = LIVE_RUN_DIR / "debug.log"
    try:
        debug_data, instance_id = run_debug(imported, seed["inputs"], log_file, timeout=480)
    except CheckFailure:
        journal_owned_in(partial_text(log_file), seed)
        raise
    print(f"OK: debug finished (instance {instance_id})")

    try:
        variables_data, variables_text = fetch_variables(instance_id)
    except (CheckFailure, subprocess.TimeoutExpired):
        journal_owned_in(partial_text(log_file) + json.dumps(debug_data, default=str), seed)
        raise
    ran = set(completed_ids(debug_data)) & step_ids
    try:
        owned = owned_keys(created_keys(variables_data, step_ids), correlation)
    except (SystemExit, Exception):  # noqa: BLE001 -- keep the real failure
        journal_owned_in(partial_text(log_file) + json.dumps(variables_data, default=str), seed)
        raise
    journal(owned)  # before any assertion: the issue exists whatever the verdict
    note_unjournaled(created_keys(variables_data, step_ids), owned)

    incidents, incidents_raw = fetch_incidents(instance_id)
    require_clean_run(debug_data, DebugEvidence(variables_data, variables_text, incidents, incidents_raw))

    if not ran:
        raise CheckFailure(f"no Jira step {sorted(step_ids)} completed in the run")
    keys = created_keys(variables_data, ran)
    if not keys:
        raise CheckFailure(f"the Jira step(s) {sorted(ran)} returned no issue key; no ticket was created")

    ran_owned = {key: fields for key, fields in owned.items() if key in keys}
    if not ran_owned:
        raise CheckFailure(f"none of {keys} is a Jira issue whose summary carries {correlation!r}")
    if len(ran_owned) != 1:
        raise CheckFailure(f"expected exactly one Jira issue owned by this run, found {sorted(ran_owned)}")
    key, fields = next(iter(ran_owned.items()))
    print(f"OK: Jira issue {key} exists and its summary carries {correlation!r}")
    assert_task_in_project(key, fields, seed)
    print(f"OK: Jira issue {key} is a {jira_is.ISSUETYPE_NAME} in {seed['project_key']}")

    assert_outputs(process, seed, variables_data, key)
    print("PASS: the run created this case's Jira ticket and returned the expected outputs")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
