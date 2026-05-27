#!/usr/bin/env python3
"""Check for EVAL_BROKEN_EVALUATOR_REF in a coded agent.

Verifies the saved review report cites rule_id `EVAL_BROKEN_EVALUATOR_REF`
and names the dangling evaluator `ghost-evaluator`, AND that every
rule-id-shaped citation exists in one of the catalog files.

Exit 0 on PASS; sys.exit("FAIL: ...") on any failure.
"""

import os
import re
import sys
from pathlib import Path

REPORT = Path(os.getcwd()) / "_review_report.md"
REQUIRED_RULE_ID = "EVAL_BROKEN_EVALUATOR_REF"
REQUIRED_FIELD = "ghost-evaluator"
MIN_REPORT_BYTES = 500


def assert_report_present() -> str:
    if not REPORT.is_file():
        sys.exit(f"FAIL: {REPORT} not found")
    text = REPORT.read_text(encoding="utf-8", errors="replace")
    if len(text) < MIN_REPORT_BYTES:
        sys.exit(f"FAIL: {REPORT} is suspiciously short ({len(text)} bytes).")
    print(f"OK: report file present ({len(text)} bytes)")
    return text


def assert_required_rule_id(text: str) -> None:
    if REQUIRED_RULE_ID not in text:
        sys.exit(
            f"FAIL: report does not cite rule_id `{REQUIRED_RULE_ID}`. "
            f"The eval set references {REQUIRED_FIELD}-id with no matching "
            f"evaluator config — the catalog rule for this in "
            f"agents-coded-rules.md is {REQUIRED_RULE_ID}."
        )
    print(f"OK: report cites rule_id `{REQUIRED_RULE_ID}`")


def assert_required_field(text: str) -> None:
    if REQUIRED_FIELD not in text:
        sys.exit(
            f"FAIL: report does not name the dangling evaluator "
            f"`{REQUIRED_FIELD}` — the finding should cite the broken ref."
        )
    print(f"OK: report names `{REQUIRED_FIELD}`")


def assert_no_invented_rule_ids(text: str) -> None:
    skills_repo = os.environ.get("SKILLS_REPO_PATH")
    if not skills_repo:
        print("OK (skip): SKILLS_REPO_PATH not set")
        return
    catalog_dir = Path(skills_repo) / "skills" / "uipath-review" / "references" / "agents"
    if not catalog_dir.is_dir():
        print(f"OK (skip): {catalog_dir} not found")
        return
    catalog_text = "".join(
        f.read_text(encoding="utf-8", errors="replace")
        for f in sorted(catalog_dir.glob("agents-*-rules.md"))
    )
    if not catalog_text:
        print("OK (skip): no catalog files")
        return
    backticked = set(re.findall(r"`([A-Z][A-Z0-9_]{4,})`", text))
    noise = {
        "JSON", "YAML", "TOML", "XAML", "BPMN", "PDD", "SDD", "UUID",
        "HTTP", "HTTPS", "REST", "API", "CLI", "SDK", "OS", "DB",
        "NULL", "TRUE", "FALSE", "TODO", "FIXME", "WIP",
        "README", "CHANGELOG", "LICENSE", "PII",
        # Credential / env-var / config identifiers that show up in
        # backticks in security findings but are NOT rule_ids.
        "API_KEY", "API_SECRET", "SECRET_KEY", "ACCESS_KEY", "ACCESS_TOKEN",
        "SECRET", "PASSWORD", "TOKEN", "CREDENTIALS", "CREDENTIAL", "BEARER",
        "ENV", "BASE_URL", "DB_HOST", "DB_PASSWORD",
    }
    candidates = {c for c in backticked if c not in noise}
    if not candidates:
        print("OK: no rule_id citations to check")
        return
    invented = sorted(c for c in candidates if c not in catalog_text)
    if invented:
        sys.exit(
            f"FAIL: report cites {len(invented)} rule_id(s) not in any catalog "
            f"(Critical Rule 11): {invented}."
        )
    print(f"OK: all {len(candidates)} rule_id citation(s) exist in the catalog")


def main() -> None:
    text = assert_report_present()
    assert_required_rule_id(text)
    assert_required_field(text)
    assert_no_invented_rule_ids(text)


if __name__ == "__main__":
    main()
