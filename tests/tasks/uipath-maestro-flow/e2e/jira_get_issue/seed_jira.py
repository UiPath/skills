#!/usr/bin/env python3
"""pre_run: create a real seed issue and write seed.json so the flow has a live
key to read back. The unique tag is embedded in the summary; the created key is
recorded to `.created_keys` so teardown can delete it."""

import json
import secrets
from pathlib import Path

import jira_is

tag = secrets.token_hex(4)
summary = f"coder-eval jira flow e2e {tag}"
conn = jira_is.connection_id()
key = jira_is.create_issue(conn, summary)
seed = {
    "tag": tag,
    "summary": summary,
    "issue_key": key,
    "project_key": jira_is.PROJECT_KEY,
    "issuetype_id": jira_is.ISSUETYPE_ID,
}
Path("seed.json").write_text(json.dumps(seed, indent=2))
Path(".created_keys").write_text(key + "\n")
print(f"OK: seeded live issue {key} (summary={summary!r})")
