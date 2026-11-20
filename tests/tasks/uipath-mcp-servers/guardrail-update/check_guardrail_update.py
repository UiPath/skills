#!/usr/bin/env python3
"""Grade adding credit card numbers to the PII guardrail and keeping the rest.

The stored rule blocks Email (threshold 0.7) with the reason "Personal data is
not allowed". `--entity` replaces the whole selection, so passing only the new
entity drops Email.

Passes when every executed `agenthub mcp-guardrails update` (not --help or
--dry-run; the mock answers each with success, so each changed the rule) names
`--validator pii-detection`, `--mcp vendor-mcp`, the Shared folder (`--folder-path
Shared` or `--folder-key folder-mock-shared`) and exactly the entities Email and
CreditCardNumber (any case and spacing, repeated or comma-separated), and keeps
the rest: no `--action` other than block, no `--reason` other than the stored one,
and no Email threshold other than 0.7. Fails when there is none, on any executed
`mcp-guardrails delete` or `create` (re-creating the rule instead of updating it),
and on any executed `agenthub mcp update`. The mock joins argv with spaces, so a
quoted value arrives without its quotes.
"""

import json
import os
import re
import sys
from pathlib import Path

CALL_LOG = Path(os.environ.get("CALL_LOG", "mocks/.calls.jsonl"))
SLUG = "vendor-mcp"
FOLDER_KEY = "folder-mock-shared"
ENTITIES = {"email", "creditcardnumber"}
STORED_REASON = "personal data is not allowed"
STORED_EMAIL_THRESHOLD = 0.7
SKIP = ("--help", "--dry-run")
NEXT_FLAG = r"(?=\s--|\s*$)"


def values(flag: str, args: str) -> list[str]:
    """Every value of `flag` (not of a longer flag that starts with it)."""
    pattern = re.escape(flag) + r"(?![\w-])[ =](.*?)" + NEXT_FLAG
    return [v.strip().strip("'\"") for v in re.findall(pattern, args)]


def name(entity: str) -> str:
    # The CLI drops spaces and case: "Credit Card Number" is CreditCardNumber.
    return re.sub(r"\s+", "", entity).lower()


def entities(args: str) -> set[str]:
    return {name(e) for v in values("--entity", args) for e in v.split(",") if e.strip()}


def email_threshold_ok(args: str) -> bool:
    for pair in values("--entity-threshold", args):
        entity, _, value = pair.partition("=")
        if name(entity) == "email":
            try:
                if float(value) != STORED_EMAIL_THRESHOLD:
                    return False
            except ValueError:
                return False
    return True


def folder_ok(args: str) -> bool:
    return "Shared" in values("--folder-path", args) or FOLDER_KEY in values("--folder-key", args)


def problem(args: str) -> str | None:
    if values("--validator", args) != ["pii-detection"]:
        return "the update does not name --validator pii-detection"
    if values("--mcp", args) != [SLUG]:
        return f"the update does not name --mcp {SLUG}"
    if entities(args) != ENTITIES:
        return f"the entities are {sorted(entities(args))}, not Email and CreditCardNumber (--entity replaces the selection)"
    if any(v != "block" for v in values("--action", args)):
        return "the update changes the action"
    if any(STORED_REASON not in v.lower() for v in values("--reason", args)):
        return "the update changes the reason"
    if not email_threshold_ok(args):
        return f"the update changes Email's threshold from {STORED_EMAIL_THRESHOLD}"
    if not folder_ok(args):
        return "the update does not name the Shared folder"
    return None


def main() -> int:
    if not CALL_LOG.is_file():
        print(f"FAIL: {CALL_LOG} not found")
        return 1
    updates = []
    for line in CALL_LOG.read_text(encoding="utf-8").splitlines():
        try:
            args = json.loads(line).get("args", "")
        except ValueError:
            continue
        if any(s in args for s in SKIP):
            continue
        if re.search(r"agenthub mcp-guardrails (delete|create)\b", args):
            print(f"FAIL: the rule was re-created instead of updated: {args}")
            return 1
        if re.search(r"agenthub mcp update\b", args) and "--print-schema" not in args:
            print(f"FAIL: an executed mcp update changes the whole server: {args}")
            return 1
        if "agenthub mcp-guardrails update" in args:
            updates.append(args)
    if not updates:
        print("FAIL: no executed `uip agenthub mcp-guardrails update`")
        return 1
    for args in updates:
        reason = problem(args)
        if reason:
            print(f"FAIL: {reason}: {args}")
            return 1
    print("PASS: the PII guardrail on vendor-mcp now catches Email and CreditCardNumber, rest kept")
    return 0


if __name__ == "__main__":
    sys.exit(main())
