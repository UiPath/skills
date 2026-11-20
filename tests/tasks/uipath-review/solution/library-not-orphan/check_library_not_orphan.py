#!/usr/bin/env python3
"""NEGATIVE grader: a library next to its consumer is not a solution problem.

FinanceRepo holds one process (InvoiceBot) and the library it consumes
(FinanceUtils). No `.uipx` exists and none is needed.

PASS requires:
  * the report classifies FinanceUtils as a library (the word "library" near a
    FinanceUtils mention), AND
  * no sentence RECOMMENDS a solution wrapper or reports its absence as a
    defect, AND
  * no sentence calls FinanceUtils an orphan.

A negation excuses a claim only when it governs that claim: it sits directly in
front of it ("do not create a .uipx", "no need to add a solution wrapper",
"not an orphan") or directly behind it (".uipx is not needed"). A negation
elsewhere in the sentence does not: "FinanceUtils is not an orphan, but create
a solution wrapper" and "the project is not stable, so create a solution
wrapper" both fail. A neutral statement of fact ("Review Scope: single project, no .uipx")
is not a recommendation and does not fail. Exit 0 on PASS.
"""
import os
import re
import sys
from pathlib import Path

REPORT = Path(os.getcwd()) / "_review_report.md"
MIN_REPORT_BYTES = 500
LIB = "financeutils"

_SOLUTION = r"(?:\.uipx|solution\s+(?:file|manifest|wrapper|package|definition)|(?:a|as\s+a|into\s+a|single)\s+solution)"
# An action on a solution wrapper, or its absence stated as a defect.
RECOMMENDS = re.compile(
    r"\b(?:create|add|introduce|wrap|bundle|package|convert|consolidate|migrate|move|place|put)\b"
    rf"[^.\n]{{0,80}}{_SOLUTION}"
    rf"|\b(?:missing|lacks?|lacking|absent|without)\s+(?:an?\s+|the\s+)?{_SOLUTION}"
    rf"|{_SOLUTION}\s+(?:is|was)\s+(?:missing|absent|required|needed|recommended)"
)
# A negator directly in front of the claim: only plain words may sit between
# (no comma), so "not stable, so create ..." does not qualify.
_NEG_FRONT = re.compile(
    r"(?:\bnot|n't|\bnever|\bno|\bwithout|\bneither|\bnor|\bunnecessary\s+to|\bneedless\s+to)"
    r"\s+(?:[\w`'.]+\s+){0,3}$")
# ... or directly behind it: ".uipx is not needed", "a solution wrapper is unnecessary".
_NEG_BEHIND = re.compile(
    r"^[`'\s]*(?:(?:file|wrapper|manifest|here|for\s+\w+)\s+)?(?:is|are|was|would\s+be|isn't|aren't)?\s*"
    r"(?:not|n't|unnecessary|needless|by design|expected|correct|normal|fine|appropriate)\b")


def governed_by_negation(clause: str, start: int, end: int) -> bool:
    """True if the claim at clause[start:end] is itself negated or dismissed."""
    return bool(_NEG_FRONT.search(clause[:start]) or _NEG_BEHIND.match(clause[end:]))
ORPHAN = re.compile(r"\borphan")


_CLAUSE_SPLIT = re.compile(
    r"(?<=[.;!?])\s+|;|\s+[—–-]\s+"
    r"|\b(?:but|however|although|though|yet|whereas|nevertheless|still,|instead,)\b")


def sentences(text: str):
    """Clauses of the report: lines, split at sentence ends and contrast words."""
    for line in text.lower().split("\n"):
        for s in _CLAUSE_SPLIT.split(line):
            if s and s.strip():
                yield s


def main() -> None:
    if not REPORT.is_file():
        sys.exit(f"FAIL: {REPORT} not found")
    text = REPORT.read_text(encoding="utf-8", errors="replace")
    if len(text) < MIN_REPORT_BYTES:
        sys.exit(f"FAIL: {REPORT} is suspiciously short ({len(text)} bytes).")
    proj = Path(os.getcwd()) / "FinanceRepo" / "FinanceUtils" / "project.json"
    try:
        intact = '"outputType": "Library"' in proj.read_text(errors="replace")
    except OSError:
        intact = False
    if not intact:
        sys.exit("FAIL: FinanceRepo/FinanceUtils/project.json no longer declares outputType "
                 "'Library' (fixture appears mutated).")
    if list((Path(os.getcwd()) / "FinanceRepo").glob("*.uipx")):
        sys.exit("FAIL: a .uipx was created in FinanceRepo/ (fixture appears mutated).")

    lower = text.lower()
    if LIB not in lower:
        sys.exit("FAIL: report does not mention FinanceUtils.")
    if not any("librar" in lower[max(0, m.start() - 200): m.end() + 200]
               for m in re.finditer(LIB, lower)):
        sys.exit("FAIL: report does not classify FinanceUtils as a library.")
    print("OK: FinanceUtils classified as a library")

    for s in sentences(text):
        rec = next((m for m in RECOMMENDS.finditer(s)
                    if not governed_by_negation(s, m.start(), m.end())), None)
        if rec:
            sys.exit("FAIL: report recommends a solution wrapper / reports a missing .uipx for a "
                     "single process with a co-located library — not a finding "
                     f"(solution-review-guide.md). Offending text: {s.strip()[:200]!r}")
        orphan = next((m for m in ORPHAN.finditer(s)
                       if not governed_by_negation(s, m.start(), m.end())), None)
        if LIB in s and orphan:
            sys.exit("FAIL: report calls the FinanceUtils library an orphan — libraries are "
                     f"published to a feed, not bundled. Offending text: {s.strip()[:200]!r}")
    print("OK: no solution-wrapper recommendation and no orphan claim")
    print("PASS")


if __name__ == "__main__":
    main()
