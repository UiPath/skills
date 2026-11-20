#!/usr/bin/env python3
"""Data-driven grader for single-defect review tasks.

Each task plants ONE unambiguous defect in a fixture and asks for a review. The
task YAML states what the report must say through arguments, so twenty tasks
share one tested matcher instead of twenty hand-rolled copies.

    python3 $REFERENCE_DIR/_shared/check_planted_defect.py \
        --marker "Sol/Sol.uipx::ClaimsPayout" \
        --subject "ClaimsAudit" \
        --flag-absence "orphan|not listed|not registered"

Arguments
  --marker PATH::NEEDLE   Fixture file (relative to the sandbox cwd) must still
                          contain NEEDLE. Repeatable. Guards against an agent
                          that edits the defect away through the shell.
  --marker-absent PATH    Path must still NOT exist (defects that are a missing
                          file or directory). Repeatable.
  --subject A|B           The report must name at least one of these literals
                          (case-insensitive). When given, every flag group is
                          evaluated only in the text around a subject mention,
                          so a defect term elsewhere in the report cannot pass.
  --flag T1|T2            A group of terms for a defect that is PRESENT in the
                          code. Passes when any term is framed as a problem;
                          "no hardcoded credential" does not count. Repeatable:
                          every group must pass.
  --flag-absence T1|T2    Same, for a defect that IS an absence ("not listed",
                          "missing"), where a negation is the finding itself.
  --mention T1|T2         Plain case-insensitive mention anywhere in the report
                          (no problem framing). Repeatable.
  --near N                Characters kept on each side of a subject mention
                          (default 500).
  --min-bytes N           Minimum report size (default 500).

Exit 0 on PASS. Every FAIL names the unmet requirement.
"""
import argparse
import os
import sys
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "rpa", "_shared"))
from grader_common import report_text, asserts_any  # noqa: E402


def _terms(group: str) -> list:
    return [t.strip() for t in group.split("|") if t.strip()]


def _scope(text: str, subjects: list, near: int) -> str:
    """Text around every subject mention, or the whole report with no subject."""
    if not subjects:
        return text
    lower = text.lower()
    parts = []
    for s in subjects:
        s = s.lower()
        start = 0
        while True:
            i = lower.find(s, start)
            if i == -1:
                break
            parts.append(text[max(0, i - near): i + len(s) + near])
            start = i + len(s)
    return "\n".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--marker", action="append", default=[])
    ap.add_argument("--marker-absent", action="append", default=[])
    ap.add_argument("--subject", default="")
    ap.add_argument("--flag", action="append", default=[])
    ap.add_argument("--flag-absence", action="append", default=[])
    ap.add_argument("--mention", action="append", default=[])
    ap.add_argument("--near", type=int, default=500)
    ap.add_argument("--min-bytes", type=int, default=500)
    a = ap.parse_args()

    text = report_text(a.min_bytes)
    cwd = Path(os.getcwd())

    for m in a.marker:
        rel, _, needle = m.partition("::")
        p = cwd / rel
        try:
            ok = p.is_file() and needle in p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            ok = False
        if not ok:
            sys.exit(f"FAIL: {rel} no longer contains the planted marker {needle!r} "
                     "(fixture appears mutated).")
    for rel in a.marker_absent:
        if (cwd / rel).exists():
            sys.exit(f"FAIL: {rel} now exists — the planted defect is its absence "
                     "(fixture appears mutated).")

    subjects = _terms(a.subject)
    if subjects and not any(s.lower() in text.lower() for s in subjects):
        sys.exit(f"FAIL: report does not name the affected item (expected one of {subjects}).")
    scope = _scope(text, subjects, a.near)
    where = f" near {subjects}" if subjects else ""

    for group in a.flag:
        if not asserts_any(scope, _terms(group), presence=True):
            sys.exit(f"FAIL: report does not flag the defect as a problem{where} — "
                     f"expected one of {_terms(group)}.")
    for group in a.flag_absence:
        if not asserts_any(scope, _terms(group), presence=False):
            sys.exit(f"FAIL: report does not flag the defect as a problem{where} — "
                     f"expected one of {_terms(group)}.")
    for group in a.mention:
        if not any(t.lower() in text.lower() for t in _terms(group)):
            sys.exit(f"FAIL: report does not mention any of {_terms(group)}.")

    print("OK: planted defect identified" + where)
    print("PASS")


if __name__ == "__main__":
    main()
