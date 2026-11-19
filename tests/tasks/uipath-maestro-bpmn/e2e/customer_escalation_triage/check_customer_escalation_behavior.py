#!/usr/bin/env python3
"""Verify the escalation BPMN actually creates a Jira issue and Slack alert.

Outcome-based, tenant-confirmed (mirrors the flow suite's
escalation_jira_ticket, adapted to the BPMN CLI surface):
  1. The submitted BPMN (found wherever the agent put it; Studio Web names it
     Process.bpmn) declares the three public outputs, has a Jira step and a
     Slack step (found by connector key alone, whatever the operation, element
     type or id), and names all three severities, so it encodes the rule
     rather than returning the one answer the seeded case expects.
  2. LIVE: the exact submitted project (sha256-pinned through solution
     import) runs the seeded Sev1 case via `uip maestro bpmn debug` inside an
     ephemeral solution under the sandbox CWD — kept there so the repo's
     standard `_setup/cleanup_solutions.py` post_run sweep can find the
     .uipx. Unlike `flow debug`, `bpmn debug` returns an instance id; runtime
     evidence comes from `debug-instance variables-all` (variables addressed
     by id, not name) and `debug-instance incidents`.
  3. TENANT: re-reading the created Jira key returns an issue whose summary
     carries the seeded correlationId and whose project/issuetype match the
     seed — proof the process created THIS run's ticket, not a fabricated
     key. The Slack send is proven from the executed element's own runtime
     response: the expected channel, and a message text carrying the
     correlationId and severity.

Every created id is appended to the flat journal (`escalation_is.JOURNAL`)
the moment it is visible, then a best-effort in-band delete runs; post_run
replays the journal, which is the only sweep that survives coder_eval
SIGKILLing this process on the criterion timeout.
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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_setup"))  # escalation_is (which also wires up _shared)
import escalation_is  # noqa: E402
from _shared import bpmn_check, bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    CheckFailure,
    assert_rule_encoded,
    connector_response_values,
    element_output_records,
    exact_type,
    get_ci,
    import_exact,
    incident_records,
    index_runtime_connectors,
    payload_data,
    q,
    resolve_runtime_key,
    root_scope,
    run_cli,
    run_debug,
    UIPATH_NS,
)

NAME = "CustomerEscalationTriage"
# Ephemeral solution home, under the sandbox CWD (see module docstring).
LIVE_RUN_DIR = Path("customer-escalation-live")
DEBUG_TIMEOUT_SECONDS = bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT
SOLUTION_INIT_TIMEOUT = bpmn_live.SOLUTION_INIT_TIMEOUT
SOLUTION_IMPORT_TIMEOUT = bpmn_live.SOLUTION_IMPORT_TIMEOUT
VARIABLES_ALL_TIMEOUT = bpmn_live.VARIABLES_ALL_TIMEOUT
INCIDENTS_TIMEOUT = bpmn_live.INCIDENTS_TIMEOUT

# Every live CLI call on the worst-case path, this module's plus escalation_is'.
# The behavior criterion's `timeout:` must cover the sum; test_behavior_checker
# asserts it against the YAML so the two cannot drift apart silently.
STEP_TIMEOUTS = (
    DEBUG_TIMEOUT_SECONDS,
    SOLUTION_INIT_TIMEOUT,
    SOLUTION_IMPORT_TIMEOUT,
    VARIABLES_ALL_TIMEOUT,
    INCIDENTS_TIMEOUT,
) + escalation_is.STEP_TIMEOUTS
# owned_jira_targets reads each created key once, on top of the assertion read.
MAX_OWNED_KEY_READS = 2
WORST_CASE_PATH_TIMEOUT = (
    sum(STEP_TIMEOUTS) + MAX_OWNED_KEY_READS * escalation_is.JIRA_READ_TIMEOUT
)
OUTPUT_TYPES = {
    "severity": "string",
    "caseKey": "string",
    "jiraIssueKey": "string",
}
# Connector steps are matched by connectorKey alone. Several Jira objects
# create the same ticket (verified live: same body, same {self, key, id}), and
# the Studio Web builder emits the generic `issue` object (run
# adhoc-2026-11-14_08-01-54); the runtime evidence and the tenant reread prove
# the ticket, whichever operation made it.
SLACK_SEND_AS = "user"
COMPLETED_STATUSES = bpmn_live.COMPLETED_STATUSES


@dataclass(frozen=True)
class Contract:
    """Element and variable ids needed to read runtime outcomes.

    Discovery, not grading: BPMN runtime variables are addressed by id, so
    the ids of the public outputs and the two connector activities must be
    resolved from the source before the live evidence can be read.
    """

    output_ids: dict[str, str]
    jira_create_ids: tuple[str, ...]
    slack_send_ids: tuple[str, ...]


def resolve_contract(path: Path) -> Contract:
    text = path.read_text(encoding="utf-8")
    assert_rule_encoded(text)
    root = ET.fromstring(text.encode("utf-8"))
    process = root.find(q(BPMN_NS, "process"))
    if process is None:
        raise CheckFailure("BPMN must contain one root process")

    variables = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'variables')}"
    )
    if variables is None:
        raise CheckFailure("root process is missing uipath:variables")
    output_ids: dict[str, str] = {}
    for variable in variables:
        name = variable.attrib.get("name")
        identifier = variable.attrib.get("id")
        if (
            variable.tag.rsplit("}", 1)[-1] != "output"
            or not name
            or not identifier
            or name not in OUTPUT_TYPES
        ):
            continue
        if name in output_ids:
            raise CheckFailure(
                f"public output {name!r} is declared more than once, so its "
                "runtime value cannot be addressed"
            )
        output_ids[name] = identifier
    missing = sorted(set(OUTPUT_TYPES) - set(output_ids))
    if missing:
        raise CheckFailure(f"public outputs not declared: {missing}")

    connectors = index_runtime_connectors(process)

    def ids_for(connector_key: str) -> tuple[str, ...]:
        found = tuple(
            sorted(
                element_id
                for (key, _path, _object_name), element_ids in connectors.items()
                if key == connector_key
                for element_id in element_ids
            )
        )
        if not found:
            raise CheckFailure(f"the process has no {connector_key} step")
        return found

    # Send identity, as the flow suite grades it: a node that posts as the
    # default bot instead of the prompt-required user has an indistinguishable
    # runtime response, so it can only be caught on the authored artifact.
    slack_ids = set(ids_for(escalation_is.SLACK_CONNECTOR))
    for element in process.iter():
        if element.attrib.get("id") not in slack_ids:
            continue
        sends_as = bpmn_check.query_values(element, "send_as")
        if sends_as != [SLACK_SEND_AS]:
            raise CheckFailure(
                f"Slack node {element.attrib.get('id')!r} must carry exactly "
                f"one send_as query parameter with value {SLACK_SEND_AS!r}, found "
                f"{sends_as!r}"
            )

    return Contract(
        output_ids=output_ids,
        jira_create_ids=ids_for(escalation_is.JIRA_CONNECTOR),
        slack_send_ids=ids_for(escalation_is.SLACK_CONNECTOR),
    )


def _step_values(
    variables_data: object, element_id: str, field: str
) -> set[str]:
    return {
        value
        for value in connector_response_values(
            element_output_records(variables_data, element_id), field
        )
        if isinstance(value, str) and value
    }


def steps_returning(
    variables_data: object, element_ids: tuple[str, ...], field: str
) -> tuple[str, ...]:
    """The steps among `element_ids` whose own response carries `field`: the
    Jira step that created the issue (`key`) or the Slack step that posted
    (`ts`), not a search, comment or lookup on the same connector."""

    return tuple(
        element_id
        for element_id in element_ids
        if _step_values(variables_data, element_id, field)
    )


def distinct_returns(
    variables_data: object,
    element_ids: tuple[str, ...],
    field: str,
    executed_ids: list,
) -> int:
    """Distinct `field` values the steps returned, a step run twice counting
    twice: a create plus a get-issue of the same key is one issue."""

    runs: dict[str, int] = {}
    for element_id in steps_returning(variables_data, element_ids, field):
        for value in _step_values(variables_data, element_id, field):
            runs[value] = max(runs.get(value, 0), executed_ids.count(element_id))
    return sum(runs.values())


def _distinct(values: list) -> list:
    unique: list = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def harvest_side_effects(
    contract: Contract, variables_data: object
) -> dict[str, list]:
    """Collect created connector ids from the runtime variables read.

    Called (and journalled) BEFORE any assertion: the debug already created
    real records, and this read is the only place their ids appear.
    """

    jira_outputs = element_output_records(
        variables_data,
        steps_returning(variables_data, contract.jira_create_ids, "key"),
    )
    jira_keys = _distinct([
        value
        for value in connector_response_values(jira_outputs, "key")
        if isinstance(value, str)
    ])
    jira_ids = _distinct([
        value
        for value in connector_response_values(jira_outputs, "id")
        if isinstance(value, str)
    ])
    jira_targets = {}
    for output in jira_outputs:
        response = get_ci(output, "response")
        key = get_ci(response, "key")
        if not isinstance(key, str):
            continue
        identifier = get_ci(response, "id")
        jira_targets.setdefault(key, identifier if isinstance(identifier, str) else key)
    slack_outputs = element_output_records(
        variables_data, contract.slack_send_ids
    )
    slack_messages = []
    for output in slack_outputs:
        response = get_ci(output, "response")
        timestamp = get_ci(response, "ts")
        channel_id = get_ci(response, "channel")
        if isinstance(timestamp, str) and isinstance(channel_id, str):
            slack_messages.append([channel_id, timestamp])
    return {
        "jira_keys": jira_keys,
        # Deletion targets prefer the numeric id; the key still works.
        "jira_issues": jira_ids or jira_keys,
        "jira_targets": jira_targets,
        "slack_messages": _distinct(slack_messages),
    }


def _capped_keys(keys: list[str]) -> list[str]:
    skipped = keys[MAX_OWNED_KEY_READS:]
    if skipped:
        print(f"NOTE: not journaled, over the {MAX_OWNED_KEY_READS}-read cap: {skipped}")
    return keys[:MAX_OWNED_KEY_READS]


def owned_jira_targets(
    effects: dict[str, list], jira_connection_id: str, correlation: str
) -> list[str]:
    """Deletion targets of the issues whose tenant summary carries this run's
    correlationId; a step that merely read an existing ticket is not owned."""

    owned = []
    targets = effects["jira_targets"]
    for key in _capped_keys(list(targets)):
        target = targets[key]
        try:
            fields = escalation_is.get_issue_fields(jira_connection_id, key)
        except (CheckFailure, subprocess.TimeoutExpired):
            continue
        if correlation in str(get_ci(fields, "summary", "")):
            owned.append(target)
    return owned


def assert_outcome(
    contract: Contract,
    seed: dict,
    debug_data: object,
    variables_data: object,
    incidents_data: object,
) -> str:
    """Assert the runtime evidence for the seeded case; return the Jira key."""

    final_status = get_ci(debug_data, "FinalStatus")
    if final_status not in COMPLETED_STATUSES:
        # A bare status is not diagnosable. Surface the incidents and the
        # per-element outcome so a Faulted run says WHICH node failed and
        # why, instead of sending the reader back to the tenant.
        detail = []
        faulted = [
            f"{get_ci(item, 'ElementId')}={get_ci(item, 'Status')}"
            for item in get_ci(debug_data, "ElementExecutions", []) or []
            if isinstance(item, dict)
            and str(get_ci(item, "Status") or "").casefold() != "completed"
        ]
        if faulted:
            detail.append(f"non-completed elements: {faulted}")
        records = incident_records(incidents_data)
        if records:
            detail.append(f"incidents: {json.dumps(records)[:1500]}")
        raise CheckFailure(
            f"final status was {final_status!r}"
            + ("; " + "; ".join(detail) if detail else "")
        )
    incidents = incident_records(incidents_data)
    if incidents is None:
        raise CheckFailure(
            f"incidents response has an unknown shape: {incidents_data!r}"
        )
    if incidents:
        raise CheckFailure(f"unexpected incidents: {incidents}")

    # Execution evidence: one issue created and one message posted. Counts are
    # distinct keys / ts values the connector's steps returned, so a search,
    # comment or lookup on the same connector is not counted.
    executions = get_ci(debug_data, "ElementExecutions", [])
    executed_ids = [
        get_ci(item, "ElementId") for item in executions if isinstance(item, dict)
    ]
    for label, element_ids, field in (
        ("Jira create", contract.jira_create_ids, "key"),
        ("Slack send", contract.slack_send_ids, "ts"),
    ):
        count = distinct_returns(variables_data, element_ids, field, executed_ids)
        if count != 1:
            raise CheckFailure(
                f"{label} {list(element_ids)} expected 1 execution that "
                f"returned a {field!r}, got {count}"
            )

    # Public outputs, addressed by id in the root scope's globals.
    globals_map = get_ci(root_scope(variables_data), "Globals", {})
    if not isinstance(globals_map, dict):
        raise CheckFailure(f"root scope Globals is not a map: {globals_map!r}")
    actual = {
        name: resolve_runtime_key(globals_map, identifier, name)
        for name, identifier in contract.output_ids.items()
    }
    for name, declared_type in OUTPUT_TYPES.items():
        if not exact_type(actual[name], declared_type):
            raise CheckFailure(
                f"output {name} expected exact type {declared_type}, got "
                f"{type(actual[name]).__name__}: {actual[name]!r}"
            )
    for name, expected in seed["expected"].items():
        if actual.get(name) != expected:
            raise CheckFailure(
                f"output {name} expected {expected!r}, got {actual.get(name)!r}"
            )

    # The exposed jiraIssueKey must be the executed Create-Issue node's OWN
    # response key — harvesting some other key cannot satisfy this.
    effects = harvest_side_effects(contract, variables_data)
    if len(effects["jira_keys"]) != 1:
        raise CheckFailure(
            "Jira create returned no unique issue key: "
            f"{effects['jira_keys']!r}"
        )
    jira_key = effects["jira_keys"][0]
    if actual["jiraIssueKey"] != jira_key:
        raise CheckFailure(
            f"jiraIssueKey output {actual['jiraIssueKey']!r} is not the "
            f"created issue's key {jira_key!r}"
        )

    # Slack runtime evidence: exactly one send, to the seeded channel, whose
    # message text carries the correlation and computed severity.
    if len(effects["slack_messages"]) != 1:
        raise CheckFailure(
            "Slack send returned no unique channel/timestamp: "
            f"{effects['slack_messages']!r}"
        )
    channel_id, timestamp = effects["slack_messages"][0]
    if channel_id != seed["inputs"]["slackChannelId"]:
        raise CheckFailure(
            f"Slack message went to {channel_id!r}, expected "
            f"{seed['inputs']['slackChannelId']!r}"
        )
    slack_outputs = element_output_records(
        variables_data, contract.slack_send_ids
    )
    messages = [
        value
        for value in connector_response_values(slack_outputs, "message")
        if isinstance(value, dict)
    ]
    text = get_ci(messages[0], "text") if messages else None
    required_tokens = (seed["correlationId"], seed["expected"]["severity"])
    if not isinstance(text, str) or any(
        token not in text for token in required_tokens
    ):
        raise CheckFailure(
            f"Slack message text does not carry {required_tokens}: {text!r}"
        )
    return jira_key


def assert_jira_issue_on_tenant(
    connection_id: str, issue_key: str, seed: dict
) -> None:
    """Re-read the created issue from Jira and pin the graded fields."""

    fields = escalation_is.get_issue_fields(connection_id, issue_key)
    summary = get_ci(fields, "summary")
    if not isinstance(summary, str) or seed["correlationId"] not in summary:
        raise CheckFailure(
            f"Jira issue {issue_key} summary does not contain "
            f"{seed['correlationId']!r}: {summary!r}"
        )
    remote = {
        "project.key": get_ci(get_ci(fields, "project", {}), "key"),
        "issuetype.id": get_ci(get_ci(fields, "issuetype", {}), "id"),
    }
    expected = {
        "project.key": seed["inputs"]["jiraProjectKey"],
        "issuetype.id": seed["inputs"]["jiraIssueTypeId"],
    }
    if remote != expected:
        raise CheckFailure(
            f"Jira issue {issue_key} has incorrect remote fields: "
            f"expected {expected}, got {remote}"
        )



def journal_partial_log(
    seed: dict, log_file: Path, jira_connection_id: str, debug_data: object = None
) -> None:
    """Journal the Jira keys in an interrupted run's log, and in its debug
    response when the debug finished, whose summary carries this run's
    correlationId."""

    partial = log_file.read_text(encoding="utf-8") if log_file.is_file() else ""
    if debug_data is not None:
        partial += "\n" + json.dumps(debug_data, default=str)
    project_key = seed["inputs"]["jiraProjectKey"]
    found = list(dict.fromkeys(re.findall(rf"\b{re.escape(project_key)}-\d+\b", partial)))
    for key in _capped_keys(found):
        try:
            fields = escalation_is.get_issue_fields(jira_connection_id, key)
        except (CheckFailure, subprocess.TimeoutExpired):
            continue
        if seed["correlationId"] in str(get_ci(fields, "summary", "")):
            escalation_is.record_created_id("jira_issue", key)


def run_and_read(
    seed: dict, imported_project: Path, jira_connection_id: str
) -> tuple[object, str, object]:
    """Debug the seeded case and read its variables; return (debug_data,
    instance_id, variables_data). When either step fails after the run may
    have created records, journal them from the partial log before re-raising."""

    log_file = LIVE_RUN_DIR / "debug.log"
    debug_data = None
    try:
        debug_data, instance_id = run_debug(imported_project, seed["inputs"], log_file)
        print(f"OK: debug completed (instance {instance_id})")

        variables = run_cli(
            ["uip", "maestro", "bpmn", "debug-instance", "variables-all", instance_id],
            timeout=VARIABLES_ALL_TIMEOUT,
        )
        _payload, variables_data = payload_data(variables, "variables-all")
    except (CheckFailure, subprocess.TimeoutExpired):
        try:
            journal_partial_log(seed, log_file, jira_connection_id, debug_data)
        except (CheckFailure, subprocess.TimeoutExpired, OSError):
            pass
        raise
    return debug_data, instance_id, variables_data


def main() -> None:
    seed = json.loads(Path("seed.json").read_text(encoding="utf-8"))
    bpmn_file = bpmn_check.locate_bpmn(f"{NAME}.bpmn", [LIVE_RUN_DIR])
    project = bpmn_file.parent
    contract = resolve_contract(bpmn_file)
    escalation_is.assert_live_target()
    connections = escalation_is.connection_ids()

    imported_project = import_exact(
        bpmn_file, project, LIVE_RUN_DIR / "CustomerEscalationLiveEval"
    )

    debug_data, instance_id, variables_data = run_and_read(
        seed, imported_project, connections[escalation_is.JIRA_CONNECTOR]
    )

    # Runtime evidence. Journal every created id BEFORE asserting anything —
    # the records exist regardless of the verdict, and post_run replays the
    # journal even if this process is killed mid-assertion.
    effects = harvest_side_effects(contract, variables_data)
    owned_issues = owned_jira_targets(
        effects, connections[escalation_is.JIRA_CONNECTOR], seed["correlationId"]
    )
    for issue in owned_issues:
        escalation_is.record_created_id("jira_issue", issue)
    for message in effects["slack_messages"]:
        escalation_is.record_created_id("slack_message", message)

    incidents = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "incidents", instance_id],
        timeout=INCIDENTS_TIMEOUT,
    )
    _payload, incidents_data = payload_data(incidents, "incidents")

    jira_key = assert_outcome(
        contract, seed, debug_data, variables_data, incidents_data
    )
    assert_jira_issue_on_tenant(
        connections[escalation_is.JIRA_CONNECTOR], jira_key, seed
    )
    print(
        f"OK: Jira issue {jira_key} exists on the tenant and carries "
        f"{seed['correlationId']!r}"
    )

    # Best-effort in-band cleanup; post_run replays the journal for anything
    # this leaves behind (it re-deletes idempotently — deletion is only
    # confirmed on success or an issue-specific not-found).
    for issue in owned_issues:
        if not escalation_is.delete_jira_issue(
            connections[escalation_is.JIRA_CONNECTOR], issue
        ):
            print(f"WARN: could not confirm deletion of Jira {issue}")
    for channel_id, timestamp in effects["slack_messages"]:
        if not escalation_is.delete_slack_message(
            connections[escalation_is.SLACK_CONNECTOR], channel_id, timestamp
        ):
            print(f"WARN: could not confirm deletion of Slack {timestamp}")

    print(
        "PASS: escalation BPMN created a real Jira ticket and Slack alert "
        "with the expected classification"
    )


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
