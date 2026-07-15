#!/usr/bin/env python3
"""JiraCreateIssue: structural + live + tenant checks.

Exits non-zero on the first failure (``FAIL: ...``); prints ``OK: ...`` per check.

  1. A ``.flow`` file is valid JSON referencing the ``uipath-atlassian-jira``
     connector.
  2. LIVE: ``flow debug`` runs to ``Completed`` (this creates a real Jira issue)
     and produces an issue key in its outputs.
  3. TENANT: re-reading that key via ``curated_get_issue`` returns the seeded
     summary — proof the flow hit Jira rather than fabricating an output.

The confirmed key is recorded to ``.created_keys`` so post_run teardown deletes
it even if a later step fails.
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
from _shared.flow_check import collect_outputs, get_last_debug_raw, run_debug  # noqa: E402
import jira_is  # noqa: E402

JIRA_KEY = "uipath-atlassian-jira"
ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")


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

    payload = run_debug(timeout=480)
    print("OK: flow debug completed")

    # Candidate issue keys: clean output leaves + a project-scoped scan of the
    # raw debug payload (covers a key buried in a nested response blob).
    project = seed["project_key"]
    cands = [s for leaf in collect_outputs(payload) for s in [str(leaf).strip()] if ISSUE_KEY_RE.match(s)]
    cands += re.findall(rf"\b{re.escape(project)}-\d+\b", get_last_debug_raw() or "")
    cands = list(dict.fromkeys(cands))  # de-dup, keep order
    if not cands:
        _fail(f"no issue key (e.g. {project}-123) in flow debug outputs")
    print(f"OK: candidate keys from debug: {cands}")

    conn = jira_is.connection_id()
    for key in cands:
        fields = jira_is.get_issue(conn, key)
        if fields and fields.get("summary") == seed["summary"]:
            Path(".created_keys").write_text(key + "\n")  # for teardown
            print(f"OK: Jira issue {key} exists with the seed summary")
            print("PASS: all JiraCreateIssue checks passed")
            return
    _fail(
        f"none of {cands} carries the seed summary {seed['summary']!r} — the "
        "flow did not create the expected issue in Jira"
    )


if __name__ == "__main__":
    main()
