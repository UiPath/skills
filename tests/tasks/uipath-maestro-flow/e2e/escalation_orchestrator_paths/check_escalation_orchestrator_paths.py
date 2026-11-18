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
- the Slack effect: exactly one Slack send completed (the escalation alert or
  the triage notice, never both), and a returned Slack ts is the one that
  send got back, in #coding-agent-testing, with the case reference and the
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
from _shared.flow_check import (  # noqa: E402
    _fail_with_capture,
    assert_flow_uses_connector_target,
    assert_slack_message_posted,
    completed_connector_node_ids,
    find_flow_file,
    run_debug,
)

SLACK_KEY = "uipath-salesforce-slack"
SLACK_SEND = "send-message-to-channel"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
TS_RE = re.compile(r"^\d{9,11}\.\d{4,6}$")

# What each seeded value means, as fragments of a normalized input name.
KEYWORDS = {
    "senderEmail": ["senderemail", "fromemail", "emailaddress", "senderaddress", "fromaddress",
                    "^sender$", "^from$", "email"],
    "senderDomain": ["senderdomain", "emaildomain", "domain"],
    "subject": ["emailsubject", "subject", "title"],
    "body": ["emailbody", "body", "content", "message", "description", "text"],
    "tier": ["customertier", "tier", "plan", "segment", "level"],
    "productionDown": ["productiondown", "proddown", "outage", "production", "down"],
    "workaround": ["workaround"],
    "attachments": ["attachment"],
    "match": ["customermatch", "matchstatus", "matchcount", "matchresult", "matches", "matched", "match"],
    "duplicate": ["duplicate", "dup"],
    "caseRef": ["casereference", "correlationid", "caseref", "casekey", "caseid", "casenumber",
                "correlation", "reference", "case", "ref"],
}
# The roles the path and severity depend on. The others are fed when declared;
# the domain may be derived from the address instead (see REQUIRED_ANY).
REQUIRED = ("productionDown", "workaround", "match", "duplicate", "caseRef")
REQUIRED_ANY = (("senderDomain", "senderEmail"),)
# Field names a script may read off an object input where no `$vars` path shows.
FALLBACK_KEYS = {
    "senderEmail": ["senderEmail", "email", "from", "fromEmail", "sender"],
    "senderDomain": ["senderDomain", "domain"],
    "subject": ["subject", "emailSubject"],
    "body": ["body", "emailBody", "content"],
    "tier": ["customerTier", "tier"],
    "productionDown": ["productionDown", "isProductionDown", "prodDown"],
    "workaround": ["workaroundAvailable", "hasWorkaround", "workaround"],
    "attachments": ["hasAttachments"],
    "match": ["customerMatchStatus", "matchStatus", "customerMatch", "match"],
    "duplicate": ["isDuplicate", "duplicate"],
    "caseRef": ["caseReference", "caseRef", "caseId", "correlationId", "reference"],
}

# How a flow may spell each match state, normalized.
STATE_WORDS = {
    "one": {"single", "one", "matched", "match", "unique", "exact", "exactmatch", "found",
            "singlematch", "onematch", "exactlyone", "1"},
    "none": {"none", "nomatch", "nomatches", "notfound", "unmatched", "zero", "unknown",
             "nocustomer", "nomatchfound", "0"},
    "several": {"multiple", "several", "many", "ambiguous", "multi", "multiplematches",
                "morethanone", "2"},
}
DEFAULT_WORD = {"one": "single", "none": "none", "several": "multiple"}
# The five paths the prompt names, normalized.
PATH_WORDS = {"missingdomain", "unknowncustomer", "multiplematches", "duplicate", "escalation"}
COUNT = {"one": 1, "none": 0, "several": 2}
_Q = "[\"'`]"
_LIT = rf"{_Q}([^\"'`\n]{{1,40}}){_Q}"


def _stop(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def load_flow() -> dict:
    return json.loads(Path(find_flow_file()).read_text(encoding="utf-8"))


def _match_vars(flow: dict) -> list[dict]:
    return [v for v in io.declared(flow, "in")
            if re.search("|".join(KEYWORDS["match"]), io.normalize(v["id"]))]


def match_words(flow: dict) -> dict[str, str]:
    """The literal the flow compares the match input with, per state.

    Read from the flow's own code: comparisons of a match-named identifier
    (the input, an object field, or a local copied from it), or its membership
    in a list, first, then the
    input's description, then literals near those identifiers, then
    "single"/"none"/"multiple"."""
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
        for state, vocabulary in STATE_WORDS.items():
            if state not in words and io.normalize(literal) in vocabulary:
                words[state] = literal.strip()
    return {state: words.get(state, DEFAULT_WORD[state]) for state in STATE_WORDS}


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
    roles = {role: {"value": value, "keywords": KEYWORDS[role]} for role, value in values.items()}
    fallback = {key: values[role] for role, keys in FALLBACK_KEYS.items() for key in keys}
    inputs, _, unmapped = io.map_inputs(flow, roles, object_fallback=fallback, file_path=None)
    missing = [r for r in REQUIRED if r in unmapped]
    missing += ["/".join(group) for group in REQUIRED_ANY if all(r in unmapped for r in group)]
    error = io.unmapped_error(flow, missing)
    if error:
        _stop(f"{case['name']}: {error}")
    types = {v["id"]: str(v.get("type") or "").lower() for v in io.declared(flow, "in")}
    state = case["inputs"]["match"]
    for var in _match_vars(flow):
        if var["id"] not in inputs:
            continue
        if types[var["id"]] in ("number", "integer", "int"):
            inputs[var["id"]] = COUNT[state]
        elif types[var["id"]] in ("boolean", "bool"):
            inputs[var["id"]] = _boolean_match(var["id"], state)
    # A yes/no declared as text gets "true"/"false", not Python's "True".
    return {
        k: v.lower() if types.get(k) == "string" and v in ("True", "False") else v
        for k, v in inputs.items()
    }


def _is_ts(value) -> bool:
    return isinstance(value, str) and bool(TS_RE.match(value.strip()))


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
        "Slack message id": (_is_ts, "a Slack message ts"),
    }
    holders = {}
    for result, (predicate, shown) in expected.items():
        holders[result] = io.find_out(outs, predicate)
        if not holders[result]:
            values = {k: v for k, (_t, v) in outs.items()}
            _fail_with_capture(f"{case['name']}: no declared output is {shown} ({result}); outputs: {values}")
    fired = completed_connector_node_ids(payload, SLACK_KEY, native_op_hint=SLACK_SEND)
    if len(fired) > 1:
        _fail_with_capture(
            f"{case['name']}: {len(fired)} Slack sends completed ({sorted(fired)}); "
            "a case gets the escalation alert or the triage notice, not both"
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


def check_same_outputs(per_case: list[dict[str, list[str]]]) -> None:
    """One output carries each result in every case, not a constant that fit some."""
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
    words = match_words(flow)
    print(f"OK: the flow spells the customer-match states as {words}")
    per_case = []
    for case in cases:
        # retries=1: every case posts to a shared channel, so a whole-flow retry
        # would post a duplicate; seven serial cases also need a bounded budget.
        payload = run_debug(inputs=feed(flow, case, words), timeout=300, retries=1)
        per_case.append(check_case(flow, payload, case))
        print(f"OK: {case['name']}: path={case['expected']['path']}, "
              f"severity={case['expected']['severity']}, one Slack message posted")
    check_same_outputs(per_case)
    print(f"OK: the same outputs hold the results in all {len(cases)} cases")


if __name__ == "__main__":
    main()
