#!/usr/bin/env python3
"""Run each seeded escalation-orchestrator path case and verify its outcome.

Ported from Flow `e2e/escalation_orchestrator_paths/check_escalation_orchestrator_paths.py`:
same seven seeded cases (Sev1/Sev2/Sev3 escalation + four triage reasons), same
graded behaviours, translated from `flow debug`'s inline-variable payload to
`bpmn debug`'s instance-id + `debug-instance variables-all` surface (see
`_shared/bpmn_live.py` and the LIVE-tier addendum this port followed).

Outcome-based: for every case the grader runs `uip maestro bpmn debug --inputs`
against ONE ephemeral-solution import of the exact submitted project, then reads
`debug-instance variables-all` for the expected values. For cases flagged
`expect_slack`, it additionally requires the completed Slack sendTask's OWN
runtime response to carry a real message timestamp — Slack only returns one
when a message is really delivered, not merely reached.

Assertion map (Flow -> BPMN):
  F check_escalation_orchestrator_paths.py:106  assert_flow_uses_connector_target(SLACK_KEY)
      -> Contract.slack_ids non-empty (resolve_contract)
  F check_escalation_orchestrator_paths.py:144  assert_connector_error_handlers(SLACK_KEY, ...)
      -> assert_error_handlers(): boundary errorEventDefinition on each Slack sendTask reaches a connector-free,
         acyclic, terminating path
  F check_escalation_orchestrator_paths.py:145  assert_connector_send_identity(SLACK_KEY, "user", ...)
      -> assert_send_identity(): every Slack sendTask carries target=query name=send_as value=user
  F check_escalation_orchestrator_paths.py:55   assert_named_equals(payload, name, expected, ...)
      -> public_value_present(): normalized value present among root Globals leaves + non-classifier element Outputs
         leaves, input echoes (input_echo_ids) excluded from both except for caseKey, which the
         contract sets to the correlationId input (see NOTE below)
  F check_escalation_orchestrator_paths.py:65   assert_slack_message_posted(payload, "slackMessageId", ...)
      -> assert_slack_posted(): fired Slack sendTask's own Outputs.response carries a ts-shaped id, the seeded
         channel, and correlationId + escalationPath in its text
  F check_escalation_orchestrator_paths.py:78-90 completed_node_ids_of_type(payload,"script") + is_classifier
      -> classifier candidate set per case: a scriptTask whose OWN Outputs.response dict carries all four
         CLASSIFICATION_FIELDS matching expected
  F check_escalation_orchestrator_paths.py:95   assert_node_type_executed(payload,"core.logic.decision")
      -> per-case fired_gateways non-empty
  F check_escalation_orchestrator_paths.py:97-98 completed_node_ids_of_type(payload,
     "core.logic.decision"/"core.control.end")
      -> per-case fired_gateways / fired_ends via debug_data.ElementExecutions
  F check_escalation_orchestrator_paths.py:132-139 common_classifier = intersection(per_case_classifiers)
      -> same intersection, same failure message shape
  F check_escalation_orchestrator_paths.py:149-158 escalation/triage Slack-node disjointness
      -> same set overlap check
  F check_escalation_orchestrator_paths.py:167-169 routing_decisions + assert_decision_branches_reach
      -> assert_decision_branches_reach(): exclusiveGateway's two outgoing sequenceFlows separate the fired Slack node
         sets (graph.reachable)
  F check_escalation_orchestrator_paths.py:179   assert_distinct_branch_ends(escalation_nodes, triage_nodes)
      -> assert_distinct_branch_ends(): each fired-Slack-node set reaches its own endEvent, the other's not reachable
         (graph.reachable)
  F check_escalation_orchestrator_paths.py:180-189 runtime escalation_ends/triage_ends disjointness
      -> same runtime disjointness check over per-case fired_ends
  I               locate/parse .bpmn, resolve project directory
      -> resolve_project() / resolve_contract()
  I               ephemeral solution init + import + sha256 pin, run bpmn debug per case, read variables-all
      -> LIVE-tier canonical pattern (bpmn_live.import_exact() + run_debug())
  T               finalStatus/elementExecutions completion check (flow_check.run_debug does this inline for `flow
     debug`; `bpmn debug` does not)
      -> per-case FinalStatus check in verify_case()
  T               vars.<VarId> / element Outputs in place of Flow's globals["<nodeId>.output"]
      -> element_output_records() / root_scope() (bpmn_live.py)
  T               NOTE (LIVE-ADDENDUM): a BPMN process with two end events may declare the SAME public
                  output name twice (once per end event, elementId-scoped per structural-bpmn.md), and
                  the branch that did not run has been observed to read back null even when the OTHER
                  branch's identically-named declaration is correctly populated. So the named-output
                  check searches value leaves broadly (root Globals + every OTHER element's Outputs)
                  instead of one pinned root-output id, per the addendum's explicit tolerance for this.
                  The classifier's OWN Outputs are excluded from that search (see CLASSIFICATION_FIELDS
                  binding above) so a value that was only ever computed, never mapped to a public output,
                  cannot satisfy this check by coincidence.
  DROPPED         Flow's exact_type check on public outputs (customer_escalation_triage-style)            (not in this
  Flow task's grader)
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # tests/tasks/uipath-maestro-bpmn/

from _shared import graph  # noqa: E402
from _shared.bpmn_check import NS, attr, elements, resolve_project  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    COMPLETED_STATUSES,
    CheckFailure,
    UIPATH_NS,
    VARIABLES_ALL_TIMEOUT,
    connector_context,
    element_output_records,
    get_ci,
    import_exact,
    index_runtime_connectors,
    input_echo_ids,
    output_leaves,
    payload_data,
    q,
    run_cli,
    run_debug,
)

SLACK_KEY = "uipath-salesforce-slack"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing (same tenant target as the flow suite)
SLACK_SEND_AS = "user"
# Registry object name for "Send Message to Channel" is send_message_to_channel_v2
# (registry-workflow.md L214); match loosely on the concept, as the flow suite's
# native_op_hint="send-message-to-channel" does.
SLACK_SEND_PATH_HINT = "send_message_to_channel"

PROJECT_NAME = "CustomerEscalationOrchestrator"
BPMN_NAME = f"{PROJECT_NAME}.bpmn"

CASE_SENSITIVE = {"caseKey"}  # opaque id -- exact-case match
PASSTHROUGH_FIELDS = {"caseKey"}  # the contract sets it to the correlationId input
CLASSIFICATION_FIELDS = ("escalationPath", "severity", "engineeringNeeded", "responseMode")
NAMED_OUTPUT_FIELDS = CLASSIFICATION_FIELDS + ("caseKey",)

LIVE_RUN_DIR = Path("escalation-orchestrator-live")
DEBUG_TIMEOUT_SECONDS = 300  # literal on the run_debug call below -- the budget guard reads this statically
_SLACK_TS_RE = re.compile(r"^\d{9,11}\.\d{4,6}$")


@dataclass(frozen=True)
class Contract:
    classifier_ids: tuple[str, ...]
    gateway_ids: tuple[str, ...]
    slack_ids: tuple[str, ...]
    end_ids: tuple[str, ...]
    echo_ids: tuple[str, ...]


def resolve_contract(path: Path) -> Contract:
    root = ET.parse(path).getroot()
    process = root.find(q(BPMN_NS, "process"))
    if process is None:
        raise CheckFailure("BPMN must contain one root process")

    classifier_ids = tuple(
        el.attrib["id"] for el in process.iter(q(BPMN_NS, "scriptTask")) if el.attrib.get("id")
    )
    if not classifier_ids:
        raise CheckFailure(
            "no bpmn:scriptTask to classify the escalation path; the prompt "
            "requires ALL routing logic in one classifier scriptTask"
        )

    gateway_ids = tuple(
        el.attrib["id"] for el in process.iter(q(BPMN_NS, "exclusiveGateway")) if el.attrib.get("id")
    )
    if not gateway_ids:
        raise CheckFailure("no bpmn:exclusiveGateway to route escalation vs triage")

    end_ids = tuple(
        el.attrib["id"] for el in process.iter(q(BPMN_NS, "endEvent")) if el.attrib.get("id")
    )
    if not end_ids:
        raise CheckFailure("no bpmn:endEvent in the process")

    connectors = index_runtime_connectors(process)
    slack_ids = tuple(
        element_id
        for (key, connector_path, _object_name), element_ids in connectors.items()
        if key == SLACK_KEY and SLACK_SEND_PATH_HINT in connector_path
        for element_id in element_ids
    )
    if not slack_ids:
        raise CheckFailure(
            f"no {SLACK_KEY} activity with a registry path containing "
            f"{SLACK_SEND_PATH_HINT!r} -- the process must use the real Slack connector"
        )

    return Contract(
        classifier_ids=classifier_ids,
        gateway_ids=gateway_ids,
        slack_ids=slack_ids,
        end_ids=end_ids,
        echo_ids=tuple(sorted(input_echo_ids(process))),
    )


def assert_send_identity(process: ET.Element, slack_ids: tuple[str, ...]) -> None:
    bad = []
    for element in process.iter():
        if element.attrib.get("id") not in slack_ids:
            continue
        sends_as = [
            item.attrib.get("value")
            for item in element.iter(q(UIPATH_NS, "input"))
            if item.attrib.get("name") == "send_as"
        ]
        if sends_as != [SLACK_SEND_AS]:
            bad.append((element.attrib.get("id"), sends_as))
    if bad:
        raise CheckFailure(
            f"Slack sendTask(s) do not carry exactly one send_as input with "
            f"value {SLACK_SEND_AS!r}: {bad}; the prompt requires sending as the "
            "requested identity"
        )


def assert_error_handlers(root: ET.Element, process: ET.Element, slack_ids: tuple[str, ...]) -> None:
    """Every Slack sendTask's error boundary event must degrade gracefully.

    Mirrors flow_check.assert_connector_error_handlers: the handler chain must
    be connector-free, acyclic, and reach a terminating node (endEvent, or a
    node with no outgoing flow).
    """

    by_id = {el.attrib.get("id"): el for el in process.iter() if el.attrib.get("id")}
    boundary_events = elements(root, "boundaryEvent")
    outgoing: dict[str, list[str]] = {}
    for source, target in graph.edges(root):
        outgoing.setdefault(source, []).append(target)

    def is_connector(node_id: str) -> bool:
        element = by_id.get(node_id)
        return element is not None and bool(connector_context(element).get("connectorKey"))

    def reaches_terminating(start: str) -> bool:
        color: dict[str, int] = {}
        GRAY, BLACK = 1, 2

        def dfs(node_id: str) -> bool:
            if is_connector(node_id):
                return False
            color[node_id] = GRAY
            outs = outgoing.get(node_id, [])
            element = by_id.get(node_id)
            tag = element.tag.rsplit("}", 1)[-1] if element is not None else ""
            if tag == "endEvent" or not outs:
                color[node_id] = BLACK
                return True
            for target in outs:
                state = color.get(target, 0)
                if state == GRAY:
                    return False
                if state == BLACK:
                    continue
                if not dfs(target):
                    return False
            color[node_id] = BLACK
            return True

        return dfs(start)

    bad = []
    for slack_id in slack_ids:
        handlers = [
            b
            for b in boundary_events
            if attr(b, "attachedToRef") == slack_id
            and b.find("bpmn:errorEventDefinition", NS) is not None
        ]
        if not handlers:
            bad.append((slack_id, "no error boundary event attached"))
            continue
        targets = [t for b in handlers for t in outgoing.get(attr(b, "id"), [])]
        if not targets or not any(reaches_terminating(t) for t in targets):
            bad.append((slack_id, "error boundary event does not reach a terminating, connector-free path"))
    if bad:
        raise CheckFailure(
            f"{SLACK_KEY} sendTask(s) do not degrade gracefully on failure: {bad}"
        )


def assert_decision_branches_reach(
    root: ET.Element,
    gateway_ids: set,
    escalation_targets: set,
    triage_targets: set,
) -> None:
    outgoing: dict[str, list[str]] = {}
    for source, target in graph.edges(root):
        outgoing.setdefault(source, []).append(target)

    for gateway_id in gateway_ids:
        branch_targets = outgoing.get(gateway_id, [])
        reach_by_target = {t: ({t} | graph.reachable(root, t)) for t in branch_targets}
        for ta, ra in reach_by_target.items():
            if not escalation_targets <= ra:
                continue
            for tb, rb in reach_by_target.items():
                if tb == ta:
                    continue
                if triage_targets <= rb and not (escalation_targets & rb) and not (triage_targets & ra):
                    return
    raise CheckFailure(
        f"no exclusiveGateway routes {sorted(escalation_targets)} and "
        f"{sorted(triage_targets)} through separate branches -- the distinct "
        "Slack sendTasks are not the gateway's two outgoing paths"
    )


def assert_distinct_branch_ends(
    root: ET.Element, end_ids: tuple[str, ...], branch_a_nodes: set, branch_b_nodes: set
) -> None:
    def reachable_ends(nodes: set) -> set:
        found: set = set()
        for node in nodes:
            found |= ({node} | graph.reachable(root, node)) & set(end_ids)
        return found

    ends_a = reachable_ends(branch_a_nodes)
    ends_b = reachable_ends(branch_b_nodes)
    if not (ends_a - ends_b) or not (ends_b - ends_a):
        raise CheckFailure(
            "escalation and triage branches do not each reach their OWN "
            f"endEvent (escalation-reachable={sorted(ends_a)}, "
            f"triage-reachable={sorted(ends_b)}); the prompt requires two "
            "branch-specific end events, not a single merged one"
        )


def normalized(value, *, case_fold: bool = True):
    if isinstance(value, str):
        text = value.strip()
        lowered = text.casefold()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        return lowered if case_fold else text
    return value


def _loose_contains(haystack: str, needle: str) -> bool:
    norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
    return norm(needle) in norm(haystack)


def public_value_present(
    variables_data, expected, *, exclude_ids: tuple[str, ...], case_sensitive: bool
) -> bool:
    """Whether `expected` shows up among root Globals or element Outputs, minus
    the Globals and elements named in `exclude_ids` -- see the module docstring
    NOTE on why this is a broad leaf search rather than one pinned root-output id."""

    target = normalized(expected, case_fold=not case_sensitive)
    candidates = output_leaves(variables_data, exclude_ids)
    return any(normalized(v, case_fold=not case_sensitive) == target for v in candidates)


def is_classifier_output(record, expected: dict) -> bool:
    response = get_ci(record, "response")
    if not isinstance(response, dict):
        return False
    return all(
        normalized(get_ci(response, field)) == normalized(expected[field])
        for field in CLASSIFICATION_FIELDS
    )


def assert_slack_posted(variables_data, fired_slack_ids: set, case: dict) -> None:
    if not fired_slack_ids:
        raise CheckFailure(f"{case['name']}: no Slack sendTask executed; expected a real Slack post")
    outputs = element_output_records(variables_data, tuple(fired_slack_ids))
    matched = None
    for output in outputs:
        response = get_ci(output, "response")
        ts = get_ci(response, "ts")
        if isinstance(ts, str) and _SLACK_TS_RE.match(ts.strip()):
            matched = response
            break
    if matched is None:
        raise CheckFailure(
            f"{case['name']}: no executed Slack sendTask's response carries a "
            "message ts; the process did not actually post to Slack"
        )
    channel = get_ci(matched, "channel")
    if channel != SLACK_CHANNEL:
        raise CheckFailure(
            f"{case['name']}: Slack message posted to channel {channel!r}, "
            f"expected {SLACK_CHANNEL!r}"
        )
    message = get_ci(matched, "message")
    text = get_ci(message, "text") if isinstance(message, dict) else None
    correlation_id = case["inputs"]["correlationId"]
    if not isinstance(text, str) or correlation_id not in text:
        raise CheckFailure(
            f"{case['name']}: Slack message text does not carry correlationId "
            f"{correlation_id!r}: {text!r}"
        )
    if not _loose_contains(text, case["expected"]["escalationPath"]):
        raise CheckFailure(
            f"{case['name']}: Slack message text does not carry escalationPath "
            f"{case['expected']['escalationPath']!r}: {text!r}"
        )


def verify_case(contract: Contract, imported_project: Path, case: dict) -> dict:
    log_file = LIVE_RUN_DIR / f"debug-{case['name']}.log"
    # DEBUG_TIMEOUT_SECONDS is inlined below (not passed by name) so the
    # static budget guard (test_criterion_budgets.py) can read the literal.
    debug_data, _instance_id = run_debug(
        imported_project, case["inputs"], log_file, timeout=300
    )

    final_status = get_ci(debug_data, "FinalStatus")
    executions = get_ci(debug_data, "ElementExecutions", []) or []
    if final_status not in COMPLETED_STATUSES:
        faulted = [
            f"{get_ci(item, 'ElementId')}={get_ci(item, 'Status')}"
            for item in executions
            if isinstance(item, dict)
            and str(get_ci(item, "Status") or "").casefold() != "completed"
        ]
        raise CheckFailure(
            f"{case['name']}: final status was {final_status!r}"
            + (f"; non-completed elements: {faulted}" if faulted else "")
        )

    variables = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "variables-all", _instance_id],
        timeout=VARIABLES_ALL_TIMEOUT,
    )
    _payload, variables_data = payload_data(variables, f"{case['name']}: variables-all")

    completed_ids = {
        get_ci(item, "ElementId")
        for item in executions
        if isinstance(item, dict) and str(get_ci(item, "Status") or "").casefold() == "completed"
    }
    fired_slack = completed_ids & set(contract.slack_ids)
    fired_gateways = completed_ids & set(contract.gateway_ids)
    fired_ends = completed_ids & set(contract.end_ids)

    if not fired_gateways:
        raise CheckFailure(f"{case['name']}: no exclusiveGateway executed in the debug trace")

    classifier_candidates = {
        node_id
        for node_id in contract.classifier_ids
        if any(
            is_classifier_output(record, case["expected"])
            for record in element_output_records(variables_data, (node_id,))
        )
    }
    if not classifier_candidates:
        raise CheckFailure(
            f"{case['name']}: no single executed scriptTask computed all of "
            f"{CLASSIFICATION_FIELDS} together -- the prompt requires ALL "
            "routing logic in ONE scriptTask that returns every field"
        )

    for field in NAMED_OUTPUT_FIELDS:
        expected_value = case["expected"][field]
        if not public_value_present(
            variables_data,
            expected_value,
            exclude_ids=contract.classifier_ids
            + (() if field in PASSTHROUGH_FIELDS else contract.echo_ids),
            case_sensitive=field in CASE_SENSITIVE,
        ):
            raise CheckFailure(f"{case['name']}: no public output carries {field}={expected_value!r}")

    if case.get("expect_slack"):
        assert_slack_posted(variables_data, fired_slack, case)

    print(
        f"OK: {case['name']} produced the expected outcome"
        + (" + Slack message posted" if case.get("expect_slack") else "")
    )
    return {
        "fired_slack": fired_slack,
        "fired_gateways": fired_gateways,
        "fired_ends": fired_ends,
        "classifier_candidates": classifier_candidates,
    }


def main() -> None:
    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise CheckFailure("seed.json is missing; pre_run did not complete")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    cases = seed.get("cases")
    if not isinstance(cases, list) or not cases:
        raise CheckFailure("seed.json must contain at least one case")

    project_dir = resolve_project(BPMN_NAME)
    bpmn_path = project_dir / BPMN_NAME
    contract = resolve_contract(bpmn_path)
    root = ET.parse(bpmn_path).getroot()
    process = root.find(q(BPMN_NS, "process"))

    # The escalation alert must go through the real Slack connector, wired for
    # graceful degradation and the requested send identity -- static checks,
    # before spending any live budget.
    assert_send_identity(process, contract.slack_ids)
    assert_error_handlers(root, process, contract.slack_ids)

    imported_project = import_exact(
        bpmn_path, project_dir, LIVE_RUN_DIR / "EscalationOrchestratorLiveEval"
    )

    escalation_fired: set = set()
    triage_fired: set = set()
    escalation_ends: set = set()
    triage_ends: set = set()
    per_case_gateways: list = []
    per_case_classifiers: list = []

    for case in cases:
        result = verify_case(contract, imported_project, case)
        is_escalation = case["expected"]["escalationPath"] == "escalation"
        (escalation_fired if is_escalation else triage_fired).update(result["fired_slack"])
        (escalation_ends if is_escalation else triage_ends).update(result["fired_ends"])
        per_case_gateways.append(result["fired_gateways"])
        per_case_classifiers.append(result["classifier_candidates"])

    # ONE classifier scriptTask must classify EVERY case (prompt: ALL routing
    # logic in one scriptTask).
    common_classifier = set.intersection(*per_case_classifiers) if per_case_classifiers else set()
    if not common_classifier:
        raise CheckFailure(
            "no single scriptTask classified every case -- the prompt requires "
            "ALL routing logic in ONE scriptTask, but the cases were classified "
            "by different (path-specific) scriptTasks (per-case candidates: "
            f"{[sorted(c) for c in per_case_classifiers]})"
        )
    print(f"OK: one classifier scriptTask handled all cases: {sorted(common_classifier)}")

    # The gateway must genuinely branch: escalation and triage post via
    # DIFFERENT Slack sendTasks.
    if not escalation_fired or not triage_fired:
        raise CheckFailure(
            "expected both escalation and triage cases to fire a Slack "
            f"sendTask (escalation={escalation_fired}, triage={triage_fired})"
        )
    overlap = escalation_fired & triage_fired
    if overlap:
        raise CheckFailure(
            f"escalation and triage cases fired the SAME Slack sendTask(s) "
            f"{overlap} -- the gateway does not route to two distinct branches"
        )

    # And prove those two sendTasks are the gateway's OWN outgoing branches,
    # routed by a gateway that executed in EVERY case.
    routing_gateways = set.intersection(*per_case_gateways) if per_case_gateways else set()
    if not routing_gateways:
        raise CheckFailure(
            "no EXECUTED exclusiveGateway in every run (executed sets: "
            f"{[sorted(g) for g in per_case_gateways]}); routing did not go "
            "through a gateway that actually ran every time"
        )
    assert_decision_branches_reach(root, routing_gateways, escalation_fired, triage_fired)

    # The prompt requires TWO end events -- one per branch. Static reachability
    # closes the "unused private end event + shared merged end" gaming; the
    # runtime disjointness below closes the "both real paths merge into one
    # shared end event" gaming.
    assert_distinct_branch_ends(root, contract.end_ids, escalation_fired, triage_fired)
    if not escalation_ends or not triage_ends:
        raise CheckFailure(
            "expected both escalation and triage cases to complete an "
            f"endEvent (escalation_ends={sorted(escalation_ends)}, "
            f"triage_ends={sorted(triage_ends)})"
        )
    shared_ends = escalation_ends & triage_ends
    if shared_ends:
        raise CheckFailure(
            f"escalation and triage cases completed the SAME endEvent(s) "
            f"{sorted(shared_ends)} -- both branches merge into one shared "
            "end event; the prompt requires a distinct end event per branch"
        )
    print(
        "OK: branches complete distinct end events "
        f"(escalation={sorted(escalation_ends)}, triage={sorted(triage_ends)})"
    )
    print(
        "OK: an exclusiveGateway routes escalation vs triage through separate "
        f"branches (escalation={sorted(escalation_fired)}, triage={sorted(triage_fired)})"
    )


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
