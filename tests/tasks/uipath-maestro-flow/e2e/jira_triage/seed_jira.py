#!/usr/bin/env python3
"""pre_run: write seed.json with a 3-issue batch (one High / Medium / Low) and
the escalation targets. No live issue is created here — the agent's flow creates
one issue per list item when the check runs `flow debug`.

The flow must accept the *escalation priority* as a flow input (not a hardcoded
constant) and escalate only the issues whose `priority` equals that input.
"Escalate" = transition the issue to In Progress (`status_id`), assign it to
`assignee_account_id`, and add a comment carrying `escalated_comment`. The check
supplies the input at debug time, so a flow that hardcodes a priority escalates
the wrong item and fails.

The list order is shuffled so a flow cannot cheat by escalating a fixed index.
Every summary and the comment marker embed the unique per-run `tag`.
"""

import json
import random
import secrets
from pathlib import Path

import jira_is

tag = secrets.token_hex(4)
issues = [
    {"summary": f"coder-eval jira triage {tag} {p.lower()}", "priority": p}
    for p in ("High", "Medium", "Low")
]
random.shuffle(issues)
seed = {
    "tag": tag,
    "project_key": jira_is.PROJECT_KEY,
    "issuetype_id": jira_is.ISSUETYPE_ID,
    "status_id": jira_is.STATUS_ID,               # transition target: In Progress
    "expected_status": jira_is.EXPECTED_STATUS,
    "assignee_account_id": jira_is.ASSIGNEE_ACCOUNT_ID,
    "escalated_comment": f"ESCALATED {tag}",
    "issues": issues,
}
Path("seed.json").write_text(json.dumps(seed, indent=2))
print(f"OK: wrote {len(issues)} seed issues (High/Medium/Low), tag={tag}")
