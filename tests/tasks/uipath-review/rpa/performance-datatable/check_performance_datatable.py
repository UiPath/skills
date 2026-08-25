#!/usr/bin/env python3
"""Grade the performance review.

Planted (PerfBot/Main.xaml): a nested For Each Row over two DataTables (O(n*m)),
a Log Message inside the inner loop, and a hardcoded 30s Delay used as a wait.

PASS requires the report to flag AT LEAST ONE performance defect AS a problem
(nested-loop / quadratic, hardcoded Delay, or logging-in-a-tight-loop), via
prose or a rule code. "No performance issues" does not count. The planted Delay
must still exist in the fixture.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from grader_common import report_text, asserts, asserts_any, fixture_contains  # noqa: E402

PROJECT = "PerfBot"


def main() -> None:
    text = report_text(500)
    lower = text.lower()

    if not fixture_contains(f"{PROJECT}/Main.xaml", "00:00:30"):
        sys.exit(f"FAIL: {PROJECT}/Main.xaml no longer contains the planted hardcoded "
                 "30s Delay (fixture appears mutated).")

    found = []
    if asserts_any(text, ["nested loop", "nested for each", "nested for-each", "quadratic",
                          "o(n^2)", "o(n2)", "o(n*m)", "o(nm)", "n^2", "join instead",
                          "lookup dictionary", "cartesian"], presence=True):
        found.append("nested-loop / quadratic")
    if any(c in text for c in ("ST-DBP-026", "ST-PRR-004", "UI-PRR-004")) or (
        asserts(text, "delay", presence=True)
        and any(w in lower for w in ("hardcod", "hard-cod", "fixed", "static", "dynamic wait", "instead of"))
    ):
        found.append("hardcoded Delay")
    if ("log" in lower and "loop" in lower) and asserts_any(
        text, ["tight", "inside the loop", "each iteration", "per iteration", "excessive"], presence=True
    ):
        found.append("logging in tight loop")

    if not found:
        sys.exit("FAIL: report does not flag a performance defect as a problem — expected the "
                 "nested-loop / quadratic matching, the hardcoded Delay, or logging in a loop.")
    print(f"OK: report flags: {', '.join(found)}")
    print("PASS")


if __name__ == "__main__":
    main()
