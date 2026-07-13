#!/usr/bin/env python3
"""pre_run seed for the maestro-flow Jira e2e tasks.

Writes ``seed.json`` into the working directory (the agent's cwd) so the agent
and the check share the same non-hardcoded targets:

  - ``tag``          : short unique token, embedded in the summary so the check
                       can locate this run's issue deterministically.
  - ``summary``      : full summary string the agent must pass verbatim.
  - ``project_key`` / ``issuetype_id`` : create/get targets (CE / Task).
  - ``connection_name`` / ``folder_path`` : how the check resolves the live
                       connection to re-read tenant state.

Modes (positional arg):
  - (none)      : create task — write seed.json only; the agent's flow creates
                  the issue when the check runs ``flow debug``.
  - with_issue  : get task — additionally create a real seed issue now and
                  record its ``issue_key`` in seed.json so the flow has a live
                  key to read back.

Runs OUTSIDE the agent sandbox, so ``secrets`` is fine here.

Env overrides (optional): ``JIRA_PROJECT_KEY``, ``JIRA_ISSUETYPE_ID``,
``JIRA_CONNECTION_NAME``, ``JIRA_FOLDER_PATH``.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jira_is  # noqa: E402

WORKDIR = Path.cwd()


def main() -> None:
    with_issue = len(sys.argv) > 1 and sys.argv[1] == "with_issue"

    tag = secrets.token_hex(4)
    seed = {
        "tag": tag,
        "summary": f"coder-eval jira flow e2e {tag}",
        "project_key": os.environ.get("JIRA_PROJECT_KEY", jira_is.DEFAULT_PROJECT_KEY).strip(),
        "issuetype_id": os.environ.get("JIRA_ISSUETYPE_ID", jira_is.DEFAULT_ISSUETYPE_ID).strip(),
        "connection_name": os.environ.get("JIRA_CONNECTION_NAME", jira_is.DEFAULT_CONNECTION_NAME).strip(),
        "folder_path": os.environ.get("JIRA_FOLDER_PATH", jira_is.DEFAULT_FOLDER_PATH).strip(),
    }

    if with_issue:
        # get task: create the issue the flow will read back.
        jira = jira_is.Jira.from_seed(seed)
        key = jira.create_issue(seed["summary"])
        seed["issue_key"] = key
        # Track for teardown even if the check never runs.
        _append_created_key(key)
        print(f"OK: seeded live issue {key} (summary={seed['summary']!r})")
    else:
        print(f"OK: wrote seed targets (summary={seed['summary']!r}, project={seed['project_key']})")

    (WORKDIR / "seed.json").write_text(json.dumps(seed, indent=2))


def _append_created_key(key: str) -> None:
    path = WORKDIR / ".created_keys"
    existing = path.read_text().split() if path.is_file() else []
    if key not in existing:
        with path.open("a") as f:
            f.write(key + "\n")


if __name__ == "__main__":
    main()
