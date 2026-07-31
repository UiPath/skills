#!/usr/bin/env python3
"""Grade the coded-workflow structural review.

Planted in the entry CodedProc/Main.cs: (1) class does not inherit
CodedWorkflow, (2) Execute has no [Workflow] attribute, (3) an `out string
result` parameter (CS1620), (4) a hardcoded input path.

PASS requires the report to flag AT LEAST TWO of these AS problems. Praising
the correct helper workflows ("ReadExcelData correctly inherits CodedWorkflow")
does not count. The planted `out` parameter must still exist in the fixture.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from grader_common import report_text, asserts, asserts_any, fixture_contains  # noqa: E402

PROJECT = "CodedProc"


def main() -> None:
    text = report_text(500)
    lower = text.lower()

    if not fixture_contains(f"{PROJECT}/Main.cs", "out string result"):
        sys.exit(f"FAIL: {PROJECT}/Main.cs no longer declares the planted `out string "
                 "result` parameter (fixture appears mutated).")

    found = []
    # (1) missing CodedWorkflow base — a non-dismissed CodedWorkflow mention in an
    # inheritance context (kills "correctly inherits CodedWorkflow").
    if asserts(text, "codedworkflow", presence=False) and any(
        w in lower for w in ("inherit", "base class", "extend", "derive", "subclass")
    ):
        found.append("missing CodedWorkflow base")
    # (2) missing [Workflow] attribute — requires negative framing near it.
    if re.search(r"(missing|lacks?|without|absent|no|not (?:\w+\s+){0,2}(?:have|decorated))\s+"
                 r"(?:\w+\s+){0,3}\[?workflow\]?\s*attribute", lower) or (
                 "[workflow]" in lower and any(w in lower for w in ("missing", "absent", "lacks", "without"))):
        found.append("missing [Workflow] attribute")
    # (3) out/ref parameter (CS1620) — presence defect.
    if asserts_any(text, ["cs1620", "out param", "out parameter", "out/ref",
                          "ref param", "`out`", "out string", "out-parameter"], presence=True):
        found.append("out/ref parameter (CS1620)")
    # (4) hardcoded path.
    if (asserts(text, "hardcod", presence=True) and any(w in lower for w in ("path", "c:\\", "c:/", "in.csv", "invoices"))) \
            or r"c:\invoices" in lower:
        found.append("hardcoded path")

    if len(found) < 2:
        sys.exit(f"FAIL: report flags fewer than 2 coded-workflow defects as problems "
                 f"(found: {found or 'none'}). Need >=2 of: missing CodedWorkflow base, "
                 "missing [Workflow] attribute, out/ref param (CS1620), hardcoded path.")
    print(f"OK: report flags {len(found)} defect(s): {', '.join(found)}")
    print("PASS")


if __name__ == "__main__":
    main()
