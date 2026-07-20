#!/usr/bin/env python3
"""E2E grader: solution-wide review of RetailSolution (Dispatcher + Performer).

Planted:
  - Dispatcher/Main.xaml : brittle idx selector + hardcoded prod URL / queue name
  - Performer/Main.xaml   : hardcoded finance password (Critical), swallowed
    System.Exception / no Rethrow (Critical)

PASS requires: report >= 800 bytes; both projects named; both severity bands;
a Performer Critical flagged AS a problem (credential or swallowed exception);
and a Dispatcher issue flagged (brittle selector or hardcoded URL/queue) — so
the review must cover BOTH projects. The planted Performer secret must survive.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from grader_common import report_text, asserts, asserts_any, fixture_contains  # noqa: E402

PROJECT = "RetailSolution"


def performer_critical(text, lower):
    cred = (asserts_any(text, ["hardcod", "plaintext", "plain text"], presence=True)
            and any(k in lower for k in ("password", "credential", "secret"))) \
        or bool(re.search(r"(should|must|missing|instead|convert|store\b|needs?\s+to|use)\s+"
                          r"(?:\w+\s+){0,4}secure\s?string", lower))
    swallowed = asserts_any(text, ["swallow", "marked success", "marked as success",
                                   "reported as success", "treated as success"], presence=True) \
        or asserts(text, "rethrow", presence=False)
    return cred or swallowed


def dispatcher_issue(text, lower):
    selector = "selector" in lower and asserts_any(
        text, ["idx", "brittle", "fragile", "positional", "position-based", "unstable"], presence=True)
    hardcoded_env = asserts_any(text, ["hardcod", "hard-cod"], presence=True) and any(
        w in lower for w in ("url", "queue", "vendor-prod", "invoicequeue"))
    return selector or hardcoded_env


def main() -> None:
    text = report_text(800)
    lower = text.lower()

    if not fixture_contains(f"{PROJECT}/Performer/Main.xaml", "Fin@nce_FAKE_2024"):
        sys.exit(f"FAIL: {PROJECT}/Performer/Main.xaml no longer contains the planted "
                 "(fake) credential (fixture appears mutated).")

    if "Dispatcher" not in text or "Performer" not in text:
        sys.exit("FAIL: report does not name both projects (Dispatcher AND Performer).")

    crit = len(re.findall(r"critical", text, re.IGNORECASE))
    warn = len(re.findall(r"warning", text, re.IGNORECASE))
    if crit < 1 or warn < 1:
        sys.exit(f"FAIL: report must use both severity bands (Critical={crit}, Warning={warn}).")

    if not performer_critical(text, lower):
        sys.exit("FAIL: report does not flag a Performer Critical (hardcoded credential "
                 "or swallowed exception) as a problem.")
    if not dispatcher_issue(text, lower):
        sys.exit("FAIL: report does not flag a Dispatcher issue (brittle selector or "
                 "hardcoded URL/queue) — it must review BOTH projects.")

    print(f"OK: both projects named; Critical={crit}, Warning={warn}; Performer + Dispatcher flagged")
    print("PASS")


if __name__ == "__main__":
    main()
