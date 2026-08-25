#!/usr/bin/env python3
"""Grade the REFramework-integrity review.

Planted (real ReFramework template's Framework/Process.xaml): a System.Exception
is caught and only logged with NO Rethrow, so the framework's SetTransactionStatus
never sees a failure and the queue item is reported to Orchestrator as Successful.

Only this defect is planted — Config.xlsx keeps the template default
MaxRetryNumber = 0, so double-retry / circuit-breaker are NOT accepted. PASS
requires the swallowed system exception flagged AS a problem; "rethrows
correctly" does not count. The planted swallow must still exist in the fixture.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from grader_common import report_text, asserts, asserts_any, fixture_contains  # noqa: E402

PROJECT = "REFrameworkBot"


def main() -> None:
    text = report_text(500)

    if not fixture_contains(f"{PROJECT}/Framework/Process.xaml", "Nothing is rethrown"):
        sys.exit(f"FAIL: {PROJECT}/Framework/Process.xaml no longer contains the planted "
                 "swallowed-exception catch (fixture appears mutated).")

    swallowed = asserts_any(
        text, ["swallow", "marked success", "marked as success", "reported as success",
               "treated as success", "considered successful", "silently succeed"], presence=True
    ) or asserts(text, "rethrow", presence=False)

    if not swallowed:
        sys.exit("FAIL: report does not flag the swallowed system exception as a problem "
                 "(System.Exception caught, no Rethrow, item reported to Orchestrator as "
                 "Successful). 'Rethrows correctly' does not count.")
    print("OK: report flags the swallowed system exception; fixture intact")
    print("PASS")


if __name__ == "__main__":
    main()
