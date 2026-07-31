#!/usr/bin/env python3
"""pre_run: write seed.json with the create targets (no live issue yet — the
agent's flow creates it when the check runs `flow debug`). The unique tag in
the summary lets the check locate this run's issue."""

import json
import secrets
from pathlib import Path

import jira_is

tag = secrets.token_hex(4)
summary = f"coder-eval jira flow e2e {tag}"
seed = {
    "tag": tag,
    "summary": summary,
    "project_key": jira_is.PROJECT_KEY,
    "issuetype_id": jira_is.ISSUETYPE_ID,
}
Path("seed.json").write_text(json.dumps(seed, indent=2))
print(f"OK: wrote seed targets (summary={summary!r}, project={jira_is.PROJECT_KEY})")
