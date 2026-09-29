#!/usr/bin/env python3
"""Grade one strategy-selection row.

Reads `strategy.txt` from the working directory and compares the strategy the agent
picked against this row's ground truth, supplied as --expected.

Exit 0 = the selected strategy matches. Exit 1 = anything else.
"""
import argparse
import pathlib
import re
import sys

# NONE is no longer an expected label — the deterministic rows were removed from
# the set and the prompt no longer offers it. It stays recognised so that an agent
# that reaches for it anyway is reported as "selected NONE, ground truth X", which
# says the model thought the workload left the taxonomy. Dropping it would collapse
# that into an indistinguishable "not a valid strategy" alongside genuine garbage.
STRATEGIES = ("AH", "AF", "CS", "SU", "PS", "PA", "EX", "BT", "NONE")


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expected", required=True)
    args = ap.parse_args()

    expected = args.expected.strip().upper()
    if not expected or expected.startswith("${"):
        # The harness did not substitute the row field. Fail loudly rather than
        # silently grading against a literal template string.
        return fail(
            f"--expected was not interpolated by the harness (got {args.expected!r}). "
            "Row-field substitution inside a run_command command string is required "
            "by this task; see the task description."
        )
    if expected not in STRATEGIES:
        return fail(f"--expected {expected!r} is not one of {STRATEGIES}")

    path = pathlib.Path("strategy.txt")
    if not path.is_file():
        return fail("strategy.txt was not produced")

    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return fail("strategy.txt is empty")

    # Accept the bare token on its own line, tolerating surrounding punctuation
    # and a trailing explanation on later lines.
    first = text.splitlines()[0].strip()
    token = re.sub(r"[^A-Za-z]", "", first).upper()

    if token not in STRATEGIES:
        return fail(
            f"first line of strategy.txt is {first!r}, which is not one of {STRATEGIES}. "
            "The first line must be the strategy ID alone."
        )

    if token != expected:
        print(f"FAIL: selected {token}, ground truth {expected}", file=sys.stderr)
        return 1

    print(f"PASS: selected {token}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
