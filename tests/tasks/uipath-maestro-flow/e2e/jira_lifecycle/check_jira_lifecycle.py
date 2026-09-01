#!/usr/bin/env python3
"""JiraLifecycle: structural + live + tenant checks for a loop-and-switch flow.

The agent builds ONE flow that, per seeded issue, creates a Jira issue and then
routes on the item's ``priority`` through a Switch to a branch-specific
Add-Comment. This check proves the composite shape actually ran end to end:

  1. STRUCTURAL: a ``.flow`` file is valid JSON referencing the
     ``uipath-atlassian-jira`` connector, and it contains a loop node
     (``core.logic.loop``) AND a branch node (``core.logic.switch`` or
     ``core.logic.decision``). The named shape must be present, not faked with
     N unrolled straight-line branches.
  2. LIVE: ``flow debug`` runs to ``Completed`` (this creates the real issues
     and posts the comments).
  3. TENANT: re-reading each created issue proves the loop created ALL seeded
     issues and the Switch routed each to the correct comment branch —
     ``High`` items carry the ``escalated_marker``, others the
     ``routine_marker``. Because the markers/summaries embed a unique per-run
     tag, a fabricated or hardcoded output cannot pass.

Every confirmed key is recorded to ``.created_keys`` as soon as it is seen, so
post_run teardown deletes it even if a later assertion fails.
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
    assert_flow_has_any_node_type,
    assert_flow_has_node_type,
    get_last_debug_raw,
    run_debug,
)
import jira_is  # noqa: E402

JIRA_KEY = "uipath-atlassian-jira"
ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _record_key(key: str) -> None:
    """Append a confirmed key to .created_keys (dedup) for teardown."""
    kf = Path(".created_keys")
    seen = set(kf.read_text().split()) if kf.is_file() else set()
    if key not in seen:
        with kf.open("a") as f:
            f.write(key + "\n")


def main() -> None:
    seed = json.loads(Path("seed.json").read_text())
    issues = seed["issues"]
    project = seed["project_key"]
    # summary -> expected comment marker for that item's Switch branch
    want_marker = {
        i["summary"]: (seed["escalated_marker"] if i["priority"] == "High" else seed["routine_marker"])
        for i in issues
    }

    # 1. STRUCTURAL ----------------------------------------------------------
    flows = glob.glob("**/*.flow", recursive=True)
    raw = next((r for p in flows for r in [open(p, encoding="utf-8").read()]
                if JIRA_KEY in r and '"nodes"' in r), None)
    if raw is None:
        _fail(f"no .flow references the {JIRA_KEY} connector (found {flows})")
    print(f"OK: flow references {JIRA_KEY}")

    assert_flow_has_node_type(["core.logic.loop"])
    assert_flow_has_any_node_type(["core.logic.switch", "core.logic.decision"])
    print("OK: flow contains a loop node and a switch/decision node")

    # 2. LIVE ----------------------------------------------------------------
    payload = run_debug(timeout=600)
    print("OK: flow debug completed")

    # Every CE-<n> key that appears anywhere in the debug payload — the create
    # nodes' responses land in elementExecutions/outputs, so this catches all
    # issues the loop created regardless of how the flow mapped its outputs.
    cands = list(dict.fromkeys(re.findall(rf"\b{re.escape(project)}-\d+\b", get_last_debug_raw() or "")))
    if not cands:
        _fail(f"no issue key (e.g. {project}-123) in flow debug payload — the loop created nothing")
    print(f"OK: candidate keys from debug: {cands}")

    # 3. TENANT --------------------------------------------------------------
    conn = jira_is.connection_id()
    found: dict[str, str] = {}  # summary -> key, for issues that are ours
    for key in cands:
        fields = jira_is.get_issue(conn, key)
        if not fields:
            continue
        _record_key(key)  # real issue this run created — always clean it up
        summary = fields.get("summary")
        if summary in want_marker:
            found[summary] = key
            marker = want_marker[summary]
            comment_blob = json.dumps(fields.get("comment"))
            if marker not in comment_blob:
                _fail(
                    f"issue {key} ({summary!r}) is missing its expected branch "
                    f"comment {marker!r} — the Switch routed it to the wrong "
                    f"branch (or no comment was posted)"
                )

    missing = [s for s in want_marker if s not in found]
    if missing:
        _fail(
            f"the loop did not create every seeded issue — missing {missing}; "
            f"created and matched: {list(found.values())}"
        )

    print(f"OK: all {len(want_marker)} issues created and each carries its correct branch comment")
    print("PASS: all JiraLifecycle checks passed")


if __name__ == "__main__":
    main()
