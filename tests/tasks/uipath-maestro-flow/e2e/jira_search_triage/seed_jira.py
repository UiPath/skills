#!/usr/bin/env python3
"""pre_run: create a couple of real issues carrying a unique tag in their
summary, and write seed.json with the JQL that selects exactly them plus the
comment the flow should stamp on each match. The created keys are recorded to
`.created_keys` so teardown deletes them regardless of the run outcome.
"""

import json
import secrets
from pathlib import Path

import jira_is

tag = secrets.token_hex(4)
conn = jira_is.connection_id()
keys = [jira_is.create_issue(conn, f"coder-eval jira search-triage {tag} #{n}") for n in (1, 2)]
seed = {
    "tag": tag,
    "project_key": jira_is.PROJECT_KEY,
    "jql": f'project = {jira_is.PROJECT_KEY} AND summary ~ "{tag}"',
    "processed_comment": f"TRIAGED {tag}",
    "issue_keys": keys,
}
Path("seed.json").write_text(json.dumps(seed, indent=2))
Path(".created_keys").write_text("\n".join(keys) + "\n")
print(f"OK: seeded {len(keys)} issues {keys} (tag={tag}) for JQL search")
