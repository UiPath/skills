#!/usr/bin/env python3
"""pre_run: write seed.json with a small batch of issues to create and the
per-branch comment markers. No live issue is created here — the agent's flow
creates one issue per list item when the check runs `flow debug`.

The batch mixes `priority` values so the flow's Switch node must route each
item to a different Add-Comment branch:

    priority == "High"  -> comment carries `escalated_marker`
    otherwise           -> comment carries `routine_marker`

Every summary and both markers embed the unique per-run `tag`, so the check can
locate exactly this run's issues (no JQL search — the connection is curated-ops
only) and tell the two branches apart.
"""

import json
import secrets
from pathlib import Path

import jira_is

tag = secrets.token_hex(4)
issues = [
    {"summary": f"coder-eval jira lifecycle {tag} item1", "priority": "High"},
    {"summary": f"coder-eval jira lifecycle {tag} item2", "priority": "Low"},
    {"summary": f"coder-eval jira lifecycle {tag} item3", "priority": "High"},
]
seed = {
    "tag": tag,
    "project_key": jira_is.PROJECT_KEY,
    "issuetype_id": jira_is.ISSUETYPE_ID,
    "issues": issues,
    "escalated_marker": f"ESCALATED {tag}",
    "routine_marker": f"ROUTINE {tag}",
}
Path("seed.json").write_text(json.dumps(seed, indent=2))
highs = sum(1 for i in issues if i["priority"] == "High")
print(f"OK: wrote {len(issues)} seed issues ({highs} High / {len(issues) - highs} other), tag={tag}")
