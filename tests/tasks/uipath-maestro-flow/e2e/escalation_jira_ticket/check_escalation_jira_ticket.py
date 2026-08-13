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
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # local jira_is
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))  # …/uipath-maestro-flow (for _shared)
from _shared.flow_check import (  # noqa: E402
    assert_named_equals,
    collect_outputs,
    get_last_debug_raw,
    run_debug,
)
import jira_is  # noqa: E402

JIRA_KEY = "uipath-atlassian-jira"
ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")


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

    payload = run_debug(inputs=seed["inputs"], timeout=480)
    print("OK: flow debug completed")

    cands = [s for leaf in collect_outputs(payload) for s in [str(leaf).strip()] if ISSUE_KEY_RE.match(s)]
    cands += re.findall(rf"\b{re.escape(project)}-\d+\b", get_last_debug_raw() or "")
    cands = list(dict.fromkeys(cands))
    if not cands:
        _fail(f"no Jira issue key (e.g. {project}-123) in flow debug outputs — the flow did not create a ticket")
    print(f"OK: candidate keys from debug: {cands}")

    conn = jira_is.connection_id()

    # Record ONLY keys proven to belong to this run — an issue whose summary
    # carries this run's correlationId. This is written before the classification
    # assertions so teardown still cleans up if a later assertion fails, while
    # never deleting an unrelated pre-existing issue in the shared CE project
    # (e.g. if a wrong flow echoed some other CE key into its output).
    owned = [
        k
        for k in cands
        for f in [jira_is.get_issue(conn, k)]
        if f is not None and correlation in str(f.get("summary", ""))
    ]
    if owned:
        Path(".created_keys").write_text("\n".join(owned) + "\n")  # this run's ticket(s) only
    if not owned:
        _fail(
            f"none of {cands} is a Jira issue whose summary contains {correlation!r} — "
            "the flow did not create the expected escalation ticket"
        )
    match = owned[0]
    print(f"OK: Jira ticket {match} exists and its summary carries {correlation!r}")

    # Classification outputs the prompt also requires (e.g. severity=Sev1).
    for name, expected in (seed.get("expected") or {}).items():
        assert_named_equals(payload, name, expected)

    print("PASS: escalation flow created a real Jira ticket with the expected classification")


if __name__ == "__main__":
    main()
