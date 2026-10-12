#!/usr/bin/env python3
"""Grade one routing row against the case library's ground truth.

Reads `routing.txt` from the working directory, takes the strategy from its first
non-empty line, and compares it to --expected.

Exit 0 = match. Exit 1 = anything else, with the reason on stderr.
"""
import argparse
import pathlib
import re
import sys

STRATEGIES = ("AH", "AF", "CS", "SU", "PS", "EX", "BT")
# NONE and PA are recognised but never expected: NONE so an agent that reaches for
# it is reported as "selected NONE" rather than "unparseable", PA because agentic
# search is withheld from this release and a stale answer should be legible.
STRATEGY_ANSWERS = STRATEGIES + ("NONE", "PA")

ANSWER_FILE = pathlib.Path("routing.txt")
KEY = re.compile(r"^\s*(?:strategy\s*[:=]\s*)?([A-Za-z]+)", re.I)


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    return 1


def expect(flag, raw, vocab):
    """Row-field guard. If the harness did not substitute ${row.*} into the
    run_command string, fail loudly rather than grade against a literal template.
    Both row fields are guarded on every invocation, not just the graded one: a task
    that interpolates one and not the other is broken either way, and the axis that
    happened to work must not pass."""
    value = (raw or "").strip()
    if not value or value.startswith("${"):
        return None, fail(
            f"{flag} was not interpolated by the harness (got {raw!r}). Row-field "
            "substitution inside a run_command command string is required by this "
            "task; see the task description."
        )
    if value not in vocab:
        return None, fail(f"{flag} {value!r} is not one of {vocab}")
    return value, 0


def parse_answer():
    """The strategy is the first non-empty line. A bare token is accepted, as is
    `strategy: EX`. Only the first line is read — prose below it is free text and
    must not be able to change the graded answer."""
    if not ANSWER_FILE.is_file():
        return None, fail("routing.txt was not produced")
    lines = [l for l in ANSWER_FILE.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    if not lines:
        return None, fail("routing.txt is empty")
    m = KEY.match(lines[0])
    if not m:
        return None, fail(f"could not read a strategy from the first line: {lines[0]!r}")
    return m.group(1).upper(), 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expected", required=True)
    args = ap.parse_args()

    want, rc = expect("--expected", args.expected, STRATEGIES)
    if rc:
        return rc
    got, rc = parse_answer()
    if rc:
        return rc
    if got not in STRATEGY_ANSWERS:
        return fail(f"strategy is {got!r}, not one of {STRATEGY_ANSWERS}")
    if got != want:
        return fail(f"selected strategy {got}, ground truth {want}")
    print(f"PASS: strategy {got}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
