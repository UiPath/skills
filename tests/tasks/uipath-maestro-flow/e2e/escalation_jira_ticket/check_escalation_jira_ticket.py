#!/usr/bin/env python3
"""Run each seeded escalation and prove the flow opened a real Jira ticket for it.

The prompt names no variables, so the seeded values are mapped onto the
inputs the agent declared by meaning (`_shared/flow_io_roles.py`), and the
results are found among the declared outputs by value. For every case in
seed.json the grader runs `flow debug --inputs` once (it creates a real
issue) and asserts:

1. A Jira Create Issue step completed and returned a CE-<n> key.
2. A declared output holds that key, and others hold the severity
   ("Sev1"/"Sev2"/"Sev3"), whether engineering is needed (true/false) and the
   case reference unchanged.
3. TENANT: reading the key back from Jira returns an issue whose title starts
   with "[TEST]", followed by the severity, the case reference and the email
   subject in that order, whose type is Task, and whose description holds
   the email body.

The duplicate case must get its own ticket too. After all cases, the same
output must hold each result in every case.

No node id, node type, layout or variable name is pinned. A key a Jira step
returned is written to `.created_keys`, so post_run teardown deletes it even
when a later assertion fails, only when its read-back title carries this
case's reference: a step that searches CE returns other runs' tickets. A key
whose read keeps failing is not journaled (its owner is unknown) and ends the
check as a grader error.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
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
from _shared import jira_is  # noqa: E402
from _shared.escalation_inputs import (  # noqa: E402
    check_same_outputs,
    feed_roles,
    input_types,
    is_match_input,
    load_flow,
)
from _shared.flow_check import (  # noqa: E402
    _fail_with_capture,
    assert_flow_uses_connector_target,
    completed_connector_node_ids,
    get_debug_attempt_raws,
    get_last_debug_raw,
    node_output_leaves,
    run_debug,
)

JIRA_KEY = "uipath-atlassian-jira"
JIRA_CREATE_OP = "create-issue"  # matched by op, so a connector-proxy Create also counts
CREATED_KEYS = Path(".created_keys")
READ_ATTEMPTS = 2

# The roles the ticket and the results depend on. The others are fed when declared.
REQUIRED = ("subject", "body", "tier", "productionDown", "workaround", "caseRef")


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _grader_error(msg: str) -> None:
    sys.stderr.write(f"GRADER ERROR: {msg}\n")
    sys.exit(io.GRADER_ERROR_EXIT)


def _note_unread(unread: list[str]) -> None:
    if unread:
        print(f"NOTE: could not read back {unread} from Jira; ownership unknown, not journaled for teardown")


def feed(flow: dict, case: dict) -> dict:
    """The `--inputs` for one case, keyed by the inputs the agent declared."""
    inputs = feed_roles(flow, case, case["inputs"], REQUIRED)
    types = input_types(flow)
    for k in inputs:
        if is_match_input(k) and types.get(k) in ("number", "integer", "int"):
            inputs[k] = 1  # the sender matched one customer, as a count
        elif is_match_input(k) and types.get(k) in ("boolean", "bool"):
            inputs[k] = True  # the sender matched a customer
    return inputs


def _record(keys) -> None:
    """Add keys a Create step returned to `.created_keys` for teardown."""
    known = CREATED_KEYS.read_text().split() if CREATED_KEYS.is_file() else []
    CREATED_KEYS.write_text("\n".join(dict.fromkeys([*known, *keys])) + "\n")


def _record_partial(exc: BaseException, conn: str, ref: str, project: str) -> list[str]:
    """After a failed debug, record for teardown any key in the partial output
    whose Jira title carries this case's reference. Best effort: never masks
    the failure."""
    partial = get_last_debug_raw() or ""
    if isinstance(exc, subprocess.TimeoutExpired):
        partial += "".join(
            s.decode() if isinstance(s, bytes) else (s or "") for s in (exc.stdout, exc.stderr)
        )
    owned, unread = _owned(conn, re.findall(rf"\b{re.escape(project)}-\d+\b", partial), ref)
    _note_unread(unread)
    if owned:
        _record(owned)
    return list(owned)


def _record_attempts(conn: str, ref: str, project: str) -> None:
    """Record this run's tickets from every debug attempt, not only the last:
    a re-run attempt may have created a ticket `check_case` never sees."""
    raw = "\n".join(get_debug_attempt_raws())
    owned, unread = _owned(conn, re.findall(rf"\b{re.escape(project)}-\d+\b", raw), ref)
    _note_unread(unread)
    if owned:
        _record(owned)


def _read(conn: str, key: str) -> dict | None:
    """The issue's fields, None when Jira confirms it does not exist. Raises
    RuntimeError when the read keeps failing."""
    for _ in range(READ_ATTEMPTS):
        try:
            fields = jira_is.get_issue(conn, key)
        except (RuntimeError, subprocess.SubprocessError):
            continue
        if fields is not None:
            return fields
        if jira_is.issue_absent(conn, key):
            return None
    raise RuntimeError(f"the Jira read of {key} failed {READ_ATTEMPTS} times")


def _owned(conn: str, keys, ref: str) -> tuple[dict[str, dict], list[str]]:
    """The keys whose Jira title carries `ref`, with the fields read back, and
    the keys whose read failed."""
    owned: dict[str, dict] = {}
    unread: list[str] = []
    for key in dict.fromkeys(keys):
        try:
            fields = _read(conn, key)
        except RuntimeError:
            unread.append(key)
            continue
        if fields is not None and ref in str(fields.get("summary", "")):
            owned[key] = fields
    return owned, unread


def _plain(value) -> str:
    """The text of a Jira description: a string, or an Atlassian Document."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(_plain(v) for v in value)
    if isinstance(value, dict):
        own = value["text"] if isinstance(value.get("text"), str) else ""
        return own + _plain(value.get("content") or []) + " "
    return ""


