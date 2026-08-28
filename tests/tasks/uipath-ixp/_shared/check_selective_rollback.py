#!/usr/bin/env python3
"""Verify the improve-loop rollback happened in the right ORDER and scope.

Used by smoke/selective_prompt_rollback.yaml. The fixture
(../_shared/mock_template_regression) moves per-field F1 between reads:

  baseline v15   Vendor Name 0.34   Invoice Date 0.88
  after v16      Vendor Name 0.71   Invoice Date 0.62   <- mixed result
  after v17      Vendor Name 0.71   Invoice Date 0.86   <- after a correct rollback

Workflow step P7 requires the full sequence, not just the final command:

  1. read metrics           -> the baseline to compare against
  2. update BOTH fields     -> the iteration under test
  3. read metrics again     -> the comparison; skipping this means the rollback
                               was not a decision, it was a guess
  4. update ONLY the regressed field, restoring its prior instruction

`file_matches_regex` cannot express sequence, and it cannot express "no Vendor
Name in the LAST call" — a whole-iteration rollback still contains an
`Invoice Date` entry, so a content-only check passes it. Both live here.

Field identification is by NAME because that is what `--updates` carries:
`fields update-prompts` matches by name and reports an unmatched one WITHOUT
failing, so the name in the payload is the whole contract.

Exits 0 when the sequence and the final scope are both right, 1 with a FAIL:
line naming what broke.
"""

import os
import re
import sys

LOG = os.environ.get("CALLS_LOG", "mocks/calls.log")
UPDATE = re.compile(r"^uip\s+ixp\s+fields\s+update-prompts\b")
METRICS = re.compile(r"^uip\s+ixp\s+projects\s+get-metrics\b")
REGRESSED = "Invoice Date"
IMPROVED = "Vendor Name"


def main() -> int:
    if not os.path.exists(LOG):
        print(f"FAIL: invocation log {LOG!r} does not exist — cannot verify")
        return 1

    with open(LOG, encoding="utf-8", errors="replace") as fh:
        lines = [ln.strip() for ln in fh if ln.strip()]

    updates = [(i, ln) for i, ln in enumerate(lines) if UPDATE.match(ln)]
    metric_reads = [i for i, ln in enumerate(lines) if METRICS.match(ln)]

    print(f"update-prompts calls: {len(updates)} at {[i for i, _ in updates]}")
    print(f"get-metrics reads:    {len(metric_reads)} at {metric_reads}")

    if len(updates) < 2:
        print(f"FAIL: expected at least 2 update-prompts calls (iteration + rollback), saw {len(updates)}")
        return 1

    first_idx = updates[0][0]
    last_idx = updates[-1][0]

    # 1. A baseline read before the iteration. Without it there is no "before"
    #    score, so a later comparison is against a number the agent invented.
    if not any(i < first_idx for i in metric_reads):
        print("FAIL: no get-metrics before the first update-prompts — no baseline to compare against")
        return 1

    # 2. A comparison read between the iteration and the rollback. This is the
    #    step that makes the rollback a decision rather than a guess.
    compare = [i for i in metric_reads if first_idx < i < last_idx]
    if not compare:
        print("FAIL: no get-metrics between the iteration and the rollback — the rollback was not driven by a re-read")
        return 1

    # The LAST such read is the one the decision was made on, so it splits the
    # run: everything before it is the iteration, everything after is the
    # rollback. Nothing in the skill requires both fields in one `--updates`
    # call, so the iteration is judged on the union of its calls rather than on
    # the first one — an agent updating one field per call is doing the same
    # thing.
    compare_idx = max(compare)
    iteration = [call for i, call in updates if i < compare_idx]
    rollback = [call for i, call in updates if i > compare_idx]

    if not iteration:
        print("FAIL: every update-prompts call landed after the last comparison read — no iteration was measured")
        return 1
    if not rollback:
        print("FAIL: no update-prompts call after the comparison read — nothing was rolled back")
        return 1

    print(f"iteration calls: {len(iteration)}; rollback calls: {len(rollback)}")

    # 3. The iteration covered both fields, however many calls it took.
    applied = " ".join(iteration)
    missing = [f for f in (IMPROVED, REGRESSED) if f not in applied]
    if missing:
        print(f"FAIL: the iteration never updated {missing} — both fields were requested")
        return 1

    # 4. Scope of the rollback. The regressed field must be in it...
    if not any(REGRESSED in call for call in rollback):
        print(f"FAIL: the rollback does not name {REGRESSED!r}, the field that regressed")
        return 1

    # ...and the improved field must NOT be, or a real +0.37 gain was discarded.
    if any(IMPROVED in call for call in rollback):
        print(f"FAIL: the rollback also names {IMPROVED!r} — that reverts the whole iteration and throws away its gain")
        return 1

    print(f"PASS: baseline read -> both fields updated -> re-read -> rollback of {REGRESSED!r} only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
