#!/usr/bin/env python3
"""E2E grader: comprehensive review of the RefxFull REFramework performer.

Planted across workflows:
  - Framework/System1_Login.xaml : hardcoded SAP password (Critical), brittle
    idx selector (Warning)
  - Framework/Process.xaml        : swallowed System.Exception / no Rethrow
    (Critical), Write Line (Info)

Grades BREADTH + severity discipline. PASS requires ALL:
  1. report >= 800 bytes
  2. both severity bands used (>=1 Critical AND >=1 Warning)
  3. the hardcoded credential flagged as a problem
  4. the swallowed system exception flagged
  5. >= 3 of the 4 planted categories flagged (credential, swallowed
     exception, brittle selector, Write Line)
There is NO double-retry here (Config MaxRetryNumber = 0 template default), so
it is not an accepted category — breadth cannot be padded with a non-defect.
The planted credential must still exist in the sandbox fixture.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from grader_common import report_text, asserts, asserts_any, fixture_contains  # noqa: E402

PROJECT = "RefxFull"


def has_credential(text, lower):
    if asserts_any(text, ["hardcoded", "plaintext", "plain text", "in clear"], presence=True) \
            and any(k in lower for k in ("password", "credential", "secret")):
        return True
    # SecureString is the fix — count only when recommended, not when claimed used.
    return bool(re.search(r"(should|must|missing|instead|convert|store\b|needs?\s+to|use)\s+"
                          r"(?:\w+\s+){0,4}secure\s?string", lower))


def has_swallowed(text):
    return asserts_any(text, ["swallow", "marked success", "marked as success",
                              "reported as success", "treated as success",
                              "considered successful"], presence=True) \
        or asserts(text, "rethrow", presence=False)


def has_selector(text, lower):
    return "selector" in lower and asserts_any(
        text, ["idx", "brittle", "fragile", "positional", "position-based",
               "absolute selector", "unstable"], presence=True)


def has_writeline(text):
    return asserts_any(text, ["write line", "writeline"], presence=True) or "ST-MRD-011" in text


def main() -> None:
    text = report_text(800)
    lower = text.lower()

    if not fixture_contains(f"{PROJECT}/Framework/System1_Login.xaml", "Sap#Prod_FAKE_2024"):
        sys.exit(f"FAIL: {PROJECT}/Framework/System1_Login.xaml no longer contains the "
                 "planted hardcoded credential (fixture appears mutated).")

    crit = len(re.findall(r"critical", text, re.IGNORECASE))
    warn = len(re.findall(r"warning", text, re.IGNORECASE))
    if crit < 1 or warn < 1:
        sys.exit(f"FAIL: report must use both severity bands (Critical={crit}, Warning={warn}).")

    if not has_credential(text, lower):
        sys.exit("FAIL: report does not flag the hardcoded SAP credential (Critical).")
    if not has_swallowed(text):
        sys.exit("FAIL: report does not flag the swallowed system exception in Process.xaml.")

    cats = {
        "credential": True,
        "swallowed-exception": True,
        "brittle-selector": has_selector(text, lower),
        "write-line": has_writeline(text),
    }
    hit = [k for k, v in cats.items() if v]
    if len(hit) < 3:
        sys.exit(f"FAIL: e2e review too shallow — only {len(hit)} categories: {hit}. Need >=3.")

    print(f"OK: Critical={crit}, Warning={warn}; categories: {hit}")
    print("PASS")


if __name__ == "__main__":
    main()
