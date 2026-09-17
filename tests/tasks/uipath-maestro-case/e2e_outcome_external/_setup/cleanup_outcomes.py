#!/usr/bin/env python3
"""post_run: remove the external records this run created.

Both targets are SHARED sandboxes, so the test cleans up after itself.

Mailbox messages are deleted from BOTH Inbox and Sent Items (the design sets
``saveToSentItems: true``, so each run leaves two copies).

Jira issues cannot be deleted — the sandbox account gets 403 "You do not have
permission to delete issues in this project" — so they are transitioned to Done
instead. One row per run therefore persists, but the project's open-issue list
stays clean. Worth requesting delete permission from the sandbox owner if the row
count ever matters.

Best-effort: post_run results are informational, so this always exits 0.
"""

from __future__ import annotations

import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from outcome_probe import (  # noqa: E402
    JIRA_CONN,
    JIRA_PROJECT,
    MAILBOX_FOLDER,
    OUTLOOK_CONN,
    _items,
    _uip_json,
    probe_issue,
)


def main() -> int:
    if not os.path.exists("seed.json"):
        print("cleanup_outcomes: no seed.json; nothing to clean")
        return 0
    with open("seed.json") as fh:
        token = (json.load(fh) or {}).get("run_token")
    if not token:
        print("cleanup_outcomes: seed.json carries no run_token; nothing to clean")
        return 0

    # Sweep BOTH folders. The design sets `saveToSentItems: true`, so every run
    # leaves a copy in Sent Items as well as the delivered copy in the Inbox;
    # cleaning only the Inbox silently accumulates one Sent Items message per run.
    for folder in (MAILBOX_FOLDER, "SentItems"):
        listing = _uip_json([
            "is", "resources", "run", "list",
            "uipath-microsoft-outlook365", "ListEmails",
            "--connection-id", OUTLOOK_CONN,
            "--query", f"parentFolderId={folder}&limit=100",
        ])
        for message in _items(listing):
            if token not in (message.get("subject") or ""):
                continue
            deleted = _uip_json([
                "is", "resources", "run", "delete",
                "uipath-microsoft-outlook365", "Message",
                "--connection-id", OUTLOOK_CONN,
                "--query", f"id={message.get('id')}", "-y",
            ])
            print(f"cleanup_outcomes: delete email [{folder}] "
                  f"{message.get('subject')!r} -> {deleted.get('Result')}")

    # Jira issues cannot be DELETED — the sandbox account gets 403 "You do not have
    # permission to delete issues in this project" — so close them instead. That keeps
    # the shared project's open-issue list clean even though the rows persist.
    for issue in probe_issue(token):
        key = issue["key"]
        listing = _uip_json([
            "is", "resources", "run", "list",
            "uipath-atlassian-jira", "issue_transitions",
            "--connection-id", JIRA_CONN,
            "--query", f"issueIdOrKey={key}",
        ])
        transitions = _items(listing) or (listing.get("Data") or {}).get("transitions") or []
        done = next((t.get("id") for t in transitions
                     if ((t.get("to") or {}).get("name")) == "Done"), None)
        if not done:
            print(f"cleanup_outcomes: Jira {key} has no Done transition; left open")
            continue
        # The body is {"id": <int>} — the connector rejects {"transition": {...}}
        # and {"transitionId": ...} with "'transition' identifier must be an integer".
        moved = _uip_json([
            "is", "resources", "run", "replace",
            "uipath-atlassian-jira", "curated-issue-status-update",
            "--connection-id", JIRA_CONN,
            "--query", f"issueIdOrKey={key}",
            "--body", json.dumps({"id": int(done)}),
        ])
        print(f"cleanup_outcomes: close Jira {key} -> {moved.get('Result')} "
              "(cannot delete: project forbids it for this account)")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # never let cleanup affect the run
        # Print the traceback, not just str(exc): a bare message hid a NameError in
        # the Jira branch, which only executes when there IS an issue to close — so
        # cleanup looked fine on dry runs and silently no-opped on real ones.
        print("cleanup_outcomes: best-effort cleanup failed:")
        traceback.print_exc()
        sys.exit(0)
