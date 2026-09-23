#!/usr/bin/env python3
"""EscalationSlackAlert (BPMN): live outcome check, seeded Sev1 case.

Ported from Flow `e2e/escalation_slack_alert/check_escalation_slack_alert.py`:
same scenario (a manual-start escalation-triage process classifies severity
and posts a Slack alert), same seeded Sev1 case, same OUTCOME assertions —
translated from `uip maestro flow debug`'s inline variables to `uip maestro
bpmn debug`'s instance-id + `debug-instance variables-all`/`incidents`
surface (canonical live pattern, see LIVE-ADDENDUM.md; copies the plumbing of
the CI-proven `e2e/customer_escalation_triage/check_customer_escalation_behavior.py`,
trimmed to this task's single Slack connector — no Jira, no tenant re-read, no
teardown, because Flow's own checker never re-reads the tenant or deletes the
posted message and this task's Flow `post_run` never sweeps Slack either).

Assertion map (Flow → BPMN):
  F check_escalation_slack_alert.py:44        assert_flow_uses_connector_target(SLACK_KEY)
      -> resolve_contract(): ids_for(*SLACK_SEND) via index_runtime_connectors
  F check_escalation_slack_alert.py:45        assert_connector_send_identity(key, "user", ...)
      -> resolve_contract(): send_as input == "user" on every slack_send_id
  F check_escalation_slack_alert.py:58        run_debug(inputs=case["inputs"], retries=1)
      -> ephemeral `solution init` + `solution projects import` (sha256-pinned) + bpmn_live.run_debug(project_dir,
         inputs, log)
  F flow_check.py:551-552 (run_debug's own exact-match status gate)
      -> assert_outcome(): FinalStatus == "Completed"
  F check_escalation_slack_alert.py:63-64     assert_named_equals(payload, name, expected)
      -> assert_outcome(): assert_named_equals(actual, name, expected) per output (severity, engineeringNeeded, caseKey)
  F flow_check.py:1445-1464                   completed_node_ids_of_type(payload, "script")
      -> resolve_contract(): classifier_ids = every bpmn:scriptTask id
  F check_escalation_slack_alert.py:66-88     sev_scripts / next_steps binding (same node, both fields)
      -> bind_classifier(): severity AND nextSteps must come from the SAME scriptTask's own output
  F flow_check.py:1328-1334                   slackMessageId ts-shape gate
      -> assert_outcome(): SLACK_TS_RE match on the exposed output
  F flow_check.py:1339-1355                   >=1 Completed connector node in the debug trace
      -> assert_outcome(): >=1 "completed" element among contract.slack_send_ids
  F flow_check.py:1357-1384                   mapped id must equal an executed send's OWN response ts
      -> assert_outcome(): match slackMessageId against a slack_send_ids element's response["ts"]
  F flow_check.py:1386-1394                   posted channel must equal expected_channel
      -> assert_outcome(): matched response["channel"] == SLACK_CHANNEL
  F flow_check.py:1395-1405                   must_contain: correlationId, severity, nextSteps
      -> assert_outcome(): matched response["message"]["text"] contains all three
  I    locate/parse .bpmn; resolve the project dir; import into an ephemeral solution (sha256-pinned);
       read runtime evidence via `debug-instance variables-all`/`incidents` — `bpmn debug` returns an
       instance id rather than inline variables, so this whole sequence stands in for Flow's single
       `flow debug` call (LIVE-ADDENDUM.md "canonical live pattern")
  T    public outputs addressed by declared `<uipath:variables>` id (`vars.<VarId>`) and a node's own
       `Outputs.response` in place of Flow's globals["<nodeId>.output"] map
  DROPPED  exact-type checks on public outputs (customer_escalation_triage's own addition; Flow's
           assert_named_equals never asserts a Python type, only non-empty + normalized equality)
  DROPPED  "Successful" as an alternate FinalStatus / tenant re-read / connection lookup / journal
           teardown (Flow's checker only ever accepts exact "Completed" and never re-reads the tenant
           or deletes the posted message; this task's Flow post_run has no Slack teardown either)
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared import bpmn_check  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    CheckFailure,
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

SLACK_CONNECTOR = "uipath-salesforce-slack"
# Route substring, not the curated activity's exact spelling: registry
# templates may emit a versioned path (`/send_message_to_channel_v2`), and
# `index_runtime_connectors` correlates on a substring match the same way the
# CI-proven customer_escalation_triage checker does.
SLACK_SEND = (SLACK_CONNECTOR, "send_message_to_channel")
SLACK_SEND_AS = "user"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
OUTPUT_NAMES = ("severity", "engineeringNeeded", "caseKey", "slackMessageId")
CASE_SENSITIVE_OUTPUTS = {"caseKey"}  # opaque id -- exact-case match, like Flow's CASE_SENSITIVE
SLACK_TS_RE = re.compile(r"^\d{9,11}\.\d{4,6}$")

LIVE_RUN_DIR = Path("escalation-slack-alert-live")
# Per-call budgets for the live CLI steps this checker makes. test_criterion_budgets.py
# statically prices every run_debug(...) call; the YAML criterion's `timeout:` must
# cover their sum plus bpmn_live.CRITERION_MARGIN_SECONDS.
DEBUG_TIMEOUT_SECONDS = 480  # bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT, spelled out so the
# static budget guard can price this call without following the import.
SOLUTION_INIT_TIMEOUT = 90
SOLUTION_IMPORT_TIMEOUT = 180
VARIABLES_ALL_TIMEOUT = 120
INCIDENTS_TIMEOUT = 120
STEP_TIMEOUTS = (
    DEBUG_TIMEOUT_SECONDS,
    SOLUTION_INIT_TIMEOUT,
    SOLUTION_IMPORT_TIMEOUT,
    VARIABLES_ALL_TIMEOUT,
    INCIDENTS_TIMEOUT,
)


@dataclass(frozen=True)
class Contract:
    """Element and variable ids needed to read runtime outcomes.

    Discovery, not grading: BPMN runtime variables are addressed by id, so the
    ids of the public outputs, the classifier script(s), and the Slack send
    node(s) must be resolved from the source before the live evidence can be
    read. Mirrors customer_escalation_triage's Contract, trimmed to one
    connector.
    """

    output_ids: dict[str, str]
    slack_send_ids: tuple[str, ...]
    classifier_ids: tuple[str, ...]


def resolve_contract(root: ET.Element) -> Contract:
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
            or name not in OUTPUT_NAMES
        ):
            continue
        if name in output_ids:
            raise CheckFailure(
                f"public output {name!r} is declared more than once, so its "
                "runtime value cannot be addressed"
            )
        output_ids[name] = identifier
    missing = sorted(set(OUTPUT_NAMES) - set(output_ids))
    if missing:
        raise CheckFailure(f"public outputs not declared: {missing}")

    # Every scriptTask that could be the classifier -- bind_classifier() below
    # requires severity AND nextSteps to come from the SAME executed one.
    classifier_ids = tuple(
        element.attrib["id"]
        for element in process.iter(q(BPMN_NS, "scriptTask"))
        if element.attrib.get("id")
    )
    if not classifier_ids:
        raise CheckFailure(
            "no bpmn:scriptTask to classify severity; the value would be a "
            "literal rather than computed"
        )

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

    # Send identity, as Flow grades it: a node that posts as the default bot
    # instead of the prompt-required user has an indistinguishable runtime
    # response, so it can only be caught on the authored artifact.
    slack_ids = set(ids_for(*SLACK_SEND))
    for element in process.iter():
        if element.attrib.get("id") not in slack_ids:
            continue
        sends_as = [
            item.attrib.get("value")
            for item in element.iter(q(UIPATH_NS, "input"))
            if item.attrib.get("name") == "send_as"
        ]
        if sends_as != [SLACK_SEND_AS]:
            raise CheckFailure(
                f"Slack node {element.attrib.get('id')!r} must carry exactly "
                f"one send_as input with value {SLACK_SEND_AS!r}, found "
                f"{sends_as!r}"
            )

    return Contract(
        output_ids=output_ids,
        slack_send_ids=tuple(sorted(slack_ids)),
        classifier_ids=classifier_ids,
    )


def normalized(value, *, case_fold: bool = True):
    """Port of flow_check.normalized: trim strings, coerce "true"/"false" to
    booleans, and (by default) fold case for enum-like values."""
    if isinstance(value, str):
        text = value.strip()
        lowered = text.casefold()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        return lowered if case_fold else text
    return value


def assert_named_equals(
    actual_map: dict, name: str, expected, *, case_sensitive: bool = False
) -> None:
    """Port of flow_check.assert_named_equals: the named output must be
    present, non-empty, and equal `expected` (case-insensitively unless
    `case_sensitive`)."""
    if name not in actual_map:
        raise CheckFailure(f"output {name!r} is missing from the runtime scope")
    actual = actual_map[name]
    if actual is None or (isinstance(actual, str) and not actual.strip()):
        raise CheckFailure(f"output {name!r} is empty")
    if normalized(actual, case_fold=not case_sensitive) != normalized(
        expected, case_fold=not case_sensitive
    ):
        raise CheckFailure(f"output {name!r}: expected {expected!r}, got {actual!r}")


def bind_classifier(variables_data, classifier_ids: tuple[str, ...], expected_severity: str) -> str:
    """Bind severity AND nextSteps to the SAME executed scriptTask.

    Port of check_escalation_slack_alert.py's script_nodes/sev_scripts/
    next_steps logic: the prompt requires the alert to include severity,
    correlationId, and next steps, and nextSteps is an intermediate script
    output (not a named End/public output). Binding both to one node's own
    response means an unrelated or cosmetic scriptTask can't supply either
    value.
    """
    records = element_output_records(variables_data, classifier_ids)
    sev_responses = []
    for record in records:
        response = get_ci(record, "response")
        severity_value = get_ci(response, "severity") if isinstance(response, dict) else response
        if severity_value is not None and normalized(severity_value) == normalized(expected_severity):
            sev_responses.append(response)
    if not sev_responses:
        raise CheckFailure(
            f"no executed bpmn:scriptTask among {list(classifier_ids)} produced "
            f"the expected severity {expected_severity!r} in its own output -- "
            "cannot bind the nextSteps check to the classification script"
        )
    for response in sev_responses:
        if isinstance(response, dict):
            candidate = get_ci(response, "nextSteps")
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    raise CheckFailure(
        "the bpmn:scriptTask that produced the expected severity did not also "
        "produce a nextSteps value in its own output -- the prompt requires "
        "classifying a short next-steps string"
    )


def assert_outcome(
    contract: Contract,
    case: dict,
    debug_data,
    variables_data,
    incidents_data,
) -> str:
    """Assert the runtime evidence for the seeded case; return the Slack ts."""

    final_status = get_ci(debug_data, "FinalStatus")
    if final_status != "Completed":
        faulted = [
            f"{get_ci(item, 'ElementId')}={get_ci(item, 'Status')}"
            for item in get_ci(debug_data, "ElementExecutions", []) or []
            if isinstance(item, dict)
            and str(get_ci(item, "Status") or "").casefold() != "completed"
        ]
        detail = [f"non-completed elements: {faulted}"] if faulted else []
        records = incident_records(incidents_data)
        if records:
            detail.append(f"incidents: {json.dumps(records)[:1500]}")
        raise CheckFailure(
            f"final status was {final_status!r}"
            + ("; " + "; ".join(detail) if detail else "")
        )

    # `bpmn debug` reports success via an instance id, not inline variables;
    # a completed run with incidents is still a failure (LIVE-ADDENDUM.md).
    incidents = incident_records(incidents_data)
    if incidents is None:
        raise CheckFailure(f"incidents response has an unknown shape: {incidents_data!r}")
    if incidents:
        raise CheckFailure(f"unexpected incidents: {incidents}")

    executions = get_ci(debug_data, "ElementExecutions", [])
    slack_completed = [
        item
        for item in executions
        if isinstance(item, dict)
        and get_ci(item, "ElementId") in contract.slack_send_ids
        and str(get_ci(item, "Status") or "").casefold() == "completed"
    ]
    if not slack_completed:
        raise CheckFailure(
            f"no Slack send element among {list(contract.slack_send_ids)} "
            "completed in the debug trace; the alert was not actually posted"
        )

    globals_map = get_ci(root_scope(variables_data), "Globals", {})
    if not isinstance(globals_map, dict):
        raise CheckFailure(f"root scope Globals is not a map: {globals_map!r}")
    actual = {
        name: resolve_runtime_key(globals_map, identifier, name)
        for name, identifier in contract.output_ids.items()
    }

    expected = case["expected"]
    assert_named_equals(actual, "severity", expected["severity"])
    assert_named_equals(actual, "engineeringNeeded", expected["engineeringNeeded"])
    assert_named_equals(actual, "caseKey", expected["caseKey"], case_sensitive=True)

    # Severity must be COMPUTED, not exposed as a literal, and nextSteps (not
    # a public output) must come from the same executed classification node.
    next_steps = bind_classifier(variables_data, contract.classifier_ids, expected["severity"])

    # Shape gate: reject a hard-coded placeholder like "ok"/"sent"/"1".
    slack_message_id = actual.get("slackMessageId")
    text_id = str(slack_message_id).strip() if slack_message_id is not None else ""
    if not SLACK_TS_RE.match(text_id):
        raise CheckFailure(
            f"output 'slackMessageId'={text_id!r} is not a Slack message ts "
            r"(expected \d{9,11}\.\d{4,6}); the process did not actually post to Slack"
        )

    # Trace gate: the mapped ts must equal an EXECUTED Slack node's own
    # response ts -- a constant ts mapped past an idle/unrelated node fails.
    slack_outputs = element_output_records(variables_data, contract.slack_send_ids)
    matched_response = None
    for output in slack_outputs:
        response = get_ci(output, "response")
        if not isinstance(response, dict):
            continue
        ts = get_ci(response, "ts")
        if isinstance(ts, str) and ts.strip() == text_id:
            matched_response = response
            break
    if matched_response is None:
        raise CheckFailure(
            f"slackMessageId {text_id!r} does not match any executed Slack "
            "node's response ts; the mapped ts was not produced by the "
            "executed send"
        )

    channel = get_ci(matched_response, "channel")
    if channel != SLACK_CHANNEL:
        raise CheckFailure(
            f"Slack message posted to channel {channel!r}, expected {SLACK_CHANNEL!r}"
        )

    message = get_ci(matched_response, "message")
    text = get_ci(message, "text") if isinstance(message, dict) else None
    required_tokens = (case["inputs"]["correlationId"], expected["severity"], next_steps)
    if not isinstance(text, str) or any(token not in text for token in required_tokens):
        raise CheckFailure(
            "posted Slack message is missing required text -- the message "
            f"must carry every required field (severity, correlationId, next "
            f"steps), not just some: {text!r}"
        )
    return text_id


def main() -> None:
    bpmn_path, root = bpmn_check.parse_bpmn("EscalationSlackAlert")
    project_dir = bpmn_check.resolve_project(os.path.basename(bpmn_path))
    # Artifact-level gates first (connector target + send identity + declared
    # outputs), mirroring Flow's assert_flow_uses_connector_target /
    # assert_connector_send_identity running before the live debug call.
    contract = resolve_contract(root)

    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise CheckFailure("seed.json is missing; pre_run did not complete")
    cases = json.loads(seed_path.read_text(encoding="utf-8")).get("cases")
    if not isinstance(cases, list) or len(cases) != 1:
        raise CheckFailure("seed.json must contain exactly one case")
    case = cases[0]

    original_hash = sha256(Path(bpmn_path))

    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    solution_dir = LIVE_RUN_DIR / "EscalationSlackAlertLiveEval"
    initialized = run_cli(
        ["uip", "solution", "init", str(solution_dir)],
        timeout=SOLUTION_INIT_TIMEOUT,
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
    if sha256(imported_project / Path(bpmn_path).name) != original_hash:
        raise CheckFailure("solution import changed the submitted BPMN bytes")
    print(f"OK: imported exact artifact (sha256={original_hash})")

    debug_data, instance_id = run_debug(
        imported_project, case["inputs"], LIVE_RUN_DIR / "debug.log"
    )
    print(f"OK: debug completed (instance {instance_id})")

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

    ts = assert_outcome(contract, case, debug_data, variables_data, incidents_data)
    print(
        f"OK: {case['name']} completed -- Sev1 + engineering classified, "
        f"correlationId preserved, and the Slack alert was posted (ts={ts})"
    )


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
