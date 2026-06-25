#!/usr/bin/env python3
"""Check for the content-safety flavor of LC_GUARDRAIL_RECOMMENDED — a
content-generating agent (marketing copywriter, open-ended output) has no
content-safety guardrail, so the reviewer should recommend one.

Verifies the report cites `LC_GUARDRAIL_RECOMMENDED` and the message carries the
content-safety detail (the case-insensitive token "safety"). Other rule-id
citations warn, not fail. Exit 0 on PASS; sys.exit on failure.
"""
import os
import re
import sys
from pathlib import Path

REPORT = Path(os.getcwd()) / "_review_report.md"
REQUIRED_RULE_ID = "LC_GUARDRAIL_RECOMMENDED"
REQUIRED_TOKEN = "safety"  # matched case-insensitively (content-safety flavor)
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
    if REQUIRED_RULE_ID not in text:
        sys.exit(f"FAIL: report does not cite rule_id `{REQUIRED_RULE_ID}`.")
    print(f"OK: report cites `{REQUIRED_RULE_ID}`")
    if REQUIRED_TOKEN and REQUIRED_TOKEN.lower() not in text.lower():
        sys.exit(f"FAIL: report does not mention `{REQUIRED_TOKEN}` (content-safety detail).")
    if REQUIRED_TOKEN:
        print(f"OK: report mentions `{REQUIRED_TOKEN}`")

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
