#!/usr/bin/env python3
"""Verify the escalation flow actually creates a Jira ticket.

Outcome-based, tenant-confirmed (mirrors e2e/jira_create_issue):
  1. A `.flow` references the uipath-atlassian-jira connector.
  2. LIVE: `flow debug` on the seeded Sev1 case runs to Completed and emits a
     Jira issue key (this creates a real issue).
  3. TENANT: re-reading that key via curated_get_issue returns an issue whose
     summary carries the seeded correlationId — proof the flow hit Jira and
     created THIS run's ticket, not a fabricated output.

The confirmed key is written to `.created_keys` so post_run teardown deletes it
even if a later assertion fails.
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # local jira_is
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))  # …/uipath-maestro-flow (for _shared)
from _shared.flow_check import (  # noqa: E402
    assert_named_equals,
    collect_outputs,
    completed_connector_node_ids,
    completed_node_ids_of_type,
    find_node_output_value,
    get_last_debug_raw,
    node_output_leaves,
    normalized,
    run_debug,
)
import jira_is  # noqa: E402

JIRA_KEY = "uipath-atlassian-jira"
JIRA_CREATE_OP = "create-issue"  # matched by op so a connector-proxy Create (op in endpoint) also counts
ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
CASE_SENSITIVE = {"caseKey", "jiraIssueKey"}  # opaque ids — exact-case match


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def main() -> None:
    seed = json.loads(Path("seed.json").read_text())
    correlation = seed["correlationId"]
    project = seed["project_key"]

    flows = glob.glob("**/*.flow", recursive=True)
    if not any(JIRA_KEY in open(p, encoding="utf-8").read() for p in flows):
        _fail(f"no .flow references the {JIRA_KEY} connector (found {flows})")
    print(f"OK: flow references {JIRA_KEY}")

    # No whole-flow retries: this flow CREATES a Jira issue, so re-running the
    # whole flow on a transient poll error would create a duplicate ticket that
    # this checker (deriving keys from the final attempt) wouldn't see or clean
    # up. One attempt only; a genuine transient failure fails the run cleanly.
    try:
        payload = run_debug(inputs=seed["inputs"], timeout=480, retries=1)
    except (subprocess.TimeoutExpired, SystemExit) as exc:
        # ANY debug failure (timeout, a later-node fault, or a transient poll
        # error surfaced by run_debug via SystemExit) may leave a Create Issue
        # that already succeeded. This connection is curated single-record (no JQL
        # search), so best-effort: from whatever debug output we have, record ONLY
        # keys whose summary carries this run's correlationId (verified via
        # get_issue) — never an unrelated pre-existing issue.
        partial = get_last_debug_raw() or ""
        if isinstance(exc, subprocess.TimeoutExpired):
            partial += "".join(
                s.decode() if isinstance(s, bytes) else (s or "")
                for s in (exc.stdout, exc.stderr)
            )
        cands = list(dict.fromkeys(re.findall(rf"\b{re.escape(project)}-\d+\b", partial)))
        owned = []
        if cands:
            try:
                conn = jira_is.connection_id()
                owned = [
                    k for k in cands
                    for f in [jira_is.get_issue(conn, k)]
                    if f is not None and correlation in str(f.get("summary", ""))
                ]
            except Exception:  # noqa: BLE001 — best-effort cleanup, never mask the failure
                owned = []
        if owned:
            Path(".created_keys").write_text("\n".join(owned) + "\n")
        if isinstance(exc, SystemExit):
            raise  # preserve run_debug's original failure message
        _fail(
            f"flow debug timed out after {exc.timeout}s"
            + (f"; recorded this-run key(s) {owned} for teardown" if owned else "")
        )
    print("OK: flow debug completed")

    # Execution evidence: the Jira CREATE-ISSUE node specifically must have
    # executed in the debugged flow (not merely any Jira node — a read op could
    # surface an authoring-time key). A disconnected/absent Create node fails here.
    create_nodes = completed_connector_node_ids(payload, JIRA_KEY, native_op_hint=JIRA_CREATE_OP)
    if not create_nodes:
        _fail(
            "no Jira Create-Issue node completed in the debug trace — the debugged "
            "flow did not execute the Create Issue activity"
        )

    cands = [s for leaf in collect_outputs(payload) for s in [str(leaf).strip()] if ISSUE_KEY_RE.match(s)]
    cands += re.findall(rf"\b{re.escape(project)}-\d+\b", get_last_debug_raw() or "")
    cands = list(dict.fromkeys(cands))
    if not cands:
        _fail(f"no Jira issue key (e.g. {project}-123) in flow debug outputs — the flow did not create a ticket")
    print(f"OK: candidate keys from debug: {cands}")

    # Persist proven-created keys BEFORE the fallible tenant reread: any candidate
    # that appears in the executed Create-Issue node's OWN output was created by
    # THIS run, so teardown can delete it even if the tenant reread below fails
    # transiently (jira_is.get_issue collapses a 5xx/auth envelope to None, which
    # would otherwise leave owned empty and leak the issue in the shared CE project).
    node_keys = [k for k in cands if k in node_output_leaves(payload, create_nodes)]
    if node_keys:
        Path(".created_keys").write_text("\n".join(node_keys) + "\n")

    conn = jira_is.connection_id()

    # Tenant-confirm: the key belongs to this run — an issue whose summary carries
    # this run's correlationId. Never deletes an unrelated pre-existing issue
    # (e.g. if a wrong flow echoed some other CE key into its output).
    owned = [
        k
        for k in cands
        for f in [jira_is.get_issue(conn, k)]
        if f is not None and correlation in str(f.get("summary", ""))
    ]
    created = list(dict.fromkeys(node_keys + owned))
    if created:
        Path(".created_keys").write_text("\n".join(created) + "\n")  # this run's ticket(s) only
    if not owned:
        _fail(
            f"none of {cands} is a Jira issue whose summary contains {correlation!r} — "
            "the flow did not create the expected escalation ticket"
        )
    match = owned[0]
    print(f"OK: Jira ticket {match} exists and its summary carries {correlation!r}")

    # Tie the verified key to the executed Create-Issue node's OWN response — the
    # created key must appear in that node's output, so a read op surfacing an
    # authoring-time key (whose node is not the Create) cannot satisfy this.
    if match not in node_output_leaves(payload, create_nodes):
        _fail(
            f"created key {match} is not in the executed Create-Issue node's output; "
            "the debugged Create Issue did not produce this key"
        )

    # Require the flow to actually EXPOSE the created key as jiraIssueKey (End
    # mapping present), not just create the ticket — harvesting the key from raw
    # debug text must not substitute for the required output. jiraIssueKey is an
    # opaque tenant-issued identifier: compare case-sensitively (a lowercased
    # variant must not pass).
    assert_named_equals(payload, "jiraIssueKey", match, case_sensitive=True)

    # Named classification/correlation outputs the prompt requires (severity, caseKey).
    # Opaque ids (caseKey) compare case-sensitively; enum-like values (severity) do not.
    for name, expected in (seed.get("expected") or {}).items():
        assert_named_equals(payload, name, expected, case_sensitive=(name in CASE_SENSITIVE))

    # Classification the prompt requires the Script to compute but does not map to a
    # named End out (engineeringNeeded) — verify it against the ONE classification
    # Script: the executed Script whose own output carries the expected severity.
    # Binding to that single node (not the set of all completed Scripts) stops an
    # unrelated Script from supplying engineeringNeeded while the real classifier omits it.
    script_nodes = completed_node_ids_of_type(payload, "script")
    sev = (seed.get("expected") or {}).get("severity")
    sev_scripts = [
        nid for nid in sorted(n for n in script_nodes if n)
        if normalized(find_node_output_value(payload, "severity", node_ids={nid})) == normalized(sev)
    ]
    if not sev_scripts:
        _fail(f"no executed Script node produced the expected severity {sev!r} — cannot bind the classification checks")
    # Bind ALL classifications to ONE node: the same Script that produced the
    # severity must ALSO carry the expected engineeringNeeded. A split across two
    # cosmetic Scripts (one emits severity, another engineeringNeeded) fails.
    expected_script = seed.get("expected_script") or {}

    def carries_all(nid: str):
        for name, expected in expected_script.items():
            actual = find_node_output_value(payload, name, node_ids={nid})
            if actual is None:
                return f"{name!r} missing"
            if normalized(actual) != normalized(expected):
                return f"{name!r}={actual!r} (expected {expected!r})"
        return None

    if not any(carries_all(nid) is None for nid in sev_scripts):
        detail = "; ".join(f"{nid}: {carries_all(nid)}" for nid in sev_scripts)
        _fail(
            "no single executed Script carries the expected severity AND the "
            f"classification fields together — classification is split or missing ({detail})"
        )

    print("PASS: escalation flow created a real Jira ticket with the expected classification")


if __name__ == "__main__":
    main()
