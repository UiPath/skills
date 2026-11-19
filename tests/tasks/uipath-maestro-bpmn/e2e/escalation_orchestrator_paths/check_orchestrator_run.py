#!/usr/bin/env python3
"""CustomerEscalationOrchestrator: run the agent's process once per seeded
path case, from the grader's own sandbox, and assert what each run did.

Seven cases (seed.py): Sev1/Sev2/Sev3 escalations and the four triage
reasons. For each run:
- it completed;
- exactly one Slack step completed (the alert or the triage notice, never
  both), and the message it posted (its own response) went to
  #coding-agent-testing, as `user`, carrying the correlationId and the
  escalation path: a real external effect;
- the outputs the request names read back by name: escalationPath, severity,
  engineeringNeeded, responseMode, caseKey=<correlationId>, and
  slackMessageId equal to the ts Slack returned for that post.

Seven input-driven cases with different answers prove the routing is
computed, so no layout is required: no script task, gateway, end-event count
or variable name the request does not give. The old grader required one
classifier script returning all four fields, a single exclusive gateway,
two Slack steps and two end events.

`slack_failure_handled` mode (advisory) checks that each Slack step has an
error boundary leading to a connector-free end, as the request asks.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared import bpmn_check  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    COMPLETED_STATUSES,
    UIPATH_NS,
    CheckFailure,
    element_output_records,
    fetch_incidents,
    fetch_variables,
    get_ci,
    import_exact,
    index_runtime_connectors,
    normalized_identifier,
    q,
    root_scope,
    run_debug,
)

NAME = "CustomerEscalationOrchestrator"
SLACK_CONNECTOR = "uipath-salesforce-slack"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
SLACK_TS_RE = re.compile(r"^\d{9,11}\.\d{4,6}$")
LIVE_RUN_DIR = Path("escalation-orchestrator-live")
OUTPUTS = ("escalationPath", "severity", "engineeringNeeded", "responseMode", "caseKey")


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
    GlobalDefinitions Name is `name`, and the `name` output of the element each
    declaration belongs to (an end event; the branch that did not run reads
    back null and is skipped)."""
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


def _norm(value):
    if isinstance(value, str):
        text = value.strip().casefold()
        return {"true": True, "false": False}.get(text, text)
    return value


