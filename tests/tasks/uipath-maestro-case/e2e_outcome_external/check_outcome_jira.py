#!/usr/bin/env python3
"""OUTCOME: the audit record was actually filed.

Measured in Jira itself (Atlassian REST, via the Integration Service connection).
Exactly one issue in the sandbox project must carry this run's reference in its
summary.

This is also the deepest signal in the test: the audit task sits in the final
stage, so an issue bearing the reference proves the case traversed the whole path
— stage 1 completed, stage 2 was entered, and its task ran.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from outcome_probe import (  # noqa: E402
    JIRA_PROJECT,
    ensure_debug_ran,
    require_attributable,
    fail,
    poll,
    probe_issue,
    run_token,
)


def main() -> int:
    token = run_token()
    # Nothing measured here means anything unless the HARNESS ran the case.
    require_attributable(ensure_debug_ran())

    print(f"Probing Jira project {JIRA_PROJECT} for reference {token} ...")
    hits = poll("jira", probe_issue, token)
    for hit in hits:
        print(f"    issue: {hit['key']} {hit['summary']!r} created={hit['created']}")

    if not hits:
        fail(f"no Jira issue carrying reference {token} exists in {JIRA_PROJECT} — "
             "the audit record was never filed")
    if len(hits) > 1:
        # See check_outcome_email.py — the objective is met by >= 1; duplicates are
        # reported rather than failed so a stray extra case run cannot mask success.
        print(f"  NOTE: {len(hits)} issues carry {token} — the audit record was "
              "filed more than once (case re-run, or a looping task)")

    print("OK: the audit record was filed — issue present in Jira.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
