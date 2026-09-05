#!/usr/bin/env python3
"""JiraGetIssue: structural + live checks.

Exits non-zero on the first failure (``FAIL: ...``); prints ``OK: ...`` per check.

  1. A ``.flow`` file is valid JSON referencing the ``uipath-atlassian-jira``
     connector and a Get-Issue operation.
  2. It references the SEEDED issue key (from seed.json, unique per run) — so
     the agent read the key from the fixture rather than inventing one.
  3. LIVE: ``flow debug`` runs to ``Completed`` and its outputs contain the
     seeded issue's summary — proof the flow actually fetched it from Jira.

The issue is created/cleaned up by seed_jira.py / teardown_jira.py; this check
does not touch the tenant.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-maestro-flow")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.dirname(os.path.dirname(HERE))
)
sys.path.insert(0, _shared_root)  # …/uipath-maestro-flow (for _shared)
from _shared.flow_check import assert_outputs_contain, find_flow_file, run_debug  # noqa: E402

JIRA_KEY = "uipath-atlassian-jira"
GET_OP_RE = re.compile(r"get[\s_-]?issue|curated_get_issue", re.IGNORECASE)


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def main() -> None:
    seed = json.loads(Path("seed.json").read_text())
    issue_key = seed["issue_key"]

    flow_path = find_flow_file()
    raw = Path(flow_path).read_text(encoding="utf-8")
    if JIRA_KEY not in raw or '"nodes"' not in raw:
        _fail(f"{flow_path} does not reference the {JIRA_KEY} connector")
    print(f"OK: flow references {JIRA_KEY}")
    if not GET_OP_RE.search(raw):
        _fail("flow does not reference a Get-Issue operation")
    if issue_key not in raw:
        _fail(f"flow does not reference the seeded key {issue_key!r} (agent must read it from seed.json)")
    print(f"OK: flow references a Get-Issue op and the seeded key {issue_key}")

    payload = run_debug(timeout=480)
    print("OK: flow debug completed")

    assert_outputs_contain(payload, seed["summary"])
    print("OK: flow outputs contain the seeded issue summary")
    print("PASS: all JiraGetIssue checks passed")


if __name__ == "__main__":
    main()
