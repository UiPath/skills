#!/usr/bin/env python3
"""Grade the logging / PII-leakage review.

Planted (LoggingBot/Main.xaml): a Write Line instead of Log Message, and — the
CRITICAL defect — customer PII (email + SSN) written into Log Messages.

PASS REQUIRES a sentence that AFFIRMS PII is written to / exposed in the logs.
A clean denial ("Logs do not contain PII, sensitive data, SSNs, or personal
data") must fail — even though it names PII terms and 'log', the whole sentence
denies the leak. Prescriptive phrasing ("Never log SSNs", "SSNs should be
masked before logging") still counts as flagging.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from grader_common import report_text, asserts_any, fixture_contains  # noqa: E402

PROJECT = "LoggingBot"
PII = ("pii", "ssn", "social security", "sensitive data", "sensitive information",
       "personal data", "personally identifiable", "email address")
_EXPOSE = ("log", "writ", "output", "expos", "leak", "captured")
_DENIAL = re.compile(r"\b(no|not|n't|without|masked|redacted|scrubbed|sanitiz|obfuscat|"
                     r"excluded|omitted|stripped|filtered)\b")
_PRESCRIPTIVE = re.compile(r"(should not|must not|avoid|never|do not log|don't log|"
                           r"should (?:be )?mask|must (?:be )?mask|should (?:be )?redact|"
                           r"needs? to (?:be )?(?:mask|redact))")


def pii_logged(lower: str) -> bool:
    for sent in re.split(r"[.\n]", lower):
        if not any(p in sent for p in PII):
            continue
        if not any(e in sent for e in _EXPOSE):
            continue
        if _DENIAL.search(sent) and not _PRESCRIPTIVE.search(sent):
            continue  # declarative denial ("logs do not contain PII")
        return True
    return False


def main() -> None:
    text = report_text(500)
    lower = text.lower()

    if not fixture_contains(f"{PROJECT}/Main.xaml", "customerSSN"):
        sys.exit(f"FAIL: {PROJECT}/Main.xaml no longer logs the planted PII "
                 "(customerSSN) — fixture appears mutated.")

    if not pii_logged(lower):
        sys.exit("FAIL: report does not flag the Critical defect — customer PII "
                 "(email/SSN) written to the logs. A Write Line / log-level finding "
                 "alone, or a 'logs do not contain PII' denial, is not sufficient.")

    extra = []
    if asserts_any(text, ["write line", "writeline"], presence=True) or "ST-MRD-011" in text:
        extra.append("Write Line")
    if asserts_any(text, ["verbose"], presence=True) or "ST-USG-020" in text:
        extra.append("log level")
    print("OK: PII-in-logs leakage flagged" + (f"; also: {', '.join(extra)}" if extra else ""))
    print("PASS")


if __name__ == "__main__":
    main()
