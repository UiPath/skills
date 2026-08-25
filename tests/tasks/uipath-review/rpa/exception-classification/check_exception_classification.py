#!/usr/bin/env python3
"""Grade the exception-classification review.

Planted (ExceptionBot/Main.xaml): a Catch that does `throw new
Exception(ex.Message)` (destroys the stack trace, should Rethrow) and a
`ContinueOnError=True` file op that swallows failures.

PASS requires the report to flag AT LEAST ONE of the two concrete defects AS a
problem. A clean report ("does not throw new Exception, preserves the stack
trace, ContinueOnError is not used") must fail: preserving the stack trace and
not using ContinueOnError describe healthy code, so they are not credited.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from grader_common import report_text, asserts, asserts_any, fixture_contains  # noqa: E402

PROJECT = "ExceptionBot"
# Stack trace is the DESIRABLE thing — only a loss framing is a defect.
_STACK_LOSS = re.compile(
    r"(los[et]|losing|destroy|discard|drop|reset|wipe|overwrit|swallow)\w*\s+(?:the\s+)?"
    r"(?:original\s+)?stack[\s-]?trace"
    r"|stack[\s-]?trace\s+(?:is|are|gets?|will be|being|becomes?)\s+"
    r"(?:lost|destroyed|discarded|dropped|reset|wiped|overwritten)")


def main() -> None:
    text = report_text(500)
    lower = text.lower()

    if not fixture_contains(f"{PROJECT}/Main.xaml", "new Exception(exception.Message)"):
        sys.exit(f"FAIL: {PROJECT}/Main.xaml no longer contains the planted "
                 "`new Exception(exception.Message)` (fixture appears mutated).")

    found = []
    # Stack-trace loss: should Rethrow (absence) / throw-new anti-pattern present /
    # explicit stack-trace-loss framing. NOT bare "stack trace" (that is healthy).
    if asserts(text, "rethrow", presence=False) \
            or asserts_any(text, ["throw new exception", "throw new"], presence=True) \
            or _STACK_LOSS.search(lower):
        found.append("stack-trace loss (Rethrow)")
    if asserts_any(text, ["continueonerror", "continue on error", "ui-ana-017"], presence=True):
        found.append("ContinueOnError misuse")
    if asserts_any(text, ["businessruleexception", "business rule exception",
                          "business vs system", "business exception"], presence=True):
        found.append("business-vs-system classification")

    if not found:
        sys.exit("FAIL: report does not flag any exception-handling defect as a problem — "
                 "expected the stack-trace loss (Rethrow) or the ContinueOnError misuse.")
    print(f"OK: report flags: {', '.join(found)}")
    print("PASS")


if __name__ == "__main__":
    main()
