#!/usr/bin/env python3
"""Grade the PII guardrail create from the uip mock's call log.

Passes when exactly one executed `agenthub mcp-guardrails create` (not --help
or --dry-run) exists, and it names `--validator pii-detection`, `--mcp vendor-mcp`,
`--action block`, the entities USSocialSecurityNumber and
InternationalBankingAccountNumber and nothing else (any
case and spacing, as the CLI matches them; repeated `--entity` or comma-separated),
the `--reason` the user gave ("Personal data is not allowed"), and the Shared folder
(`--folder-path Shared` or `--folder-key folder-mock-shared`). Fails on any
executed `agenthub mcp update`. The mock joins argv with spaces, so a quoted
value arrives without its quotes.
"""

import json
import os
import re
import sys
from pathlib import Path

CALL_LOG = Path(os.environ.get("CALL_LOG", "mocks/.calls.jsonl"))
SLUG = "vendor-mcp"
FOLDER_KEY = "folder-mock-shared"
ENTITIES = {"ussocialsecuritynumber", "internationalbankingaccountnumber"}
REASON = "personal data is not allowed"
SKIP = ("--help", "--dry-run")
NEXT_FLAG = r"(?=\s--|\s*$)"


def values(flag: str, args: str) -> list[str]:
    """Every value of `flag` (not of a longer flag that starts with it)."""
    pattern = re.escape(flag) + r"(?![\w-])[ =](.*?)" + NEXT_FLAG
    return [v.strip().strip("'\"") for v in re.findall(pattern, args)]


def entities(args: str) -> set[str]:
    # The CLI drops spaces and case: "Credit Card Number" is CreditCardNumber.
    return {re.sub(r"\s+", "", e).lower() for v in values("--entity", args) for e in v.split(",") if e.strip()}


def folder_ok(args: str) -> bool:
    return "Shared" in values("--folder-path", args) or FOLDER_KEY in values("--folder-key", args)


def problem(args: str) -> str | None:
    if values("--validator", args) != ["pii-detection"]:
        return "the create does not name --validator pii-detection"
    if values("--mcp", args) != [SLUG]:
        return f"the create does not name --mcp {SLUG}"
    if values("--action", args) != ["block"]:
        return "the create does not block (--action block)"
    if entities(args) != ENTITIES:
        return f"the entities are {sorted(entities(args))}, not USSocialSecurityNumber and InternationalBankingAccountNumber"
    if REASON not in " ".join(values("--reason", args)).lower():
        return "the --reason is not the message the user gave"
    if not folder_ok(args):
        return "the create does not name the Shared folder"
    return None


def main() -> int:
    if not CALL_LOG.is_file():
        print(f"FAIL: {CALL_LOG} not found")
        return 1
    creates = []
    for line in CALL_LOG.read_text(encoding="utf-8").splitlines():
        try:
            args = json.loads(line).get("args", "")
        except ValueError:
            continue
        if any(s in args for s in SKIP):
            continue
        if re.search(r"agenthub mcp update\b", args) and "--print-schema" not in args:
            print(f"FAIL: an executed mcp update changes the whole server: {args}")
            return 1
        if "agenthub mcp-guardrails create" in args:
            creates.append(args)
    if len(creates) != 1:
        print(f"FAIL: {len(creates)} executed `uip agenthub mcp-guardrails create`, want 1")
        for args in creates:
            print(f"  create: {args}")
        return 1
    reason = problem(creates[0])
    if reason:
        print(f"FAIL: {reason}: {creates[0]}")
        return 1
    print("PASS: one PII guardrail that blocks US SSNs and IBANs on vendor-mcp in Shared")
    return 0


if __name__ == "__main__":
    sys.exit(main())
