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
    CheckFailure,
    completed_ids,
    element_output_records,
    fetch_incidents,
    fetch_variables,
    get_ci,
    import_exact,
    index_runtime_connectors,
    named_values,
    q,
    run_debug,
)

NAME = "CustomerEscalationOrchestrator"
SLACK_CONNECTOR = "uipath-salesforce-slack"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
SLACK_TS_RE = re.compile(r"^\d{9,11}\.\d{4,6}$")
LIVE_RUN_DIR = Path("escalation-orchestrator-live")
OUTPUTS = ("escalationPath", "severity", "engineeringNeeded", "responseMode", "caseKey")


def _norm(value):
    if isinstance(value, str):
        text = value.strip().casefold()
        return {"true": True, "false": False}.get(text, text)
    return value


def _loose(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


# Squashed spellings the word split cannot separate ("nodraft", "noresponserequired").
_NO_RESPONSE = {
    "na", "nodraft", "noresponse", "notrequired", "noresponserequired",
    "noresponseneeded", "notapplicable", "notneeded", "draftnotneeded",
}
_NEGATED_DRAFT = re.compile(
    r"\b(?:no|not|without|dont|do not|none)\s+(?:a\s+|any\s+)?(?:draft|response)\b"
    r"|\bdraft\s+(?:is\s+)?(?:not|no)\s+(?:needed|required|applicable|necessary)\b"
    r"|\bdraft\s+(?:none|false|n a|na)\b"
    r"|^(?:n a|none|false|not applicable|not required|not needed)$"
)


def _words(text: str) -> str:
    unquoted = re.sub(r"['\u2019]", "", text)
    return " ".join(re.findall(r"[a-z0-9]+", re.sub(r"([a-z])([A-Z])", r"\1 \2", unquoted).lower()))


def response_mode(value) -> str | None:
    """'draft' or 'none' by meaning: the request no longer names the values, only
    that a draft response is written for escalations that need engineering.
    A negation counts only when it governs the draft ("No draft", "Draft not
    needed"), so "Draft, no edits required" is still 'draft'. Anything else is
    None (unknown)."""
    if isinstance(value, bool):
        return "draft" if value else "none"
    if not isinstance(value, str):
        return None
    text = _loose(value)
    if text in _NO_RESPONSE or _NEGATED_DRAFT.search(_words(value)):
        return "none"
    if "draft" in text:
        return "draft"
    return None


def names_path(text: str, path: str) -> bool:
    """`path` appears as its own word(s), in any case and with `_`, `-` or a
    space between its parts: "unknown customer" names unknown_customer, while
    "CustomerEscalationOrchestrator" or "escalations" does not name escalation."""
    parts = r"[\s_-]*".join(re.escape(p) for p in path.split("_"))
    return re.search(rf"(?<![a-z0-9]){parts}(?![a-z0-9])", text, re.IGNORECASE) is not None


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
            wanted = response_mode(expected[field])
            ok = wanted is not None and any(response_mode(v) == wanted for v in values)
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
    if not isinstance(text, str) or correlation not in text or not names_path(text, expected["escalationPath"]):
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
    bpmn_path = bpmn_check.locate_bpmn(f"{NAME}.bpmn", [LIVE_RUN_DIR])
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

    bpmn_path = bpmn_check.locate_bpmn(f"{NAME}.bpmn", [LIVE_RUN_DIR])
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
