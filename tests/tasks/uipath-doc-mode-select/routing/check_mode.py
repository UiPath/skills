#!/usr/bin/env python3
"""Grade one mode-selection row.

Reads `mode.txt` from the working directory and compares the mode the agent
picked against this row's ground truth, supplied as --expected.

Exit 0 = the selected mode matches. Exit 1 = anything else.
"""
import argparse
import pathlib
import re
import sys

# NONE is a real answer: the workload is deterministic and belongs in a Data,
# Transform or Script node, outside the document-mode taxonomy entirely.
MODES = ("AH", "AF", "CS", "SU", "PS", "PA", "EX", "BT", "NONE")


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
    if expected not in MODES:
        return fail(f"--expected {expected!r} is not one of {MODES}")

    path = pathlib.Path("mode.txt")
    if not path.is_file():
        return fail("mode.txt was not produced")

    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return fail("mode.txt is empty")

    # Accept the bare token on its own line, tolerating surrounding punctuation
    # and a trailing explanation on later lines.
    first = text.splitlines()[0].strip()
    token = re.sub(r"[^A-Za-z]", "", first).upper()

    if token not in MODES:
        return fail(
            f"first line of mode.txt is {first!r}, which is not one of {MODES}. "
            "The first line must be the mode ID alone."
        )

    if token != expected:
        print(f"FAIL: selected {token}, ground truth {expected}", file=sys.stderr)
        return 1

    print(f"PASS: selected {token}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
