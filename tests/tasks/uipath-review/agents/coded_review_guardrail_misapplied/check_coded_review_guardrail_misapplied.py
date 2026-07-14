#!/usr/bin/env python3
"""Check for CODED_GUARDRAIL_MISAPPLIED — a synthetic-data generator agent (never
receives real PII) carries a `pii_detection` guardrail, matching the catalog's
`when_not_to_use`.

A `command_executed` gate in the task YAML proves the reviewer fetched the live
catalog (Audit Mode → Relevance). This check confirms the report surfaced the
relevance defect, accepting:

  1. the rule_id `CODED_GUARDRAIL_MISAPPLIED` carried verbatim (preferred), OR
  2. prose identifying the PII guardrail as inappropriate / unnecessary for a
     synthetic-data generator (it never receives real PII).

Exit 0 on PASS; sys.exit on failure.
"""
import os
import re
import sys
from pathlib import Path

REPORT = Path(os.getcwd()) / "_review_report.md"
REQUIRED_RULE_ID = "CODED_GUARDRAIL_MISAPPLIED"
# Prose form: a misapplication cue, tied to the guardrail.
MISAPPLIED_PHRASES = (
    "misapplied",
    "does not belong",
    "doesn't belong",
    "not appropriate",
    "inappropriate",
    "adds no protection",
    "no protection",
    "unnecessary",
    "not needed",
    "should be removed",
    "when_not_to_use",
    "when not to use",
    "never receives real",
    "never sees real",
)
MIN_REPORT_BYTES = 500

NOISE = {
    "JSON", "YAML", "TOML", "XAML", "BPMN", "PDD", "SDD", "UUID", "HTTP",
    "HTTPS", "REST", "API", "CLI", "SDK", "NULL", "TRUE", "FALSE", "TODO",
    "FIXME", "WIP", "README",
}


def main() -> None:
    if not REPORT.is_file():
        sys.exit(f"FAIL: {REPORT} not found")
    text = REPORT.read_text(encoding="utf-8", errors="replace")
    if len(text) < MIN_REPORT_BYTES:
        sys.exit(f"FAIL: {REPORT} is suspiciously short ({len(text)} bytes).")

    low = text.lower()
    has_rule_id = REQUIRED_RULE_ID in text
    has_prose = ("pii" in low or "guardrail" in low) and any(p in low for p in MISAPPLIED_PHRASES)

    if has_rule_id:
        print(f"OK: report cites `{REQUIRED_RULE_ID}`")
    elif has_prose:
        print("OK: report identifies the PII guardrail as misapplied on the synthetic-data generator")
    else:
        sys.exit(
            f"FAIL: report neither cites `{REQUIRED_RULE_ID}` nor identifies the "
            "PII guardrail as misapplied on a synthetic-data generator."
        )

    skills_repo = os.environ.get("SKILLS_REPO_PATH")
    if skills_repo:
        catalog_dir = Path(skills_repo) / "skills" / "uipath-review" / "references" / "agents"
        if catalog_dir.is_dir():
            catalog_text = "".join(
                f.read_text(encoding="utf-8", errors="replace")
                for f in sorted(catalog_dir.glob("agents-*-rules.md"))
            )
            unknown = sorted(
                c for c in set(re.findall(r"`([A-Z][A-Z0-9_]{4,})`", text)) - NOISE
                if c not in catalog_text
            )
            if unknown:
                print(f"WARN: rule_id(s) not in the judgment catalog (may be CLI-emitted): {unknown}")
    print("PASS")


if __name__ == "__main__":
    main()
