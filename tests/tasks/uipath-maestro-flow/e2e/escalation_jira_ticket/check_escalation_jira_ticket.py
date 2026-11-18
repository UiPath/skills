#!/usr/bin/env python3
"""Run the seeded Sev1 escalation and prove the flow created a real Jira ticket.

1. The flow reaches the uipath-atlassian-jira connector (native node or a
   connector-auth HTTP proxy).
2. LIVE: one `flow debug` on the seeded case, which creates a real issue.
3. A Jira Create Issue step completed in that run, and the issue key it
   returned is the flow's jiraIssueKey output.
4. TENANT: reading that key back from Jira returns an issue whose summary
   carries the seeded correlationId, so the flow created THIS run's ticket.
5. The named outputs severity, engineeringNeeded and caseKey are right.

No node id, Script node or variable the prompt does not name is pinned.
Every key proven to be this run's is written to `.created_keys` so post_run
teardown can delete it even when a later assertion fails.
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

from _shared import jira_is  # noqa: E402
from _shared.flow_check import (  # noqa: E402
    assert_flow_uses_connector_target,
    assert_named_equals,
    collect_outputs,
    completed_connector_node_ids,
    get_last_debug_raw,
    node_output_leaves,
    run_debug,
)

JIRA_KEY = "uipath-atlassian-jira"
JIRA_CREATE_OP = "create-issue"  # matched by op, so a connector-proxy Create also counts
ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
CASE_SENSITIVE = {"caseKey"}  # opaque id: exact-case match
CREATED_KEYS = Path(".created_keys")


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _owned(conn: str, keys: list[str], correlation: str) -> list[str]:
    """The keys whose Jira summary carries this run's correlationId."""
    return [
        k for k in keys
        for fields in [jira_is.get_issue(conn, k)]
        if fields is not None and correlation in str(fields.get("summary", ""))
    ]


def _record_partial(exc: BaseException, correlation: str, project: str) -> list[str]:
    """After a failed debug, record for teardown any key in the partial output
    that Jira confirms belongs to this run. Best effort: never masks the failure."""
    partial = get_last_debug_raw() or ""
    if isinstance(exc, subprocess.TimeoutExpired):
        partial += "".join(
            s.decode() if isinstance(s, bytes) else (s or "") for s in (exc.stdout, exc.stderr)
        )
    cands = list(dict.fromkeys(re.findall(rf"\b{re.escape(project)}-\d+\b", partial)))
    owned: list[str] = []
    if cands:
        try:
            owned = _owned(jira_is.connection_id(), cands, correlation)
        except Exception:  # noqa: BLE001
            owned = []
    if owned:
        CREATED_KEYS.write_text("\n".join(owned) + "\n")
    return owned


def check_payload(payload: dict, seed: dict) -> str:
    """Assert the run created this run's ticket and returned the right outputs.
    Returns the verified issue key."""
    correlation = seed["correlationId"]
    project = seed["project_key"]

    create_nodes = completed_connector_node_ids(payload, JIRA_KEY, native_op_hint=JIRA_CREATE_OP)
    if not create_nodes:
        _fail("no Jira Create Issue step completed in the debug run")
    created_by_node = node_output_leaves(payload, create_nodes)

    cands = [s for leaf in collect_outputs(payload) for s in [str(leaf).strip()] if ISSUE_KEY_RE.match(s)]
    cands += re.findall(rf"\b{re.escape(project)}-\d+\b", get_last_debug_raw() or "")
    cands = list(dict.fromkeys(cands))
    if not cands:
        _fail(f"no Jira issue key in the debug output (expected a {project}-<n> key)")
    print(f"OK: candidate keys from debug: {cands}")

    # A key in the executed Create step's own response was created by this run:
    # record it before the tenant read, which can fail transiently.
    node_keys = [k for k in cands if k in created_by_node]
    if node_keys:
        CREATED_KEYS.write_text("\n".join(node_keys) + "\n")

    owned = _owned(jira_is.connection_id(), cands, correlation)
    created = list(dict.fromkeys(node_keys + owned))
    if created:
        CREATED_KEYS.write_text("\n".join(created) + "\n")
    if not owned:
        _fail(
            f"none of {cands} is a Jira issue whose summary contains {correlation!r}; "
            "the flow did not create the escalation ticket"
        )
    match = owned[0]
    print(f"OK: Jira ticket {match} exists and its summary carries {correlation!r}")

    if match not in created_by_node:
        _fail(f"{match} is not in the response of the Create Issue step that ran")
    assert_named_equals(payload, "jiraIssueKey", match, case_sensitive=True)
    for name, expected in (seed.get("expected") or {}).items():
        assert_named_equals(payload, name, expected, case_sensitive=(name in CASE_SENSITIVE))
    return match


def main() -> None:
    seed = json.loads(Path("seed.json").read_text())
    assert_flow_uses_connector_target(JIRA_KEY)
    print(f"OK: flow reaches {JIRA_KEY}")

    # One attempt only: the flow creates a ticket, so a whole-flow retry would
    # create a duplicate this checker never sees or cleans up.
    try:
        payload = run_debug(inputs=seed["inputs"], timeout=480, retries=1)
    except (subprocess.TimeoutExpired, SystemExit) as exc:
        owned = _record_partial(exc, seed["correlationId"], seed["project_key"])
        if isinstance(exc, SystemExit):
            raise
        _fail(
            f"flow debug timed out after {exc.timeout}s"
            + (f"; recorded this run's key(s) {owned} for teardown" if owned else "")
        )
    print("OK: flow debug completed")

    key = check_payload(payload, seed)
    print(f"PASS: the escalation run created Jira ticket {key} with the expected outputs")


if __name__ == "__main__":
    main()
