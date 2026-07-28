#!/usr/bin/env python3
"""Grade the selector-brittle review.

Planted (real desktop UI automation): the primary Type Into selectors were
made positional idx-only (`<ctrl idx='3' />...`) instead of the stable
automationid capture. PASS requires the report to flag the selector fragility
AS a problem (a UI-* rule code the skill teaches, or prose about idx /
positional / brittle selectors). "Selectors are robust" does not count. The
planted idx selector must still exist in the fixture.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from grader_common import report_text, asserts_any, fixture_contains  # noqa: E402

PROJECT = "BrittleBot"
RULE_CODES = ("UI-REL-001", "UI-DBP-030", "UI-ANA-016")
FRAGILE = ("idx", "brittle", "fragile", "positional", "position-based", "position based",
           "absolute selector", "full selector", "full-path", "unstable selector",
           "hardcoded selector", "index-based", "index based")


def main() -> None:
    text = report_text(500)
    lower = text.lower()

    if not fixture_contains(f"{PROJECT}/Main.xaml", "idx='3'"):
        sys.exit(f"FAIL: {PROJECT}/Main.xaml no longer contains the planted idx-only "
                 "selector (fixture appears mutated).")

    cited = [c for c in RULE_CODES if c in text]
    if cited:
        print(f"OK: report cites selector rule code(s): {cited}")
    elif ("selector" in lower or "target" in lower) and asserts_any(text, FRAGILE, presence=True):
        print("OK: report flags the brittle / positional selector in prose")
    else:
        sys.exit("FAIL: report does not flag the brittle selector as a problem — expected "
                 "a UI-* selector rule code or prose about an idx/positional/brittle selector.")
    print("PASS")


if __name__ == "__main__":
    main()
