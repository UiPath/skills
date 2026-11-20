#!/usr/bin/env python3
"""EscalationSlackAlert: run the agent's process once with the seeded Sev1
case, from the grader's own sandbox, and assert what the run did.

Asserted on the run:
- it completed with no incidents;
- a Slack step completed, and the message it posted (its own response) went
  to #coding-agent-testing and carries the correlationId and the severity;
- the outputs the request names read back by name: severity=Sev1,
  engineeringNeeded=true, caseKey=<correlationId>, and slackMessageId equal to
  the ts Slack returned for that post (a real external effect).

Static, layout-free guards: the Slack step that posted sends as `user`, as the
request asks (a bot post has an indistinguishable response); and the process
names all three severities, so it encodes the rule rather than returning the
one answer the seeded case expects.

The Slack step is found by its connector key, whatever its operation, element
type or id; no script task, gateway or variable name is required.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_SUITE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _SUITE_DIR)
sys.path.insert(0, os.path.join(_SUITE_DIR, "_setup"))

import escalation_is  # noqa: E402
from _shared import bpmn_check  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    CheckFailure,
    assert_rule_encoded,
    completed_ids,
    debug_evidence,
    element_output_records,
    get_ci,
    import_exact,
    index_runtime_connectors,
    named_values,
    norm_value,
    q,
    require_clean_run,
    run_debug,
)

NAME = "EscalationSlackAlert"
LIVE_RUN_DIR = Path("escalation-slack-alert-live")


def assert_named(process, variables_data, name: str, expected, *, case_sensitive: bool = False) -> None:
    values = named_values(process, variables_data, name)
    if case_sensitive:
        ok = any(isinstance(v, str) and v.strip() == expected for v in values)
    else:
        ok = any(norm_value(v) == norm_value(expected) for v in values)
    if not ok:
        raise CheckFailure(f"output {name!r}: expected {expected!r}, got {values!r}")


def slack_ids(process: ET.Element) -> set[str]:
    ids = {
        element_id
        for (key, _path, _obj), element_ids in index_runtime_connectors(process).items()
        if key == escalation_is.SLACK_CONNECTOR
        for element_id in element_ids
    }
    if not ids:
        raise CheckFailure(f"the process has no {escalation_is.SLACK_CONNECTOR} step")
    return ids


def posted_messages(variables_data, element_ids) -> list[tuple[str, dict]]:
    """(element id, Slack response) for each executed Slack step that returned a ts."""
    found = []
    for element_id in sorted(element_ids):
        for record in element_output_records(variables_data, element_id):
            response = get_ci(record, "response")
            ts = get_ci(response, "ts") if isinstance(response, dict) else None
            if isinstance(ts, str) and escalation_is.SLACK_TS_RE.match(ts.strip()):
                found.append((element_id, response))
    return found


def assert_outcome(process, case: dict, debug_data, variables_data) -> str:
    ran = set(completed_ids(debug_data)) & slack_ids(process)
    if not ran:
        raise CheckFailure("no Slack step completed in the run; the alert was not posted")
    posts = posted_messages(variables_data, ran)
    if not posts:
        raise CheckFailure(f"Slack step(s) {sorted(ran)} completed but returned no message ts")

    distinct = {get_ci(r, "ts").strip() for _, r in posts}
    if len(distinct) != 1:
        raise CheckFailure(f"expected exactly one posted Slack message, the run posted {sorted(distinct)}")

    expected = case["expected"]
    correlation = case["inputs"]["correlationId"]
    assert_named(process, variables_data, "severity", expected["severity"])
    assert_named(process, variables_data, "engineeringNeeded", expected["engineeringNeeded"])
    assert_named(process, variables_data, "caseKey", expected["caseKey"], case_sensitive=True)

    message_ids = [str(v).strip() for v in named_values(process, variables_data, "slackMessageId")]
    matched = [(eid, r) for eid, r in posts if get_ci(r, "ts").strip() in message_ids]
    if not matched:
        raise CheckFailure(
            f"slackMessageId {message_ids!r} is not the ts of the message the run posted "
            f"{[get_ci(r, 'ts') for _, r in posts]!r}"
        )
    element_id, response = matched[0]

    sends_as = bpmn_check.query_values(next(e for e in process.iter() if e.attrib.get("id") == element_id), "send_as")
    if sends_as != ["user"]:
        raise CheckFailure(f"Slack step {element_id!r} must post as 'user', found send_as={sends_as!r}")

    channel = get_ci(response, "channel")
    if channel != escalation_is.SLACK_CHANNEL:
        raise CheckFailure(f"the alert went to channel {channel!r}, expected {escalation_is.SLACK_CHANNEL!r} (#coding-agent-testing)")
    message = get_ci(response, "message")
    text = get_ci(message, "text") if isinstance(message, dict) else None
    missing = [t for t in (correlation, expected["severity"]) if not isinstance(text, str) or t not in text]
    if missing:
        raise CheckFailure(f"the posted alert does not carry {missing}: {text!r}")
    return get_ci(response, "ts")


def main() -> None:
    escalation_is.assert_live_target()
    bpmn_path = bpmn_check.locate_bpmn(f"{NAME}.bpmn", [LIVE_RUN_DIR])
    bpmn_text = bpmn_path.read_text(encoding="utf-8")
    process = ET.fromstring(bpmn_text.encode("utf-8")).find(q(BPMN_NS, "process"))
    if process is None:
        raise CheckFailure(f"{bpmn_path} has no bpmn:process")
    slack_ids(process)
    assert_rule_encoded(bpmn_text)

    seed = json.loads(Path("seed.json").read_text(encoding="utf-8"))
    (case,) = seed["cases"]

    imported = import_exact(bpmn_path, bpmn_path.parent, LIVE_RUN_DIR / f"{NAME}LiveEval")
    # Posts a real message, so no whole-run retry.
    log_file = LIVE_RUN_DIR / "debug.log"
    debug_data = None
    try:
        debug_data, instance_id = run_debug(imported, case["inputs"], log_file, timeout=480)
        evidence = debug_evidence(instance_id)
    except (CheckFailure, subprocess.TimeoutExpired):
        escalation_is.journal_slack_posts_in_log(log_file, debug_data)
        raise
    escalation_is.journal_slack_posts(evidence.variables, set(completed_ids(debug_data)) & slack_ids(process))
    require_clean_run(debug_data, evidence)
    ts = assert_outcome(process, case, debug_data, evidence.variables)
    print(f"OK: {case['name']}: Sev1 + engineering, correlationId kept, Slack alert posted (ts={ts})")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
