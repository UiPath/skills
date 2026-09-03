#!/usr/bin/env python3
"""Verify Critical Rule 18 was FOLLOWED, not merely survived.

Used by smoke/occurrence_renumber.yaml. The resolving mock
(../_shared/mock_template_occurrence) already catches a stale index by the row it
lands on — but only when the ordering happens to shift under it. Confirming
Steel bolts (occurrence 2) before Pallet wrap (occurrence 3) leaves Pallet wrap's
index unmoved, so a run that carried an index across a write can end up on the
right rows by luck.

Rule 18 is a rule about method, so this checks the method:

  - one per-occurrence call        -> nothing to invalidate, passes
  - two or more                    -> a get-predictions must sit between each
                                      consecutive pair

Batching every target into ONE `--updates` call is the path the skill
recommends, and it passes here trivially: all indices in a single call resolve
against the same read, so there is no index to carry.

Calls that name no occurrence (the plain `--fields` form, which hits every row)
are not counted — the task's resolved-row guard owns that mistake, and counting
them here would report the same failure twice.

Exits 0 when the method holds, 1 with a FAIL: line naming the gap.
"""

import json
import os
import re
import sys

LOG = os.environ.get("CALLS_JSONL", "mocks/calls.jsonl")
WRITE_VERBS = ("confirm", "unconfirm")


def targets_an_occurrence(argv):
    """True when this invocation names specific occurrence indices.

    Read from argv (a list) rather than the flat log so an `--updates` payload
    containing spaces cannot be mistaken for several arguments.
    """
    for i, token in enumerate(argv):
        if token == "--occurrence" and i + 1 < len(argv):
            return True
        if token.startswith("--occurrence="):
            return True
        if token == "--updates" and i + 1 < len(argv):
            return bool(re.search(r'"occurrence"\s*:\s*\d+', argv[i + 1]))
        if token.startswith("--updates="):
            return bool(re.search(r'"occurrence"\s*:\s*\d+', token))
    return False


def main() -> int:
    if not os.path.exists(LOG):
        print(f"FAIL: invocation log {LOG!r} does not exist — cannot verify")
        return 1

    writes, reads = [], []
    with open(LOG, encoding="utf-8", errors="replace") as fh:
        for index, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            try:
                argv = json.loads(line).get("argv")
            except ValueError:
                print(f"FAIL: unparseable record at line {index + 1} — the verdict cannot be trusted")
                return 1
            if not isinstance(argv, list) or argv[:2] != ["ixp", "labellings"]:
                continue
            verb = argv[2] if len(argv) > 2 else ""
            if verb == "get-predictions":
                reads.append(index)
            elif verb in WRITE_VERBS and targets_an_occurrence(argv):
                writes.append(index)

    print(f"per-occurrence writes at {writes}; get-predictions reads at {reads}")

    if not writes:
        print("FAIL: no per-occurrence confirm/unconfirm call was made")
        return 1

    if len(writes) == 1:
        print("PASS: a single per-occurrence call — every index resolved against one read")
        return 0

    for earlier, later in zip(writes, writes[1:]):
        if not any(earlier < r < later for r in reads):
            print(
                f"FAIL: per-occurrence writes at {earlier} and {later} with no get-predictions between them — "
                "the second call reused indices the first one invalidated (Critical Rule 18)"
            )
            return 1

    print(f"PASS: {len(writes)} sequential per-occurrence calls, each preceded by a fresh read")
    return 0


if __name__ == "__main__":
    sys.exit(main())
