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
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared import bpmn_check  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    UIPATH_NS,
    CheckFailure,
    debug_evidence,
    element_output_records,
    get_ci,
    import_exact,
    index_runtime_connectors,
    normalized_identifier,
    q,
    require_clean_run,
    root_scope,
    run_debug,
)

NAME = "EscalationSlackAlert"
SLACK_CONNECTOR = "uipath-salesforce-slack"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
SLACK_TS_RE = re.compile(r"^\d{9,11}\.\d{4,6}$")
SEVERITIES = ("Sev1", "Sev2", "Sev3")
LIVE_RUN_DIR = Path("escalation-slack-alert-live")


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


def _norm(value):
    if isinstance(value, str):
        text = value.strip().casefold()
        return {"true": True, "false": False}.get(text, text)
    return value


def assert_named(process, variables_data, name: str, expected, *, case_sensitive: bool = False) -> None:
    values = named_values(process, variables_data, name)
    if case_sensitive:
        ok = any(isinstance(v, str) and v.strip() == expected for v in values)
    else:
        ok = any(_norm(v) == _norm(expected) for v in values)
    if not ok:
        raise CheckFailure(f"output {name!r}: expected {expected!r}, got {values!r}")


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


def posted_messages(variables_data, element_ids) -> list[tuple[str, dict]]:
    """(element id, Slack response) for each executed Slack step that returned a ts."""
    found = []
    for element_id in sorted(element_ids):
        for record in element_output_records(variables_data, element_id):
            response = get_ci(record, "response")
            ts = get_ci(response, "ts") if isinstance(response, dict) else None
            if isinstance(ts, str) and SLACK_TS_RE.match(ts.strip()):
                found.append((element_id, response))
    return found


def assert_outcome(process, case: dict, debug_data, variables_data) -> str:
    ran = completed_ids(debug_data) & slack_ids(process)
    if not ran:
        raise CheckFailure("no Slack step completed in the run; the alert was not posted")
    posts = posted_messages(variables_data, ran)
    if not posts:
        raise CheckFailure(f"Slack step(s) {sorted(ran)} completed but returned no message ts")

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
    if channel != SLACK_CHANNEL:
        raise CheckFailure(f"the alert went to channel {channel!r}, expected {SLACK_CHANNEL!r} (#coding-agent-testing)")
    message = get_ci(response, "message")
    text = get_ci(message, "text") if isinstance(message, dict) else None
    missing = [t for t in (correlation, expected["severity"]) if not isinstance(text, str) or t not in text]
    if missing:
        raise CheckFailure(f"the posted alert does not carry {missing}: {text!r}")
    return get_ci(response, "ts")


def main() -> None:
    bpmn_path = locate_bpmn()
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
    debug_data, instance_id = run_debug(imported, case["inputs"], LIVE_RUN_DIR / "debug.log", timeout=480)
    evidence = debug_evidence(instance_id)
    require_clean_run(debug_data, evidence)
    ts = assert_outcome(process, case, debug_data, evidence.variables)
    print(f"OK: {case['name']}: Sev1 + engineering, correlationId kept, Slack alert posted (ts={ts})")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