def _squash(text: str) -> str:
    return " ".join(text.split())


def check_ticket(fields: dict, case: dict, key: str, severity: str) -> None:
    """Title: "[TEST]", then the severity, the case reference and the subject.
    Description: the email body."""
    ref, subject, body = (case["inputs"][k] for k in ("caseRef", "subject", "body"))
    summary = str(fields.get("summary") or "")
    if not summary.startswith("[TEST]"):
        _fail(f"{key}: the ticket title {summary!r} does not start with '[TEST]'")
    rest = summary[len("[TEST]"):]
    found = {"severity": rest.lower().find(severity.lower()), "case reference": rest.find(ref),
             "email subject": rest.find(subject)}
    missing = [part for part, at in found.items() if at < 0]
    if missing:
        _fail(f"{key}: the ticket title {summary!r} lacks the {', '.join(missing)} "
              f"(expected {severity!r}, {ref!r}, {subject!r})")
    if not found["severity"] < found["case reference"] < found["email subject"]:
        _fail(f"{key}: the ticket title {summary!r} does not give the severity, the case "
              "reference and the email subject in that order")
    issuetype = str((fields.get("issuetype") or {}).get("name") or "")
    if issuetype.casefold() != jira_is.ISSUETYPE_NAME.casefold():
        _fail(f"{key}: the ticket is not a {jira_is.ISSUETYPE_NAME} (issue type {issuetype!r})")
    if _squash(body) not in _squash(_plain(fields.get("description"))):
        _fail(f"{key}: the ticket description does not hold the email body {body!r}")
    print(f"OK: {key} reads back as {summary!r}, with the email body as its description")


def check_case(flow: dict, payload: dict, case: dict, conn: str, project: str) -> dict[str, list[str]]:
    """Assert one case's ticket and results. Returns, per result, the declared
    outputs that hold it."""
    want = case["expected"]
    ref = case["inputs"]["caseRef"]
    # A ticket can be created by the curated Create Issue op or by the generic
    # `insert-record` on the issue object. Any Jira step that ran counts; the
    # proof is a CE key it returned whose ticket reads back with this case's ref.
    create_nodes = completed_connector_node_ids(payload, JIRA_KEY, native_op_hint=JIRA_CREATE_OP) or (
        completed_connector_node_ids(payload, JIRA_KEY)
    )
    if not create_nodes:
        _fail_with_capture(f"{case['name']}: no Jira step completed in the debug run")
    returned = sorted(k for k in node_output_leaves(payload, create_nodes) if re.fullmatch(rf"{project}-\d+", k))
    if not returned:
        _fail_with_capture(f"{case['name']}: the Create Issue step that ran returned no {project}-<n> key")
    owned, unread = _owned(conn, returned, ref)
    if not owned and unread:
        _grader_error(f"{case['name']}: could not read back {unread} from Jira, so their ownership is unknown "
                      "and nothing was journaled for teardown")
    if not owned:
        _fail(f"{case['name']}: no {project} key the Jira steps returned ({returned}) reads back as a "
              f"ticket whose title carries the case reference {ref!r}")
    _note_unread(unread)
    created = sorted(owned)
    _record(created)

    outs = io.out_values(flow, payload)
    expected = {
        "ticket key": (lambda v: isinstance(v, str) and v.strip() in created, f"the created key {created}"),
        "severity": (io.equals_text(want["severity"]), repr(want["severity"])),
        "engineering needed": (io.equals_bool(want["engineering"]), str(want["engineering"]).lower()),
        "case reference": (io.equals_exact(ref), repr(ref)),
    }
    holders = {}
    for result, (predicate, shown) in expected.items():
        holders[result] = io.find_out(outs, predicate)
        if not holders[result]:
            values = {k: v for k, (_t, v) in outs.items()}
            _fail_with_capture(f"{case['name']}: no declared output is {shown} ({result}); outputs: {values}")

    key = str(outs[holders["ticket key"][0]][1]).strip()
    check_ticket(owned[key], case, key, want["severity"])
    return holders


def main() -> None:
    seed = json.loads(Path("seed.json").read_text())
    project = seed["project_key"]
    assert_flow_uses_connector_target(JIRA_KEY)
    print(f"OK: flow reaches {JIRA_KEY}")
    flow = load_flow()
    conn = jira_is.connection_id()

    per_case = []
    for case in seed["cases"]:
        ref = case["inputs"]["caseRef"]
        # One attempt only: the flow creates a ticket, so a whole-flow retry
        # would create a duplicate this checker never sees or cleans up.
        try:
            payload = run_debug(inputs=feed(flow, case), timeout=480, retries=1)
        except (subprocess.TimeoutExpired, SystemExit) as exc:
            owned = _record_partial(exc, conn, ref, project)
            if isinstance(exc, SystemExit):
                raise
            _fail(
                f"{case['name']}: flow debug timed out after {exc.timeout}s"
                + (f"; recorded this run's key(s) {owned} for teardown" if owned else "")
            )
        _record_attempts(conn, ref, project)
        per_case.append(check_case(flow, payload, case, conn, project))
        print(f"OK: {case['name']}: {case['expected']['severity']}, engineering needed "
              f"{case['expected']['engineering']}, ticket opened and read back")
    check_same_outputs(per_case)
    print("PASS: every seeded escalation, the duplicate included, opened its own Jira ticket "
          "with the expected results")


if __name__ == "__main__":
    main()
