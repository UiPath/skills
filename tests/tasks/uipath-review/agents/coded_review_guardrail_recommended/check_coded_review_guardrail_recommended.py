#!/usr/bin/env python3
"""Check for CODED_GUARDRAIL_RECOMMENDED — the coded agent handles PII (email,
ssn) and takes free-text input but wires no guardrail, so the reviewer should
recommend one (Recommend Mode, catalog-driven).

A `command_executed` gate in the task YAML proves the reviewer fetched the live
catalog. This check confirms the report surfaced a recommendation, accepting:

  1. the rule_id `CODED_GUARDRAIL_RECOMMENDED` carried verbatim (preferred), OR
  2. prose recommending a guardrail for the PII / injection exposure.

Exit 0 on PASS; sys.exit on failure.
"""
import os
import re
import sys
from pathlib import Path

REPORT = Path(os.getcwd()) / "_review_report.md"
REQUIRED_RULE_ID = "CODED_GUARDRAIL_RECOMMENDED"
# Prose form: a recommendation phrase + a guardrail/PII/injection cue.
RECOMMEND_PHRASES = ("recommend", "should add", "consider adding", "add a guardrail", "missing guardrail")
TOPIC_PHRASES = ("guardrail", "pii", "personal data", "prompt injection", "prompt_injection")
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
    has_prose = any(r in low for r in RECOMMEND_PHRASES) and any(t in low for t in TOPIC_PHRASES)

    if has_rule_id:
        print(f"OK: report cites `{REQUIRED_RULE_ID}`")
    elif has_prose:
        print("OK: report recommends a guardrail for the PII / injection exposure")
    else:
        sys.exit(
            f"FAIL: report neither cites `{REQUIRED_RULE_ID}` nor recommends a "
            "guardrail for the PII / injection exposure."
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
