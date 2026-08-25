#!/usr/bin/env python3
"""Grade the transaction-shape / idempotency review.

Planted (real ReFramework Framework/Process.xaml): each queue item is a batch
whose line items are all posted downstream with NO idempotency key, so a
mid-batch retry re-posts already-sent rows.

PASS requires the report to (a) classify the one-to-many / bulk shape AS a
problem, and (b) flag the missing idempotency / duplicate-on-retry risk — a
report that says "this is not one-to-many; no duplicate risk" is rejected. The
planted loop must also still exist in the sandbox fixture (guards shell edits).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from grader_common import report_text, asserts, asserts_any, fixture_contains  # noqa: E402

PROJECT = "TxnShapeBot"
SHAPE = ("one-to-many", "one to many", "bulk-in-transaction", "bulk in transaction",
         "bulk", "batch", "multiple records", "multiple items", "many records",
         "multiple line items", "several records", "per transaction")
DUP = ("duplicate", "re-post", "repost", "reprocess", "re-process", "posted again",
       "processed twice", "double post", "already posted", "already processed")


def main() -> None:
    text = report_text(500)

    if not fixture_contains(f"{PROJECT}/Framework/Process.xaml", "AddQueueItem"):
        sys.exit(f"FAIL: {PROJECT}/Framework/Process.xaml no longer contains the planted "
                 "per-line-item AddQueueItem loop (fixture appears mutated).")

    if not asserts_any(text, SHAPE, presence=True):
        sys.exit("FAIL: report does not classify the one-to-many / bulk transaction shape "
                 "as a problem (a 'not one-to-many' dismissal does not count).")

    idem = asserts(text, "idempoten", presence=False) or asserts_any(text, DUP, presence=True)
    if not idem:
        sys.exit("FAIL: report does not flag the missing idempotency / duplicate-on-retry "
                 "risk (a 'no duplicate risk' dismissal does not count).")

    print("OK: one-to-many shape + missing idempotency both flagged as problems; fixture intact")
    print("PASS")


if __name__ == "__main__":
    main()