def _loose(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


_NO_RESPONSE = {"none", "", "no", "false", "noresponse", "notrequired", "noresponserequired", "na"}


def response_mode(value) -> str | None:
    """'draft' or 'none' by meaning: the request no longer names the values, only
    that a draft response is written for escalations that need engineering."""
    if isinstance(value, bool):
        return "draft" if value else "none"
    if isinstance(value, str):
        text = _loose(value)
        if "draft" in text:
            return "draft"
        if text in _NO_RESPONSE:
            return "none"
    return None


def slack_ids(process: ET.Element) -> set[str]:
    ids = {
        element_id
        for (key, _path, _obj), element_ids in index_runtime_connectors(process).items()
        if key == SLACK_CONNECTOR
        for element_id in element_ids
    }
    if not ids:
        raise CheckFailure(f"the process has no {SLACK_CONNECTOR} step")
    return ids


def completed_ids(debug_data) -> list[str]:
    return [
        get_ci(item, "ElementId")
        for item in get_ci(debug_data, "ElementExecutions", []) or []
        if isinstance(item, dict) and str(get_ci(item, "Status") or "").casefold() == "completed"
    ]


def verify_case(process, slack: set[str], case: dict, debug_data, variables_data) -> str:
    name = case["name"]
    final_status = get_ci(debug_data, "FinalStatus")
    if final_status not in COMPLETED_STATUSES:
        raise CheckFailure(f"{name}: final status was {final_status!r}")

    expected = case["expected"]
    for field in OUTPUTS:
        values = named_values(process, variables_data, field)
        if field == "caseKey":
            ok = any(isinstance(v, str) and v.strip() == expected[field] for v in values)
        elif field == "responseMode":
            ok = any(response_mode(v) == response_mode(expected[field]) for v in values)
        else:
            ok = any(_norm(v) == _norm(expected[field]) for v in values)
        if not ok:
            raise CheckFailure(f"{name}: output {field!r}: expected {expected[field]!r}, got {values!r}")

    ran = [eid for eid in completed_ids(debug_data) if eid in slack]
    if len(ran) != 1:
        raise CheckFailure(f"{name}: expected exactly one Slack post in the run, Slack steps completed: {ran}")
    (element_id,) = ran
    responses = [get_ci(r, "response") for r in element_output_records(variables_data, element_id)]
    response = next(
        (r for r in responses if isinstance(r, dict) and SLACK_TS_RE.match(str(get_ci(r, "ts") or "").strip())),
        None,
    )
    if response is None:
        raise CheckFailure(f"{name}: Slack step {element_id!r} completed but returned no message ts")
    ts = get_ci(response, "ts").strip()

    message_ids = [str(v).strip() for v in named_values(process, variables_data, "slackMessageId")]
    if ts not in message_ids:
        raise CheckFailure(f"{name}: slackMessageId {message_ids!r} is not the posted message's ts {ts!r}")

    element = next(e for e in process.iter() if e.attrib.get("id") == element_id)
    sends_as = bpmn_check.query_values(element, "send_as")
    if sends_as != ["user"]:
        raise CheckFailure(f"{name}: Slack step {element_id!r} must post as 'user', found send_as={sends_as!r}")
    channel = get_ci(response, "channel")
    if channel != SLACK_CHANNEL:
        raise CheckFailure(f"{name}: posted to channel {channel!r}, expected {SLACK_CHANNEL!r} (#coding-agent-testing)")
    message = get_ci(response, "message")
    text = get_ci(message, "text") if isinstance(message, dict) else None
    correlation = case["inputs"]["correlationId"]
    if not isinstance(text, str) or correlation not in text or _loose(expected["escalationPath"]) not in _loose(text):
        raise CheckFailure(f"{name}: the posted message does not carry {correlation!r} and {expected['escalationPath']!r}: {text!r}")
    return ts


def load_process(bpmn_path: Path) -> ET.Element:
    process = ET.parse(bpmn_path).getroot().find(q(BPMN_NS, "process"))
    if process is None:
        raise CheckFailure(f"{bpmn_path} has no bpmn:process")
    return process


def cases() -> None:
    seed = json.loads(Path("seed.json").read_text(encoding="utf-8"))
    seeded = seed["cases"]
    bpmn_path = locate_bpmn()
    process = load_process(bpmn_path)
    slack = slack_ids(process)

    imported = import_exact(bpmn_path, bpmn_path.parent, LIVE_RUN_DIR / "EscalationOrchestratorLiveEval")
    for case in seeded:
        # Posts a real message, so no whole-run retry. timeout is a literal so
        # test_criterion_budgets.py can price it.
        debug_data, instance_id = run_debug(
            imported, case["inputs"], LIVE_RUN_DIR / f"debug-{case['name']}.log", timeout=300
        )
        variables_data, _text = fetch_variables(instance_id)
        try:
            ts = verify_case(process, slack, case, debug_data, variables_data)
        except CheckFailure as error:
            try:
                incidents, _raw = fetch_incidents(instance_id)
            except (CheckFailure, subprocess.TimeoutExpired):
                incidents = None
            raise CheckFailure(f"{error}" + (f"; incidents: {json.dumps(incidents)[:1500]}" if incidents else "")) from error
        print(f"OK: {case['name']} took its path and posted to Slack (ts={ts})")
    print(f"OK: all {len(seeded)} path cases produced the expected outcome")


def slack_failure_handled() -> None:
    from _shared.check_escalation_orchestrator_paths import assert_error_handlers

    bpmn_path = locate_bpmn()
    root = ET.parse(bpmn_path).getroot()
    process = root.find(q(BPMN_NS, "process"))
    assert_error_handlers(root, process, tuple(sorted(slack_ids(process))))
    print("OK: every Slack step has an error boundary that ends the process cleanly")


DISPATCH = {"cases": cases, "slack_failure_handled": slack_failure_handled}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "cases"
    try:
        DISPATCH[mode]()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
