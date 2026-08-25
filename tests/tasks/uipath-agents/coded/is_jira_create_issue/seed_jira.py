#!/usr/bin/env python3
"""Seed file for the coded IS Jira create-issue e2e.

Writes `seed.json` in the working directory with:

  - `uuid8`: short unique tag to embed in the issue summary so the check
    script can locate the agent's new issue deterministically.
  - `summary`: full summary string the agent must pass verbatim.
  - `project_key` / `issuetype_id`: env-supplied targets for the
    progressive-disclosure `-f project=... -f issuetype=...` call.
  - `epic_key`: env-supplied epic the created issue must be filed under
    (parent / epic-link), so the test exercises parent-field resolution
    and lands issues under a known epic.

Env vars (optional — default to the canonical test target):

  JIRA_PROJECT_KEY   — Jira project to file into (default "PRODEV")
  JIRA_ISSUETYPE_ID  — numeric issuetype id (default "3" = Task)
  JIRA_EPIC_KEY      — epic in that project to file under (default "PRODEV-685")

Override any of them to point the e2e at a different tenant/project.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path

WORKDIR = Path.cwd()


def main() -> None:
    # Non-secret targets default to the canonical test epic
    # (PRODEV-685 "Test coded agent activity creation E2E" on the test tenant);
    # override via env for a different tenant/project.
    project_key = os.environ.get("JIRA_PROJECT_KEY", "PRODEV").strip()
    issuetype_id = os.environ.get("JIRA_ISSUETYPE_ID", "3").strip()
    epic_key = os.environ.get("JIRA_EPIC_KEY", "PRODEV-685").strip()

    uuid8 = secrets.token_hex(4)
    summary = f"uipath-agents coded-is eval {uuid8}"
    seed = {
        "uuid8": uuid8,
        "summary": summary,
        "project_key": project_key,
        "issuetype_id": issuetype_id,
        "epic_key": epic_key,
        "connection_name": "jira-coded-eval",
        "folder_path": "Shared/uipath-agents",
    }
    (WORKDIR / "seed.json").write_text(json.dumps(seed, indent=2))
    print(f"OK: wrote seed.json with summary={summary!r}, project={project_key}, epic={epic_key}")


if __name__ == "__main__":
    main()
