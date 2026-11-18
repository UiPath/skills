#!/usr/bin/env python3
"""EscalationJiraTicket: run the agent's process once with the seeded Sev1
case, from the grader's own sandbox, and assert what the run did.

Asserted on the run:
- it completed with no incidents;
- a Jira step completed and its own response carries the created issue's key;
- re-reading that key from Jira (CE project, Task) returns an issue whose
  summary carries this run's correlationId: the ticket really exists and is
  this run's (a real external effect);
- the outputs the request names read back by name: severity=Sev1,
  caseKey=<correlationId>, jiraIssueKey=<that key>.

Static, layout-free guard: the process names all three severities, so it
encodes the rule rather than returning the one answer the seeded case expects.

The Jira step is found by its connector key, whatever its operation (curated
Create Issue, the generic `issue` object the Studio Web builder emits, run
adhoc-2026-11-14_08-01-54), element type or id; no script task or variable
name is required. Every created key is journalled to `.created_keys` before
any assertion; post_run's teardown_jira.py deletes them.
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_setup"))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import jira_is  # noqa: E402
from _shared import bpmn_check  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    UIPATH_NS,
    CheckFailure,
    DebugEvidence,
    connector_response_values,
    element_output_records,
    fetch_incidents,
    fetch_variables,
    get_ci,
    import_exact,
    index_runtime_connectors,
    normalized_identifier,
    q,
    require_clean_run,
    root_scope,
    run_debug,
)

NAME = "EscalationJiraTicket"
SEVERITIES = ("Sev1", "Sev2", "Sev3")
LIVE_RUN_DIR = Path("escalation-jira-live")
JOURNAL = Path(".created_keys")


def locate_bpmn() -> Path:
    try:
        return bpmn_check.resolve_bpmn_file(f"{NAME}.bpmn", exclude_under=[LIVE_RUN_DIR])
    except SystemExit:
        return Path(bpmn_check.find_bpmn_file(None))


def declarations(process: ET.Element) -> list[ET.Element]:
    variables = process.find(f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'variables')}")
    return [] if variables is None else list(variables)


def named_values(process: ET.Element, variables_data, name: str) -> list:
    """Every non-null runtime value of the output called `name`: its declared
    ids in Globals (the runtime may re-case them), any Globals key whose
    GlobalDefinitions Name is `name`, and the `name` output of the element the
    declaration belongs to (the end event)."""
    wanted = normalized_identifier(name)
    decls = [d for d in declarations(process) if normalized_identifier(d.attrib.get("name", "")) == wanted]
    scope = root_scope(variables_data)
    globals_ = get_ci(scope, "Globals", {}) or {}
    definitions = get_ci(scope, "GlobalDefinitions", {}) or {}
    ids = {normalized_identifier(d.attrib.get("id", "")) for d in decls} | {wanted}
    keys = {k for k in globals_ if normalized_identifier(k) in ids}
    keys |= {k for k, d in definitions.items() if normalized_identifier(get_ci(d, "Name", "")) == wanted}
    values = [globals_[k] for k in sorted(keys) if globals_.get(k) is not None]
    owners = tuple(d.attrib["elementId"] for d in decls if d.attrib.get("elementId"))
    for record in element_output_records(variables_data, owners) if owners else []:
        value = get_ci(record, name)
        if value is not None:
            values.append(value)
    return values


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


def assert_rule_encoded(bpmn_text: str) -> None:
    missing = [s for s in SEVERITIES if s not in bpmn_text]
    if missing:
        raise CheckFailure(
            f"the process never names {missing}: it returns the seeded case's answer "
            "instead of classifying by the stated rule"
        )


def completed_ids(debug_data) -> set[str]:
    return {
        get_ci(item, "ElementId")
        for item in get_ci(debug_data, "ElementExecutions", []) or []
        if isinstance(item, dict) and str(get_ci(item, "Status") or "").casefold() == "completed"
    }


def created_keys(variables_data, element_ids) -> list[str]:
    outputs = element_output_records(variables_data, tuple(sorted(element_ids)))
    keys = [v for v in connector_response_values(outputs, "key") if isinstance(v, str) and v.strip()]
    return list(dict.fromkeys(keys))


def journal(keys) -> None:
    known = JOURNAL.read_text().split() if JOURNAL.is_file() else []
    merged = list(dict.fromkeys([*known, *keys]))
    if merged:
        JOURNAL.write_text("\n".join(merged) + "\n")


def owned_keys(keys, correlation: str) -> list[str]:
    """The keys whose Jira issue's summary carries this run's correlationId."""
    conn = jira_is.connection_id()
    owned = []
    for key in keys:
        fields = jira_is.get_issue(conn, key)
        if fields is not None and correlation in str(fields.get("summary", "")):
            owned.append(key)
    return owned


def assert_outputs(process, seed: dict, variables_data, issue_key: str) -> None:
    assert_named(process, variables_data, "jiraIssueKey", issue_key, case_sensitive=True)
    expected = seed["expected"]
    assert_named(process, variables_data, "severity", expected["severity"])
    assert_named(process, variables_data, "caseKey", expected["caseKey"], case_sensitive=True)


def main() -> None:
    seed = json.loads(Path("seed.json").read_text(encoding="utf-8"))
    correlation = seed["correlationId"]

    bpmn_path = locate_bpmn()
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
        # The issue may exist even though the CLI stopped waiting: journal any
        # key in the partial log that is provably this run's, then fail.
        partial = log_file.read_text(encoding="utf-8") if log_file.is_file() else ""
        found = list(dict.fromkeys(re.findall(rf"\b{re.escape(seed['project_key'])}-\d+\b", partial)))
        try:
            journal(owned_keys(found, correlation) if found else [])
        except (SystemExit, Exception):  # noqa: BLE001 -- best effort; keep the real failure
            pass
        raise
    print(f"OK: debug finished (instance {instance_id})")

    variables_data, variables_text = fetch_variables(instance_id)
    ran = completed_ids(debug_data) & step_ids
    keys = created_keys(variables_data, step_ids)
    journal(keys)  # before any assertion: the issue exists whatever the verdict

    incidents, incidents_raw = fetch_incidents(instance_id)
    require_clean_run(debug_data, DebugEvidence(variables_data, variables_text, incidents, incidents_raw))

    if not ran:
        raise CheckFailure(f"no Jira step {sorted(step_ids)} completed in the run")
    keys = created_keys(variables_data, ran)
    if not keys:
        raise CheckFailure(f"the Jira step(s) {sorted(ran)} returned no issue key; no ticket was created")

    owned = owned_keys(keys, correlation)
    if not owned:
        raise CheckFailure(f"none of {keys} is a Jira issue whose summary carries {correlation!r}")
    print(f"OK: Jira issue {owned[0]} exists and its summary carries {correlation!r}")

    assert_outputs(process, seed, variables_data, owned[0])
    print("PASS: the run created this case's Jira ticket and returned the expected outputs")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
