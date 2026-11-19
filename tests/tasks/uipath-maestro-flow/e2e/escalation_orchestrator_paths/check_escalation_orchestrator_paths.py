#!/usr/bin/env python3
"""Run each seeded path case and check what the run did.

The prompt names no variables, so the seeded values are mapped onto the
inputs the agent declared by meaning (`_shared/flow_io_roles.py`), and the
results are found among the declared outputs by value. The customer-match
input is fed in the vocabulary the flow itself compares against ("none",
"multiple", ...), or as a count when the agent declared a number.

For every case in seed.json the grader runs `flow debug --inputs` once and
asserts:

- declared outputs hold the path, the severity, whether engineering is
  needed, the response mode and the case reference unchanged;
- the Slack effect: exactly one Slack message was posted (the escalation
  alert or the triage notice, never both, and no send run twice), and a
  returned Slack ts is the one that send got back, in #coding-agent-testing, with the case reference and the
  path in the message.

After all cases, the same output must hold each result in every case, so a
constant that happens to match some cases does not count.

Any layout passes: one Script or several, a Decision or a Switch, one Slack
node or two, one End or two. "If Slack fails, the automation should still
finish" is not exercised: failing the shared Slack connection is not safe.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Walk up to the directory that holds `_shared` so the import resolves.
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
    input_types,
    is_match_input,
    is_slack_ts,
    load_flow,
)
from _shared.flow_check import (  # noqa: E402
    _fail_with_capture,
    _get_ci,
    assert_flow_uses_connector_target,
    assert_slack_message_posted,
    completed_connector_node_ids,
    node_output_leaves,
    run_debug,
)
from _shared.slack_journal import journal_slack_posts  # noqa: E402


# The roles the path and severity depend on. The others are fed when declared;
# the domain may be derived from the address instead (see REQUIRED_ANY).
REQUIRED = ("productionDown", "workaround", "match", "duplicate", "caseRef")
REQUIRED_ANY = (("senderDomain", "senderEmail"),)

# Words a flow may spell each match state with, checked in this order, since
# "no_match" holds "match" too. A literal's words are compared, so
# "NO_CUSTOMER_FOUND", "exactly_one" and "MORE_THAN_ONE" are understood.
STATE_WORDS = (
    ("none", ["none", "no", "not", "zero", "unknown", "unmatched", "nomatch", "nomatches", "notfound",
              "nocustomer", "nomatchfound", "missing", "0"]),
    ("several", ["multiple", "several", "many", "ambiguous", "multi", "multiplematches", "morethanone",
                 "2"]),
    ("one", ["single", "one", "matched", "match", "unique", "exact", "exactmatch", "found",
             "singlematch", "onematch", "exactlyone", "1"]),
)
# The prompt's own words, when the flow's code names no word for a state.
DEFAULT_WORD = {"one": "one", "none": "none", "several": "several"}
# The five paths the prompt names, normalized.
PATH_WORDS = {"missingdomain", "unknowncustomer", "multiplematches", "duplicate", "escalation"}
COUNT = {"one": 1, "none": 0, "several": 2}
_Q = "[\"'`]"
_LIT = rf"{_Q}([^\"'`\n]{{1,40}}){_Q}"


def _match_vars(flow: dict) -> list[dict]:
    return [v for v in io.declared(flow, "in") if is_match_input(v["id"])]


def state_of(literal: str) -> str | None:
    """The match state a literal means, by its words."""
    # Whole words only: "phone" or "notification" must not read as one or none.
    return next((state for state, words in STATE_WORDS
                 if io.means([literal.strip()], words, substring=False)), None)


def match_words(flow: dict) -> dict[str, str]:
    """The literal the flow compares the match input with, per state.

    The words a text input expects exist only in the flow's code, so they are
    read from it: comparisons of the input that means the match (by
    `flow_io_roles`), an object field or a local copied from it, or its
    membership in a list, first, then the input's description, then literals
    near those identifiers. Each literal is classed by what its words mean
    (`state_of`). A state no literal names gets the prompt's own word."""
    code = "\n".join(io.texts(flow.get("nodes") or []))
    idents = {v["id"] for v in _match_vars(flow)}
    # Identifiers that hold the match status; `.match(` is a string method, not one.
    idents |= {
        t for t in re.findall(r"(?<![\w$])([A-Za-z_$][\w$]*)(?![\w$])(?!\s*\()", code)
        if "match" in t.lower()
    }
    for alias, rhs in re.findall(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*([^;\n]*)", code):
        if any(re.search(rf"(?<![\w$]){re.escape(i)}(?![\w$])", rhs) for i in idents):
            idents.add(alias)
    compared, near = [], []
    # Sorted: a set's order changes with the hash seed, and so would the pick.
    for ident in sorted(idents):
        e = rf"(?<![\w$]){re.escape(ident)}(?![\w$])"
        compared += re.findall(rf"{e}(?:\s*\.\s*\w+\(\s*\))*\s*[!=]==?\s*{_LIT}", code)
        compared += re.findall(rf"{_LIT}\s*[!=]==?\s*{e}", code)
        # Membership: `["several", "multiple"].indexOf(match)` or `.includes(match)`.
        for listed in re.findall(rf"\[([^\[\]]{{1,300}})\]\s*\.\s*(?:indexOf|includes)\(\s*{e}", code):
            compared += re.findall(_LIT, listed)
        for m in re.finditer(e, code):
            near += re.findall(_LIT, code[max(0, m.start() - 200): m.end() + 400])
    # A path the prompt names ("multiple_matches") is an output set near the
    # match check, so it is the last guess for how the input is spelled.
    near.sort(key=lambda literal: io.normalize(literal) in PATH_WORDS)
    described = [w for v in _match_vars(flow) for w in re.findall(r"[\w-]+", str(v.get("description") or ""))]
    words: dict[str, str] = {}
    for literal in [*compared, *described, *near]:
        state = state_of(literal)
        if state and state not in words:
            words[state] = literal.strip()
    return {state: words.get(state, DEFAULT_WORD[state]) for state in DEFAULT_WORD}


def _boolean_match(var_id: str, state: str) -> bool:
    name = io.normalize(var_id)
    if re.search("multiple|several|many|ambiguous", name):
        return state == "several"
    if re.search("none|nomatch|unknown|notfound|unmatched", name):
        return state == "none"
    return state != "none"


def feed(flow: dict, case: dict, words: dict[str, str]) -> dict:
    """The `--inputs` for one case, keyed by the inputs the agent declared."""
    values = {**case["inputs"], "match": words[case["inputs"]["match"]]}
    inputs = feed_roles(flow, case, values, REQUIRED, REQUIRED_ANY)
    types = input_types(flow)
    state = case["inputs"]["match"]
    for var in _match_vars(flow):
        if var["id"] not in inputs:
            continue
        if types[var["id"]] in ("number", "integer", "int"):
            inputs[var["id"]] = COUNT[state]
        elif types[var["id"]] in ("boolean", "bool"):
            inputs[var["id"]] = _boolean_match(var["id"], state)
    return inputs


def slack_messages(payload: dict, sends: set[str]) -> int:
    """How many Slack messages the completed sends posted: their completed
    executions (a send in a loop runs more than once) or the distinct ts
    values in their responses, whichever is more."""
    runs = [e for e in _get_ci(payload, "elementExecutions", "Elements", "elements") or []
            if _get_ci(e, "elementId", "ElementId", "nodeId", "NodeId") in sends
            and str(_get_ci(e, "status", "Status")).lower() == "completed"]
    ts = {str(x).strip() for x in node_output_leaves(payload, sends) if is_slack_ts(x)}
    return max(len(runs), len(ts))


def _any_text(options: list[str]):
    return lambda v: any(io.equals_text(o)(v) for o in options)


def check_case(flow: dict, payload: dict, case: dict) -> dict[str, list[str]]:
    """Assert one case's results and its single Slack message. Returns, per
    result, the declared outputs that hold it."""
    want = case["expected"]
    ref = case["inputs"]["caseRef"]
    modes = [want["responseMode"]] if isinstance(want["responseMode"], str) else want["responseMode"]
    outs = io.out_values(flow, payload)
    expected = {
        "path": (io.equals_text(want["path"]), repr(want["path"])),
        "severity": (io.equals_text(want["severity"]), repr(want["severity"])),
        "engineering needed": (io.equals_bool(want["engineering"]), str(want["engineering"]).lower()),
        "response mode": (_any_text(modes), " or ".join(map(repr, modes))),
        "case reference": (io.equals_exact(ref), repr(ref)),
        "Slack message id": (is_slack_ts, "a Slack message ts"),
    }
    holders = {}
    for result, (predicate, shown) in expected.items():
        holders[result] = io.find_out(outs, predicate)
        if not holders[result]:
            values = {k: v for k, (_t, v) in outs.items()}
            _fail_with_capture(f"{case['name']}: no declared output is {shown} ({result}); outputs: {values}")
    fired = completed_connector_node_ids(payload, SLACK_KEY, native_op_hint=SLACK_SEND)
    if (posted := slack_messages(payload, fired)) > 1:
        _fail_with_capture(
            f"{case['name']}: {posted} Slack messages posted by {sorted(fired)}; "
            "a case gets one message, the escalation alert or the triage notice"
        )
    # The case reference is opaque and must appear verbatim. The path is matched
    # ignoring case and separators, so "Unknown customer" counts.
    assert_slack_message_posted(
        payload,
        holders["Slack message id"][0],
        expected_channel=SLACK_CHANNEL,
        must_contain=ref,
        must_contain_loose=[want["path"]],
        send_op=SLACK_SEND,
    )
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
    words = match_words(flow)
    print(f"OK: the flow spells the customer-match states as {words}")
    per_case = []
    for case in cases:
        # retries=1: every case posts to a shared channel, so a whole-flow retry
        # would post a duplicate; seven serial cases also need a bounded budget.
        with journal_slack_posts():
            payload = run_debug(inputs=feed(flow, case, words), timeout=300, retries=1)
        per_case.append(check_case(flow, payload, case))
        print(f"OK: {case['name']}: path={case['expected']['path']}, "
              f"severity={case['expected']['severity']}, one Slack message posted")
    check_same_outputs(per_case)
    print(f"OK: the same outputs hold the results in all {len(cases)} cases")


if __name__ == "__main__":
    main()
