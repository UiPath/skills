#!/usr/bin/env python3
"""Check that the review report identifies the missing PII guardrail.

Accepts either:
  - the canonical rule ID `LC_GUARDRAIL_RECOMMENDED` with a PII field mention, OR
  - any prose that identifies a missing / absent pii_detection guardrail together
    with at least one of the agent's PII fields (customer_email, full_name, ssn).

Exit 0 on PASS; sys.exit(message) on failure.
"""
import os
import re
import sys
from pathlib import Path

REPORT = Path(os.getcwd()) / "_review_report.md"
MIN_REPORT_BYTES = 500
PII_FIELDS = ["customer_email", "full_name", "ssn"]
CANONICAL_RULE_ID = "LC_GUARDRAIL_RECOMMENDED"

NOISE = {
    "JSON", "YAML", "TOML", "XAML", "BPMN", "PDD", "SDD", "UUID", "HTTP",
    "HTTPS", "REST", "API", "CLI", "SDK", "NULL", "TRUE", "FALSE", "TODO",
    "FIXME", "WIP", "README",
}


def has_pii_field(text: str) -> bool:
    return any(f in text for f in PII_FIELDS)


def has_pii_guardrail_prose(text: str) -> bool:
    """True when the report identifies a missing/absent PII guardrail in prose."""
    lower = text.lower()
    has_pii = "pii" in lower or "pii_detection" in lower
    has_guardrail = "guardrail" in lower
    has_missing = any(w in lower for w in ("missing", "absent", "no ", "not configured",
                                            "recommend", "should add", "lacks", "without"))
    return has_pii and has_guardrail and has_missing


def main() -> None:
    if not REPORT.is_file():
        sys.exit(f"FAIL: {REPORT} not found")
    text = REPORT.read_text(encoding="utf-8", errors="replace")
    if len(text) < MIN_REPORT_BYTES:
        sys.exit(f"FAIL: {REPORT} is suspiciously short ({len(text)} bytes).")

    if not has_pii_field(text):
        sys.exit(f"FAIL: report does not mention any PII field ({', '.join(PII_FIELDS)}).")
    print(f"OK: report mentions at least one PII field")

    if CANONICAL_RULE_ID in text:
        print(f"OK: report cites canonical rule_id `{CANONICAL_RULE_ID}`")
    elif has_pii_guardrail_prose(text):
        print("OK: report identifies missing PII guardrail in prose")
    else:
        sys.exit(
            "FAIL: report does not identify a missing PII guardrail — "
            "expected either `LC_GUARDRAIL_RECOMMENDED` or prose about a "
            "missing/absent pii_detection guardrail."
        )

    skills_repo = os.environ.get("SKILLS_REPO_PATH")
    if skills_repo:
        catalog_dir = (
            Path(skills_repo) / "skills" / "uipath-review" / "references" / "agents"
        )
        if catalog_dir.is_dir():
            catalog_text = "".join(
                f.read_text(encoding="utf-8", errors="replace")
                for f in sorted(catalog_dir.glob("agents-*-rules.md"))
            )
            unknown = sorted(
                c
                for c in set(re.findall(r"`([A-Z][A-Z0-9_]{4,})`", text)) - NOISE
                if c not in catalog_text
            )
            if unknown:
                print(
                    f"WARN: rule_id(s) not in judgment catalog (may be CLI-emitted): {unknown}"
                )
    print("PASS")


if __name__ == "__main__":
    main()
