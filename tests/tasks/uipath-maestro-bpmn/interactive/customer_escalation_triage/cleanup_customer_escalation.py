#!/usr/bin/env python3
"""post_run backstop: delete anything the live grader created but could not free.

check_customer_escalation_behavior.py frees every live resource from a
``finally`` block. That block does not run if coder_eval SIGKILLs the graded
command on its timeout, which would leak Jira issues, Drive copies, Slack
messages, and an ephemeral Alpha solution with no second chance.

The grader therefore appends every created id to ``CLEANUP_JOURNAL`` the moment
the resource exists. This script replays that journal through the grader's own
leases, so the deletion calls are defined in exactly one place.

Wired in via ``post_run`` per the convention in tests/experiments/default.yaml.
Always exits 0 — post_run must never fail a task over cleanup.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_customer_escalation_behavior as grader


def read_journal(path: Path) -> dict[str, list]:
    records: dict[str, list] = {}
    if not path.is_file():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = record.get("kind")
        value = record.get("value")
        if not isinstance(kind, str) or value is None:
            continue
        records.setdefault(kind, []).append(value)
    return records


def main() -> int:
    journal = grader.CLEANUP_JOURNAL
    records = read_journal(journal)
    if not records:
        print("cleanup: nothing journalled; grader freed its own resources")
        return 0

    # Deletions issued here must not be journalled again.
    grader.CLEANUP_JOURNAL = Path("/dev/null")
    grader.ACTIVE_CLI_DEADLINE = None
    print(
        "cleanup: replaying journal "
        + ", ".join(f"{kind}={len(items)}" for kind, items in records.items())
    )

    failures: list[str] = []

    solution_ids = records.get("solution", [])
    if solution_ids:
        solution_lease = grader.AlphaSolutionLease(Path("unused.uipx"))
        solution_lease.solution_ids = set(solution_ids)
        try:
            failures.extend(solution_lease.cleanup())
        except BaseException as exc:
            failures.append(f"solution sweep: {exc}")

    connector_kinds = {"jira_issue", "drive_file", "slack_message"}
    if connector_kinds & set(records):
        try:
            environment = grader.discover_live_environment()
        except BaseException as exc:
            failures.append(f"environment discovery: {exc}")
        else:
            side_effects = grader.ConnectorSideEffectLease(environment)
            side_effects.jira_issue_ids = set(records.get("jira_issue", []))
            side_effects.drive_file_ids = set(records.get("drive_file", []))
            side_effects.slack_messages = {
                tuple(item) for item in records.get("slack_message", [])
            }
            protected = set(environment.drive_source_file_ids)
            leaked = side_effects.drive_file_ids & protected
            if leaked:
                # Never delete the shared Drive fixtures the task reads from.
                side_effects.drive_file_ids -= protected
                print(f"cleanup: skipped protected Drive fixtures {sorted(leaked)}")
            try:
                failures.extend(side_effects.cleanup())
            except BaseException as exc:
                failures.append(f"connector sweep: {exc}")

    if failures:
        print(f"cleanup: {len(failures)} resource(s) could not be freed:")
        for failure in failures:
            print(f"  - {failure}")
    else:
        print("cleanup: every journalled resource is gone")
        try:
            journal.unlink()
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
