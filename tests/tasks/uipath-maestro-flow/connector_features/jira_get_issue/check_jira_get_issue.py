#!/usr/bin/env python3
"""JiraGetIssue: structural + live checks.

Exits non-zero on the first failure with ``FAIL: ...``; prints ``OK: ...`` per
check on success.

  1. A ``.flow`` file is valid JSON with ``nodes``/``edges``.
  2. It references the ``uipath-atlassian-jira`` connector key.
  3. It references a Get-Issue operation.
  4. It references the SEEDED issue key (from seed.json, unique per run) — so
     the agent read the key from the fixture rather than inventing one.
  5. LIVE: ``flow debug`` runs to ``Completed`` and its outputs contain the
     seeded issue's summary — proof the flow actually fetched the issue from
     Jira.

The issue is created + tracked by pre_run seed_jira.py and removed by post_run
teardown_jira.py; this check does not create or delete anything.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
MAESTRO = os.path.dirname(os.path.dirname(HERE))  # …/uipath-maestro-flow
sys.path.insert(0, MAESTRO)
from _shared.flow_check import assert_outputs_contain, run_debug  # noqa: E402

JIRA_KEY = "uipath-atlassian-jira"
GET_OP_RE = re.compile(r"get[\s_-]?issue|curated_get_issue", re.IGNORECASE)
WORKDIR = Path.cwd()


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _load_seed() -> dict:
    for candidate in (WORKDIR / "seed.json", Path(HERE) / "seed.json"):
        if candidate.is_file():
            return json.loads(candidate.read_text())
    _fail("seed.json not found (expected pre_run seed_jira.py to write it)")


def _flow_raw() -> str:
    flows = glob.glob("**/*.flow", recursive=True)
    if not flows:
        _fail("no .flow file found under cwd")
    for path in flows:
        raw = open(path, encoding="utf-8").read()
        try:
            flow = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if "nodes" in flow and "edges" in flow and JIRA_KEY in raw:
            print(f"OK: {path}: {len(flow['nodes'])} nodes, {len(flow['edges'])} edges, {JIRA_KEY} present")
            return raw
    _fail(f"no valid .flow references the {JIRA_KEY} connector (checked {flows})")


def main() -> None:
    seed = _load_seed()
    issue_key = seed.get("issue_key")
    if not issue_key:
        _fail("seed.json has no issue_key — pre_run must seed with `with_issue`")

    raw = _flow_raw()
    if not GET_OP_RE.search(raw):
        _fail("flow does not reference a Get-Issue operation")
    print("OK: Get-Issue operation referenced")
    if issue_key not in raw:
        _fail(
            f"flow does not reference the seeded issue key {issue_key!r} — the "
            "agent must read the key from seed.json, not hardcode a literal"
        )
    print(f"OK: flow references the seeded key {issue_key}")

    payload = run_debug(timeout=240)
    print("OK: flow debug completed")

    assert_outputs_contain(payload, seed["summary"])
    print("OK: flow outputs contain the seeded issue summary")
    print("PASS: all JiraGetIssue checks passed")


if __name__ == "__main__":
    main()
