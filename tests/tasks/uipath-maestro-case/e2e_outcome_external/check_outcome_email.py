#!/usr/bin/env python3
"""OUTCOME: the approver was actually notified.

Measured in the sending mailbox itself (Microsoft Graph, via the Integration
Service connection), not in the caseplan, the debug log, or anything the agent
said. A message carrying this run's reference must sit in Sent Items, addressed
to the approver. The approver's mailbox is a different one, so delivery is read
from the sender's side.

A saved draft does not satisfy this: drafts stay in Drafts, so a case that
leaves ``saveAsDraft`` at its default of ``true`` fails here even though its
caseplan looks correct and validates.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_setup"))
from outcome_probe import (  # noqa: E402
    email_miss_reason,
    ensure_debug_ran,
    require_attributable,
    fail,
    poll,
    probe_email,
    run_token,
)


def main() -> int:
    token = run_token()
    # Nothing measured here means anything unless the HARNESS ran the case.
    require_attributable(ensure_debug_ran())

    print(f"Probing the sandbox mailbox for reference {token} ...")
    hits = poll("email", probe_email, token)
    for hit in hits:
        print(f"    email: {hit['subject']!r} sent={hit['received']}")

    if not hits:
        why = email_miss_reason()
        fail(f"no email carrying reference {token} reached the approver's mailbox — "
             + (f"found {why}" if why else "no message carries it at all")
             + " (a saved draft does not count)")
    if len(hits) > 1:
        # The objective is "the approver was notified", so extra copies still meet it.
        # Duplicates are reported but not failed: the agent disobeying the "harness runs
        # debug" contract would otherwise corrupt an exactly-once assertion. Running
        # debug is graded separately by its own command_not_executed criterion.
        print(f"  NOTE: {len(hits)} messages carry {token} — the notification was "
              "delivered more than once (case re-run, or a looping task)")

    print("OK: the approver was notified — a sent message to the approver carries the reference.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
