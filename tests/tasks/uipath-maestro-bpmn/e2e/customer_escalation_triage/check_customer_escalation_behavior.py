#!/usr/bin/env python3
"""Verify the escalation BPMN actually creates a Jira issue and Slack alert.

Outcome-based, tenant-confirmed (mirrors the flow suite's
escalation_jira_ticket, adapted to the BPMN CLI surface):
  1. The submitted BPMN declares the three public outputs and one Jira
     Create-Issue plus one Slack Send connector activity.
  2. LIVE: the exact submitted project (sha256-pinned through solution
     import) runs the seeded Sev1 case via `uip maestro bpmn debug` inside an
     ephemeral solution under the sandbox CWD — kept there so the repo's
     standard `_shared/cleanup_solutions.py` post_run sweep can find the
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
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # local escalation_is (which also wires up _shared)
import escalation_is  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    CheckFailure,
    connector_response_values,
    element_output_records,
    exact_type,
    get_ci,
    incident_records,
    index_runtime_connectors,
    parse_json_output,
    payload_data,
    q,
    resolve_runtime_key,
    root_scope,
    run_cli,
    sha256,
    tail_log,
    UIPATH_NS,
)

# The prompt states this exact layout, so the pinned path is a stated
# requirement — not the unstated-solution-name trap the flow suite's
# discovery helper exists for.
PROJECT = Path("CustomerEscalationTriageSolution") / "CustomerEscalationTriage"
BPMN_FILE = PROJECT / "CustomerEscalationTriage.bpmn"
# Ephemeral solution home, under the sandbox CWD (see module docstring).
LIVE_RUN_DIR = Path(".customer-escalation-live")
DEBUG_TIMEOUT_SECONDS = 480
OUTPUT_TYPES = {
    "severity": "string",
    "caseKey": "string",
    "jiraIssueKey": "string",
}
# Connector activities are matched by (connectorKey, path substring): the
# registry may emit versioned or templated paths, and the runtime correlates
# on the element id either way.
JIRA_CREATE = (escalation_is.JIRA_CONNECTOR, "curated_create_issue")
SLACK_SEND = (escalation_is.SLACK_CONNECTOR, "send_message_to_channel")
COMPLETED_STATUSES = {"Completed", "Successful"}


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


def resolve_contract(path: Path = BPMN_FILE) -> Contract:
    root = ET.parse(path).getroot()
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

    def ids_for(connector_key: str, path_needle: str) -> tuple[str, ...]:
        found = tuple(
            element_id
            for (key, route), element_ids in connectors.items()
            if key == connector_key and path_needle in route
            for element_id in element_ids
        )
        if not found:
            raise CheckFailure(
                f"no {connector_key} activity with a registry path "
                f"containing {path_needle!r}"
            )
        return found

    return Contract(
        output_ids=output_ids,
        jira_create_ids=ids_for(*JIRA_CREATE),
        slack_send_ids=ids_for(*SLACK_SEND),
    )


def harvest_side_effects(
    contract: Contract, variables_data: object
) -> dict[str, list]:
    """Collect created connector ids from the runtime variables read.

    Called (and journalled) BEFORE any assertion: the debug already created
    real records, and this read is the only place their ids appear.
    """

    jira_outputs = element_output_records(
        variables_data, contract.jira_create_ids
    )
    jira_keys = [
        value
        for value in connector_response_values(jira_outputs, "key")
        if isinstance(value, str)
    ]
    jira_ids = [
        value
        for value in connector_response_values(jira_outputs, "id")
        if isinstance(value, str)
    ]
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
        "slack_messages": slack_messages,
    }


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
        raise CheckFailure(f"final status was {final_status!r}")
    incidents = incident_records(incidents_data)
    if incidents is None:
        raise CheckFailure(
            f"incidents response has an unknown shape: {incidents_data!r}"
        )
    if incidents:
        raise CheckFailure(f"unexpected incidents: {incidents}")

    # Execution evidence: each connector activity ran exactly once. Counts sum
    # across every element id bound to the same operation.
    executions = get_ci(debug_data, "ElementExecutions", [])
    executed_ids = [
        get_ci(item, "ElementId") for item in executions if isinstance(item, dict)
    ]
    for label, element_ids in (
        ("Jira create", contract.jira_create_ids),
        ("Slack send", contract.slack_send_ids),
    ):
        count = sum(executed_ids.count(element_id) for element_id in element_ids)
        if count != 1:
            raise CheckFailure(
                f"{label} {list(element_ids)} expected 1 execution, got {count}"
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


def run_debug(project_dir: Path, inputs: dict, log_file: Path) -> tuple:
    """Run one `uip maestro bpmn debug`; return (debug_data, instance_id)."""

    completed = run_cli(
        [
            "uip",
            "maestro",
            "bpmn",
            "debug",
            str(project_dir),
            "--poll-interval",
            "500",
            "--inputs",
            json.dumps(inputs, separators=(",", ":")),
        ],
        timeout=DEBUG_TIMEOUT_SECONDS,
        log_file=log_file,
    )
    payload = parse_json_output(completed.stdout or completed.stderr, "debug")
    debug_data = get_ci(payload, "Data", {})
    instance_id = get_ci(debug_data, "InstanceId")
    if not isinstance(instance_id, str) or not instance_id:
        raise CheckFailure(
            f"debug returned no instance id (exit {completed.returncode}); "
            f"log: {tail_log(log_file)}"
        )
    return debug_data, instance_id


def main() -> None:
    seed = json.loads(Path("seed.json").read_text(encoding="utf-8"))
    if not BPMN_FILE.is_file():
        raise CheckFailure(f"missing {BPMN_FILE}")
    contract = resolve_contract()
    original_hash = sha256(BPMN_FILE)
    escalation_is.assert_live_target()
    connections = escalation_is.connection_ids()

    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    solution_dir = LIVE_RUN_DIR / "CustomerEscalationLiveEval"
    initialized = run_cli(["uip", "solution", "init", str(solution_dir)], timeout=120)
    payload_data(initialized, "initialize ephemeral solution")
    imported = run_cli(
        [
            "uip",
            "solution",
            "projects",
            "import",
            str(PROJECT.resolve()),
            "--solutionFile",
            str(next(solution_dir.glob("*.uipx"))),
        ],
        timeout=180,
    )
    payload_data(imported, "import exact BPMN project")
    imported_project = solution_dir / PROJECT.name
    if sha256(imported_project / BPMN_FILE.name) != original_hash:
        raise CheckFailure("solution import changed the submitted BPMN bytes")
    print(f"OK: imported exact artifact (sha256={original_hash})")

    debug_data, instance_id = run_debug(
        imported_project, seed["inputs"], LIVE_RUN_DIR / "debug.log"
    )
    print(f"OK: debug completed (instance {instance_id})")

    # Runtime evidence. Journal every created id BEFORE asserting anything —
    # the records exist regardless of the verdict, and post_run replays the
    # journal even if this process is killed mid-assertion.
    variables = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "variables-all", instance_id],
        timeout=180,
    )
    _payload, variables_data = payload_data(variables, "variables-all")
    effects = harvest_side_effects(contract, variables_data)
    for issue in effects["jira_issues"]:
        escalation_is.record_created_id("jira_issue", issue)
    for message in effects["slack_messages"]:
        escalation_is.record_created_id("slack_message", message)

    incidents = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "incidents", instance_id],
        timeout=180,
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
    for issue in effects["jira_issues"]:
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
