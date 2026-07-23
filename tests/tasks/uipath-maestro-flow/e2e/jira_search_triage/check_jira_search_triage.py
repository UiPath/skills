#!/usr/bin/env python3
"""JiraSearchTriage: structural + live + tenant checks for a JQL-search-driven
triage flow.

Checks:
  1. STRUCTURAL: a valid `.flow` references the `uipath-atlassian-jira`
     connector, a search activity, and a loop node.
  2. LIVE: `flow debug` runs to Completed.
  3. TENANT: both pre-seeded issues (unique per run) carry the triage comment —
     proof the search found them and the loop commented each.
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
from _shared.flow_check import assert_flow_has_node_type, run_debug  # noqa: E402
import jira_is  # noqa: E402

JIRA_KEY = "uipath-atlassian-jira"
SEARCH_OP_RE = re.compile(r"search[\s_-]?issues|search-issues-by-jql", re.IGNORECASE)


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def main() -> None:
    seed = json.loads(Path("seed.json").read_text())

    flows = glob.glob("**/*.flow", recursive=True)
    raw = next((r for p in flows for r in [open(p, encoding="utf-8").read()]
                if JIRA_KEY in r and '"nodes"' in r), None)
    if raw is None:
        _fail(f"no .flow references the {JIRA_KEY} connector (found {flows})")
    print(f"OK: flow references {JIRA_KEY}")
    if not SEARCH_OP_RE.search(raw):
        _fail("flow does not reference a Search-Issues (JQL) operation")
    assert_flow_has_node_type(["core.logic.loop"])
    print("OK: flow references a JQL search op and a loop node")

    payload = run_debug(timeout=600)
    print("OK: flow debug completed")

    conn = jira_is.connection_id()
    marker = seed["processed_comment"]
    for key in seed["issue_keys"]:
        fields = jira_is.get_issue(conn, key)
        if not fields:
            _fail(f"seeded issue {key} not found on re-read")
        if marker not in json.dumps(fields.get("comment")):
            _fail(f"issue {key} is missing the triage comment {marker!r} — the "
                  "search-driven loop did not comment it")
    print(f"OK: all {len(seed['issue_keys'])} matched issues carry the triage comment")
    print("PASS: all JiraSearchTriage checks passed")


if __name__ == "__main__":
    main()
