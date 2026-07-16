#!/usr/bin/env python3
"""Shared helpers for the uipath-review RPA grader scripts.

Imported by each `check_*.py` via:

    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
    from grader_common import report_text, asserts, count_asserted, fixture_contains

Two robustness guarantees these helpers provide over plain substring matching:

1. `asserts()` — a defect term only counts when it is framed AS A PROBLEM, not
   when the report DISMISSES it. "Main does not inherit CodedWorkflow" counts;
   "ReadExcelData correctly inherits CodedWorkflow" and "no duplicate risk" do
   NOT. This stops an explicitly-wrong "no issues" review from passing.

2. `fixture_contains()` — lets a grader assert the planted-defect marker is
   still present in the reviewed project (read from the sandbox cwd). If an
   agent mutated the fixture (e.g. via a shell command that the Write/Edit
   read-only guards don't see) to remove the defect, the marker check fails.
"""
import os
import re
import sys
from pathlib import Path

# Contexts around a defect term that mean it is NOT being flagged as a problem
# (the report says that aspect is fine / correct / absent-as-a-non-issue).
# Structural problem-dismissals — the report says that aspect is fine / not a
# problem. Phrase-anchored, so they don't fire on unrelated text.
_STRUCT_DISMISS = re.compile(
    r"(no (?:\w+\s+){0,2}(issues?|problems?|concerns?|risks?|defects?|violations?)|"
    r"not (?:\w+\s+){0,2}(issue|problem|concern|risk|defect)|"
    r"no longer an? (issue|problem|concern)|looks good|is fine|are fine|"
    r"no action|nothing to (flag|report|fix)|is compliant)"
)

# Positive quality affirmations ("...is correct / robust / acceptable / handled
# properly"). These count as a dismissal ONLY when not negated, so a strong
# review saying "this is not acceptable" / "idx selector is not robust" still
# flags the problem.
# \b so we don't match the stem inside a NEGATIVE word — "unacceptable",
# "incorrectly", "inadequate", "improper" have no word boundary before the
# stem, so they are not read as praise.
_QUALITY = re.compile(
    r"\b(correctl|properl|adequat|robust|acceptabl|well[- ]?structured|"
    r"masked|redacted|scrubbed|sanitiz|obfuscat|"
    r"handled (?:correct|proper|well))"
)
_NEG_QUALITY = re.compile(
    r"\b(not|n't|isn't|aren't|never|hardly|far from|no|lacks?|without|fails? to|failed to)\b"
    r"(?:\s+\w+){0,2}\s*$"
)

# Factual absence of a PRESENCE defect right before the term ("password is
# not hardcoded", "no hardcoded credential", "logs do not contain PII" → the
# defect is absent / code is clean). Includes factual negations (no/not/n't/
# without/lacks/free of) but NOT prescriptive words (avoid/never), which FLAG a
# present defect being advised against ("Avoid hardcoded URLs", "Never log SSNs").
_NEG_BEFORE = re.compile(
    r"(?:\bno\b|\bnot\b|n't|\bwithout\b|\bfree of\b|\blacks?\b)\s+(?:\w+[\s,]+){0,3}$"
)
# Declarative negation just AFTER the term ("ContinueOnError is not used",
# "the selector is not brittle" is handled before; here e.g. "<term> is not ...").
_NEG_AFTER = re.compile(r"^(?:\s+\w+){0,2}\s+(?:is|are|was|were)\s*(?:not|n't)\b")

# PRESCRIPTIVE / prohibition framing — the defect is present and advised
# against, so it FLAGS even though a negation is nearby. "avoid hardcoded",
# "should not hardcode", "never log SSNs", and clause-initial "Do not hardcode"
# (but NOT declarative "logs do not contain PII", where "do not" is mid-clause).
_PRESCRIPTIVE = re.compile(
    r"(avoid|never|should not|shouldn't|must not|mustn't|instead of|externaliz|"
    r"move (?:it|them|these|this)?\s*to|replace|should use|must use|rather than|"
    r"(?:^|[.:;•\-]\s*)(?:do not|don't)\b)"
)


def _dismissed(window: str) -> bool:
    if _STRUCT_DISMISS.search(window):
        return True
    for m in _QUALITY.finditer(window):
        pre = window[max(0, m.start() - 18): m.start()]
        if not _NEG_QUALITY.search(pre):
            return True  # a *positive* quality affirmation → dismissal
    return False


def report_text(min_bytes: int = 500) -> str:
    """Read ./_review_report.md from the sandbox cwd; exit on missing/short."""
    report = Path(os.getcwd()) / "_review_report.md"
    if not report.is_file():
        sys.exit(f"FAIL: {report} not found")
    text = report.read_text(encoding="utf-8", errors="replace")
    if len(text) < min_bytes:
        sys.exit(f"FAIL: {report} is suspiciously short ({len(text)} bytes, need {min_bytes}).")
    return text


def asserts(text: str, term: str, presence: bool = True, window: int = 70) -> bool:
    """True if `term` appears at least once framed as a real problem.

    A match is rejected when the PROBLEM is dismissed (``_DISMISS``), and — for
    ``presence=True`` defects (the defect is something present in the code, e.g.
    a hardcoded credential) — when the term itself is directly negated
    ("no hardcoded credential"). For ``presence=False`` defects (the finding IS
    the absence, e.g. "no idempotency key", "missing [Workflow]") that direct
    negation is the finding, so only the problem-dismissal filter applies."""
    lower = text.lower()
    t = term.lower()
    start = 0
    while True:
        i = lower.find(t, start)
        if i == -1:
            return False
        w = lower[max(0, i - window): i + len(t) + window]
        pre = lower[max(0, i - 40): i]
        post = lower[i + len(t): i + len(t) + 40]
        neg = _NEG_BEFORE.search(pre) or _NEG_AFTER.search(post)
        dismissed = _dismissed(w) or (presence and neg and not _PRESCRIPTIVE.search(w))
        if not dismissed:
            return True
        start = i + len(t)


def asserts_any(text: str, terms, presence: bool = True) -> bool:
    return any(asserts(text, t, presence) for t in terms)


def count_asserted(text: str, terms, presence: bool = True) -> int:
    """Number of the given terms asserted as a problem at least once."""
    return sum(1 for t in terms if asserts(text, t, presence))


def fixture_contains(relpath: str, needle: str) -> bool:
    """True if the fixture file at `relpath` (relative to the sandbox cwd) still
    contains `needle` — used to confirm the planted defect was not edited away."""
    p = Path(os.getcwd()) / relpath
    try:
        return p.is_file() and needle in p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
