#!/usr/bin/env python3
"""Verify the agent read metrics and STOPPED, rather than polling for numbers.

Used by smoke/diagnose_metrics_not_trained.yaml. The fixture
(../_shared/mock_template_untrained) serves two projects whose metrics will
never appear on their own:

  fresh_contracts-8c21b4d3-ixp    Result: Failure / ErrorCode: not_found, exit 1
  pending_invoices-4f77e9a1-ixp   Success, Data == { Metrics: null }, exit 0

The skill's instruction for both is the same: report "no metrics yet" and stop.
The failure mode is an agent that reads the exit code or the null without
reading the ErrorCode and loops waiting for a number that no wait produces.

`file_matches_regex` cannot express an upper bound on invocation count, which is
the whole assertion here, so it lives in a script.

Budget: MAX_READS per project, counting `--model-version` probes toward the same
total — hunting an older version for numbers is the same mistake wearing a
different flag.

Why 3: `pending_invoices` IS trained (v3), and `get-metrics --model-version <N>`
is the skill's documented way to scope to a trained version — so latest, then
scoped to v3, is two legitimate reads with no polling at all, plus one spare for
orientation. Real polling does not look like 3; it looks like a loop waiting for
a number, which is 5 or 10.

Exits 0 when both projects were read within budget, 1 with a FAIL: line naming
the project and its count.
"""

import os
import re
import sys

LOG = os.environ.get("CALLS_LOG", "mocks/calls.log")
MAX_READS = 3
PROJECTS = ("fresh_contracts-8c21b4d3-ixp", "pending_invoices-4f77e9a1-ixp")

# Anchored the same way the task's regex criteria are, so the two cannot disagree
# about what counts as a metrics read.
CALL = re.compile(r"^uip\s+ixp\s+projects\s+get-metrics\s+[\"']?(?P<project>[\w.-]+)")


def main() -> int:
    if not os.path.exists(LOG):
        print(f"FAIL: invocation log {LOG!r} does not exist — cannot verify")
        return 1

    counts = {name: 0 for name in PROJECTS}
    unknown = 0
    with open(LOG, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            match = CALL.match(line.strip())
            if not match:
                continue
            project = match.group("project")
            if project in counts:
                counts[project] += 1
            else:
                # A get-metrics against something that is not one of the two
                # fixture projects: report it, but do not fail on it. The task's
                # own criteria own project-name correctness (Critical Rule 7).
                unknown += 1

    print("get-metrics reads: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    if unknown:
        print(f"note: {unknown} get-metrics call(s) against an unrecognised project")

    failures = []
    for name, count in counts.items():
        if count == 0:
            failures.append(f"FAIL: never read metrics for {name}")
        elif count > MAX_READS:
            failures.append(f"FAIL: polled metrics for {name} {count} times (budget {MAX_READS})")

    for line in failures:
        print(line)
    if failures:
        return 1

    print(f"PASS: both projects read within the {MAX_READS}-call budget, no polling")
    return 0


if __name__ == "__main__":
    sys.exit(main())
