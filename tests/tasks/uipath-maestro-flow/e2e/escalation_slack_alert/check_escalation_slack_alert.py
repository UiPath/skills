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
from _shared.escalation_inputs import (  # noqa: E402
    SLACK_CHANNEL,
    SLACK_KEY,
    SLACK_SEND,
    check_same_outputs,
    feed_roles,
    is_slack_ts,
    load_flow,
)
from _shared.flow_check import (  # noqa: E402
    _fail_with_capture,
    _get_ci,
    _leaves,
    _op_matches,
    assert_flow_uses_connector_target,
    assert_slack_message_posted,
    completed_connector_node_ids,
    run_debug,
)
from _shared.slack_journal import journal_slack_posts  # noqa: E402

BULLET_RE = re.compile(r"^\s*(?:[-*•◦▪‣–·]|\d+[.)])\s*\S")
# The roles the graded results depend on. The others are fed when declared.
REQUIRED = ("tier", "productionDown", "workaround", "caseRef")


def feed(flow: dict, case: dict) -> dict:
    """The `--inputs` for one case, keyed by the inputs the agent declared."""
    return feed_roles(flow, case, case["inputs"], REQUIRED)


def posted_texts(payload: dict, ts: str) -> list[str]:
    """Every text in the response of the completed Slack send that returned `ts`."""
    globals_ = _get_ci(_get_ci(payload, "variables", "Variables") or {}, "globals", "Globals") or {}
    for node_id in completed_connector_node_ids(payload, SLACK_KEY, native_op_hint=SLACK_SEND):
        out = globals_.get(f"{node_id}.output")
        if isinstance(out, (dict, list)) and ts in {str(x).strip() for x in _leaves(out) if isinstance(x, str)}:
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
        "Slack message id": (is_slack_ts, "a Slack message ts"),
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
        with journal_slack_posts():
            payload = run_debug(inputs=feed(flow, case), timeout=300, retries=1)
        per_case.append(check_case(flow, payload, case))
        print(f"OK: {case['name']}: {case['expected']['severity']}, engineering needed "
              f"{case['expected']['engineering']}, case reference returned, Slack alert posted")
    check_same_outputs(per_case)
    print(f"OK: the same outputs hold the results in all {len(cases)} cases: "
          f"{ {r: sorted(set.intersection(*(set(h[r]) for h in per_case))) for r in per_case[0]} }")


if __name__ == "__main__":
    main()
