#!/usr/bin/env python3
"""Check for CODED_GUARDRAIL_WRONG_IMPORT — a LangChain coded agent that imports
guardrail symbols from `uipath.platform.guardrails` and never from
`uipath_langchain.guardrails`, so the adapter never registers and the guardrail
silently no-ops.

This finding is deterministic and **offline** — it comes from `uip codedagent
review` (Step 2.5a), which a separate `command_executed` criterion in the task
YAML enforces ran. So this check only confirms the review **surfaced** the
finding in the saved report, accepting either form the agent uses:

  1. the CLI rule_id `CODED_GUARDRAIL_WRONG_IMPORT` carried verbatim (preferred), OR
  2. prose that identifies the wrong-import / silent-no-op problem (names the
     correct `uipath_langchain.guardrails` module, the unregistered adapter, or
     the silent no-op).

Form 2 keeps the check robust to report-fidelity variance without weakening the
signal — the `command_executed` gate already proves the CLI ran. Exit 0 on PASS;
sys.exit on failure.
"""
import os
import re
import sys
from pathlib import Path

REPORT = Path(os.getcwd()) / "_review_report.md"
REQUIRED_RULE_ID = "CODED_GUARDRAIL_WRONG_IMPORT"
# Phrases that mean the report identified the wrong-import / silent-no-op problem.
# Matched case-insensitively.
WRONG_IMPORT_PHRASES = (
    "uipath_langchain.guardrails",  # names the module guardrails should come from
    "silently no-op",
    "silently no op",
    "silently does nothing",
    "never registers",
    "never registered",
    "adapter is not registered",
    "adapter never",
    "wrong import",
    "wrong module",
    "incorrect import",
    "imported from the wrong",
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
    has_prose = any(p in low for p in WRONG_IMPORT_PHRASES)

    if has_rule_id:
        print(f"OK: report cites `{REQUIRED_RULE_ID}`")
    elif has_prose:
        print(
            "OK: report describes the wrong-import / silent-no-op problem "
            "(rule_id not transcribed verbatim, but the CLI finding was surfaced)"
        )
    else:
        sys.exit(
            f"FAIL: report neither cites `{REQUIRED_RULE_ID}` nor describes the "
            "guardrail wrong-import / silent-no-op problem."
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
