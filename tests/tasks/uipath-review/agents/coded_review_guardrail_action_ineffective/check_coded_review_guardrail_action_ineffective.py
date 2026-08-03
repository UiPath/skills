#!/usr/bin/env python3
"""Check for CODED_GUARDRAIL_ACTION_INEFFECTIVE — the coded agent's PII guardrail
uses `LogAction`, which records but does not stop PII from reaching the LLM.

A `command_executed` gate in the task YAML proves the reviewer fetched the live
catalog (Audit Mode). This check confirms the report surfaced the actionability
defect, accepting:

  1. the rule_id `CODED_GUARDRAIL_ACTION_INEFFECTIVE` carried verbatim (preferred), OR
  2. prose identifying the log-vs-block ineffectiveness of the PII guardrail.

Exit 0 on PASS; sys.exit on failure.
"""
import os
import re
import sys
from pathlib import Path

REPORT = Path(os.getcwd()) / "_review_report.md"
REQUIRED_RULE_ID = "CODED_GUARDRAIL_ACTION_INEFFECTIVE"
# Prose form: an ineffectiveness cue tied to the log-not-block action.
INEFFECTIVE_PHRASES = (
    "ineffective",
    "does not block",
    "doesn't block",
    "does not prevent",
    "doesn't prevent",
    "only logs",
    "log instead of block",
    "log rather than block",
    "should block",
    "use a blocking action",
    "blockaction",
    "log-only",
    "log only",
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
    has_prose = ("pii" in low or "guardrail" in low) and any(p in low for p in INEFFECTIVE_PHRASES)

    if has_rule_id:
        print(f"OK: report cites `{REQUIRED_RULE_ID}`")
    elif has_prose:
        print("OK: report identifies the PII guardrail's log action as ineffective (block needed)")
    else:
        sys.exit(
            f"FAIL: report neither cites `{REQUIRED_RULE_ID}` nor identifies the "
            "PII guardrail's log-not-block ineffectiveness."
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
