#!/usr/bin/env python3
"""Check for GUARDRAIL_UNKNOWN_VALIDATOR — the agent has a built-in guardrail
whose `validatorType` is not in the tenant's guardrail catalog.

The finding can ONLY be known by running `uip agent review` (Step 2.5a), which
fetches the live catalog — you cannot tell a validator is unknown by eye. The
task YAML enforces that with a separate `command_executed` criterion on
`uip agent review`. So this check only needs to confirm the review **surfaced**
the finding in the saved report, and can accept either form the agent uses:

  1. the CLI rule_id `GUARDRAIL_UNKNOWN_VALIDATOR` carried verbatim (preferred), OR
  2. the bogus validator named (`totally_made_up_validator`) together with a
     clear "unknown / not in the catalog" statement.

Form 2 makes the check robust to report-fidelity variance (on some runs the
agent summarizes the CLI finding instead of copying the rule_id verbatim) WITHOUT
weakening the signal — the `command_executed` gate already proves the
catalog-backed CLI ran, so a summarized finding is still a real, CLI-derived
one, not an eyeballed guess. Exit 0 on PASS; sys.exit on failure.
"""
import os
import re
import sys
from pathlib import Path

REPORT = Path(os.getcwd()) / "_review_report.md"
REQUIRED_RULE_ID = "GUARDRAIL_UNKNOWN_VALIDATOR"
# The bogus validatorType injected into the fixture.
VALIDATOR_NAME = "totally_made_up_validator"
# Phrases that, alongside the validator name, mean the report identified it as
# not in the catalog. Matched case-insensitively.
UNKNOWN_PHRASES = (
    "unknown validator",
    "unknown built-in validator",
    "not in the catalog",
    "not in the guardrail catalog",
    "not a known validator",
    "not a valid validator",
    "not a recognized validator",
    "not a recognised validator",
    "not recognized",
    "not recognised",
    "unrecognized validator",
    "unrecognised validator",
    "invalid validator",
    "does not exist",
    "no such validator",
    "made-up validator",
    "made up validator",
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
    has_prose = VALIDATOR_NAME.lower() in low and any(p in low for p in UNKNOWN_PHRASES)

    if has_rule_id:
        print(f"OK: report cites `{REQUIRED_RULE_ID}`")
    elif has_prose:
        print(
            f"OK: report identifies `{VALIDATOR_NAME}` as not in the catalog "
            "(rule_id not transcribed verbatim, but the CLI finding was surfaced)"
        )
    else:
        sys.exit(
            f"FAIL: report neither cites `{REQUIRED_RULE_ID}` nor describes "
            f"`{VALIDATOR_NAME}` as an unknown / uncataloged validator."
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
