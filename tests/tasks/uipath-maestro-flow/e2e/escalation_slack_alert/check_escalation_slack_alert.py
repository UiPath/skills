#!/usr/bin/env python3
"""Run each seeded escalation case and check what the run did.

The prompt names no variables, so the seeded values are mapped onto the
inputs the agent declared by meaning (`_shared/flow_io_roles.py`), and the
results are found among the declared outputs by value. For every case in
seed.json the grader runs `flow debug --inputs` once and asserts:

- a declared output holds the severity ("Sev1"/"Sev2"/"Sev3"), one holds
  whether engineering is needed (true/false), one holds the case reference
  unchanged, and one holds a Slack message ts;
- the Slack effect: that ts was returned by a Slack send that completed in
  this run, in #coding-agent-testing, and the posted message's first line
  carries the severity and the case reference, followed by two or three
  bulleted next steps.

After all cases, the same output must hold each result in every case, so a
constant that happens to match one case does not count.

No node id, node type, layout or variable name is pinned.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Walk up to the directory that holds `_shared` so the import works regardless
# of how deep this task lives under tests/tasks/uipath-maestro-flow/.
_directory = os.path.dirname(os.path.abspath(__file__))
while _directory != os.path.dirname(_directory) and not os.path.isdir(
    os.path.join(_directory, "_shared")
):
    _directory = os.path.dirname(_directory)
sys.path.insert(0, _directory)

from _shared import flow_io_roles as io  # noqa: E402
from _shared.flow_check import (  # noqa: E402
    _fail_with_capture,
    _leaves,
    _op_matches,
    assert_flow_uses_connector_target,
    assert_slack_message_posted,
    find_flow_file,
    run_debug,
)

SLACK_KEY = "uipath-salesforce-slack"
SLACK_SEND = "send-message-to-channel"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
TS_RE = re.compile(r"^\d{9,11}\.\d{4,6}$")
BULLET_RE = re.compile(r"^\s*(?:[-*•◦▪‣–·]|\d+[.)])\s*\S")

# What each seeded value means, as fragments of a normalized input name.
KEYWORDS = {
    "senderEmail": ["senderemail", "fromemail", "emailaddress", "senderaddress", "fromaddress",
                    "^sender$", "^from$", "email"],
    "subject": ["emailsubject", "subject", "title"],
    "body": ["emailbody", "body", "content", "message", "description", "text"],
    "tier": ["customertier", "tier", "plan", "segment", "level"],
    "productionDown": ["productiondown", "proddown", "outage", "production", "down"],
    "workaround": ["workaround"],
    "caseRef": ["casereference", "correlationid", "caseref", "casekey", "caseid", "casenumber",
                "correlation", "reference", "case", "ref"],
}
# The roles the graded results depend on. The others are fed when declared.
REQUIRED = ("tier", "productionDown", "workaround", "caseRef")
# Field names a script may read off an object input where no `$vars` path shows.
FALLBACK_KEYS = {
    "senderEmail": ["senderEmail", "email", "from", "fromEmail", "sender"],
    "subject": ["subject", "emailSubject"],
    "body": ["body", "emailBody", "content"],
    "tier": ["customerTier", "tier"],
    "productionDown": ["productionDown", "isProductionDown", "prodDown"],
    "workaround": ["workaroundAvailable", "hasWorkaround", "workaround"],
    "caseRef": ["caseReference", "caseRef", "caseId", "correlationId", "reference"],
}


def _stop(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def load_flow() -> dict:
    return json.loads(Path(find_flow_file()).read_text(encoding="utf-8"))


def feed(flow: dict, case: dict) -> dict:
    """The `--inputs` for one case, keyed by the inputs the agent declared."""
    values = case["inputs"]
    roles = {role: {"value": value, "keywords": KEYWORDS[role]} for role, value in values.items()}
    fallback = {key: values[role] for role, keys in FALLBACK_KEYS.items() for key in keys}
    inputs, _, unmapped = io.map_inputs(flow, roles, object_fallback=fallback, file_path=None)
    error = io.unmapped_error(flow, [r for r in REQUIRED if r in unmapped])
    if error:
        _stop(f"{case['name']}: {error}")
    types = {v["id"]: str(v.get("type") or "").lower() for v in io.declared(flow, "in")}
    # A yes/no declared as text gets "true"/"false", not Python's "True".
    return {
        k: v.lower() if types.get(k) == "string" and v in ("True", "False") else v
        for k, v in inputs.items()
    }


def _is_ts(value) -> bool:
    return isinstance(value, str) and bool(TS_RE.match(value.strip()))


def posted_texts(payload: dict, ts: str) -> list[str]:
    """Every text in the response of the Slack send that returned `ts`."""
    globals_ = (payload.get("variables") or {}).get("globals") or {}
    for key, out in globals_.items():
        if str(key).endswith(".output") and isinstance(out, (dict, list)):
            if ts in {str(x).strip() for x in _leaves(out) if isinstance(x, str)}:
                return io.texts(out)
    return []


def check_alert_layout(payload: dict, ts: str, ref: str, severity: str) -> None:
    """First line: the severity and the case reference. Then 2-3 bulleted next steps."""
    starts = [
        lines for text in posted_texts(payload, ts)
        for lines in [[line for line in text.splitlines() if line.strip()]]
        if lines and ref in lines[0]
    ]
    if not starts:
        _fail_with_capture(f"the posted Slack message does not start with a line carrying the case reference {ref!r}")
    starts = [lines for lines in starts if _op_matches(severity, lines[0])]
    if not starts:
        _fail_with_capture(f"the posted Slack message's first line does not carry the severity {severity!r}")
    counts = [sum(1 for line in lines[1:] if BULLET_RE.match(line)) for lines in starts]
    if not any(2 <= n <= 3 for n in counts):
        _fail_with_capture(
            f"the posted Slack message does not list two or three next steps as bullets "
            f"after its first line (bulleted lines found: {counts})"
        )


def check_case(flow: dict, payload: dict, case: dict) -> dict[str, list[str]]:
    """Assert one case's results and Slack alert. Returns, per result, the
    declared outputs that hold it."""
    want = case["expected"]
    ref = case["inputs"]["caseRef"]
    outs = io.out_values(flow, payload)
    expected = {
        "severity": (io.equals_text(want["severity"]), repr(want["severity"])),
        "engineering needed": (io.equals_bool(want["engineering"]), str(want["engineering"]).lower()),
        "case reference": (io.equals_exact(ref), repr(ref)),
        "Slack message id": (_is_ts, "a Slack message ts"),
    }
    holders = {}
    for result, (predicate, shown) in expected.items():
        holders[result] = io.find_out(outs, predicate)
        if not holders[result]:
            values = {k: v for k, (_t, v) in outs.items()}
            _fail_with_capture(f"{case['name']}: no declared output is {shown} ({result}); outputs: {values}")
    ts = assert_slack_message_posted(
        payload,
        holders["Slack message id"][0],
        expected_channel=SLACK_CHANNEL,
        must_contain=ref,
        must_contain_loose=[want["severity"]],
        send_op=SLACK_SEND,
    )
    check_alert_layout(payload, ts, ref, want["severity"])
    return holders


def check_same_outputs(per_case: list[dict[str, list[str]]]) -> None:
    """One output carries each result in every case, not a constant that fit once."""
    for result in per_case[0]:
        if not set.intersection(*(set(h[result]) for h in per_case)):
            _stop(
                f"no single output holds the {result} in every case "
                f"(outputs per case: {[h[result] for h in per_case]})"
            )


def main() -> None:
    # Slack must be reached through the real connector (or a connector-auth
    # HTTP proxy), not a hand-rolled unauthenticated call.
    assert_flow_uses_connector_target(SLACK_KEY)

    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    cases = json.loads(seed_path.read_text(encoding="utf-8")).get("cases")
    if not isinstance(cases, list) or not cases:
        raise SystemExit("FAIL: seed.json must contain at least one case")

    flow = load_flow()
    per_case = []
    for case in cases:
        # retries=1: the flow posts to a shared channel, so a whole-flow retry
        # would post a duplicate alert.
        payload = run_debug(inputs=feed(flow, case), timeout=300, retries=1)
        per_case.append(check_case(flow, payload, case))
        print(f"OK: {case['name']}: {case['expected']['severity']}, engineering needed "
              f"{case['expected']['engineering']}, case reference returned, Slack alert posted")
    check_same_outputs(per_case)
    print(f"OK: the same outputs hold the results in all {len(cases)} cases: "
          f"{ {r: sorted(set.intersection(*(set(h[r]) for h in per_case))) for r in per_case[0]} }")


if __name__ == "__main__":
    main()
