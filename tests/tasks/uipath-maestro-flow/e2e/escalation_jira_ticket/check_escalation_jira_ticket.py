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
   subject in that order, and whose description holds the email body.

The duplicate case must get its own ticket too. After all cases, the same
output must hold each result in every case.

No node id, node type, layout or variable name is pinned. Every key a Create
step returned is written to `.created_keys` so post_run teardown deletes it
even when a later assertion fails.
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
from _shared.flow_check import (  # noqa: E402
    _fail_with_capture,
    assert_flow_uses_connector_target,
    completed_connector_node_ids,
    find_flow_file,
    get_last_debug_raw,
    node_output_leaves,
    run_debug,
)

JIRA_KEY = "uipath-atlassian-jira"
JIRA_CREATE_OP = "create-issue"  # matched by op, so a connector-proxy Create also counts
CREATED_KEYS = Path(".created_keys")

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
    "match": ["customermatch", "matchstatus", "matchtype", "matchcount", "matchresult", "matches",
              "matched", "match"],
    "duplicate": ["duplicate", "dup"],
    "caseRef": ["casereference", "correlationid", "caseref", "casekey", "caseid", "casenumber",
                "correlation", "reference", "case", "ref"],
}
# The roles the ticket and the results depend on. The others are fed when declared.
REQUIRED = ("subject", "body", "tier", "productionDown", "workaround", "caseRef")
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
    "match": ["customerMatchStatus", "matchStatus", "customerMatch"],
    "duplicate": ["isDuplicate", "duplicate"],
    "caseRef": ["caseReference", "caseRef", "caseId", "correlationId", "reference"],
}


def _fail(msg: str) -> None:
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
        _fail(f"{case['name']}: {error}")
    types = {v["id"]: str(v.get("type") or "").lower() for v in io.declared(flow, "in")}
    fixed = {}
    for k, v in inputs.items():
        is_match = bool(re.search("|".join(KEYWORDS["match"]), io.normalize(k)))
        if is_match and types.get(k) in ("number", "integer", "int"):
            v = 1  # the sender matched one customer, as a count
        elif is_match and types.get(k) in ("boolean", "bool"):
            v = True  # the sender matched a customer
        elif types.get(k) == "string" and v in ("True", "False"):
            v = v.lower()  # a yes/no declared as text
        fixed[k] = v
    return fixed


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
    owned: list[str] = []
    for key in dict.fromkeys(re.findall(rf"\b{re.escape(project)}-\d+\b", partial)):
        try:
            fields = jira_is.get_issue(conn, key)
        except Exception:  # noqa: BLE001
            continue
        if fields is not None and ref in str(fields.get("summary", "")):
            owned.append(key)
    if owned:
        _record(owned)
    return owned


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
    if "description" not in fields:
        print(f"NOTE: the Jira read of {key} returned no description field; the description was not checked")
    elif _squash(body) not in _squash(_plain(fields.get("description"))):
        _fail(f"{key}: the ticket description does not hold the email body {body!r}")
    print(f"OK: {key} reads back as {summary!r}, with the email body as its description")


def check_case(flow: dict, payload: dict, case: dict, conn: str, project: str) -> dict[str, list[str]]:
    """Assert one case's ticket and results. Returns, per result, the declared
    outputs that hold it."""
    want = case["expected"]
    ref = case["inputs"]["caseRef"]
    create_nodes = completed_connector_node_ids(payload, JIRA_KEY, native_op_hint=JIRA_CREATE_OP)
    if not create_nodes:
        _fail_with_capture(f"{case['name']}: no Jira Create Issue step completed in the debug run")
    created = sorted(k for k in node_output_leaves(payload, create_nodes) if re.fullmatch(rf"{project}-\d+", k))
    if not created:
        _fail_with_capture(f"{case['name']}: the Create Issue step that ran returned no {project}-<n> key")
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
    fields = jira_is.get_issue(conn, key)
    if fields is None:
        _fail(f"{case['name']}: reading {key} back from Jira found no issue")
    check_ticket(fields, case, key, want["severity"])
    return holders


def check_same_outputs(per_case: list[dict[str, list[str]]]) -> None:
    """One output carries each result in every case, not a constant that fit once."""
    for result in per_case[0]:
        if not set.intersection(*(set(h[result]) for h in per_case)):
            _fail(
                f"no single output holds the {result} in every case "
                f"(outputs per case: {[h[result] for h in per_case]})"
            )


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
        per_case.append(check_case(flow, payload, case, conn, project))
        print(f"OK: {case['name']}: {case['expected']['severity']}, engineering needed "
              f"{case['expected']['engineering']}, ticket opened and read back")
    check_same_outputs(per_case)
    print(f"PASS: every seeded escalation, the duplicate included, opened its own Jira ticket "
          f"with the expected results")


if __name__ == "__main__":
    main()
