#!/usr/bin/env python3
"""Guard the staged SupplierOnboarding SDD: the build must not rewrite its input.

The skill never overwrites `sdd.md` (SKILL.md Rule 1). This grader re-reads the
staged copy from the sandbox and asserts every contract the other three graders
depend on is still there — seven stages, all 39 task names, the SLA response
map, the routing guards, the case exits, the case In-arguments and the pinned
tenant identities. A trimmed or regenerated SDD fails here instead of silently
weakening the rest of the suite.
"""

from __future__ import annotations

import glob
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import supplier_onboarding_expected as E  # noqa: E402


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def find_sdd() -> str:
    matches = sorted(
        path
        for path in glob.glob("**/sdd.md", recursive=True)
        if "/.venv/" not in path and "/node_modules/" not in path
    )
    if not matches:
        fail("no staged sdd.md found in the sandbox")
    return matches[0]


def main() -> None:
    path = find_sdd()
    text = open(path, encoding="utf-8").read()
    flat = E.norm_expr(text)

    missing_stages = [label for label in E.ALL_STAGES if label not in text]
    if missing_stages:
        fail(f"staged sdd.md no longer names stage(s): {missing_stages}")

    missing_tasks = [
        spec["name"]
        for specs in E.TASKS.values()
        for spec in specs
        if spec["name"] not in text
    ]
    if missing_tasks:
        fail(f"staged sdd.md no longer names task(s): {missing_tasks}")

    if not re.search(r"^#{2,4}\s+.*SLA Response Map", text, re.IGNORECASE | re.MULTILINE):
        fail("staged sdd.md has lost its SLA Response Map section")
    missing_sla = [
        title
        for title in [E.CASE_SLA_TITLE] + [f"{label} SLA" for label in E.ALL_STAGES]
        if title not in text
    ]
    if missing_sla:
        fail(f"staged sdd.md no longer names SLA(s): {missing_sla}")

    missing_guards = [
        guard
        for guard in (
            E.SEND_BACK,
            E.BUYER_APPROVE,
            E.BUYER_DECLINE,
            E.SEND_TO_SETUP,
            E.COMPLIANCE_REJECT,
            E.BANK_VERIFIED,
            E.BANK_NOT_VERIFIED,
            E.SIGN_OFF_REQUIRED,
            E.SIGN_OFF_NOT_REQUIRED,
        )
        if E.norm_expr(guard) not in flat
    ]
    if missing_guards:
        fail(f"staged sdd.md no longer carries routing guard(s): {missing_guards}")

    for rule in ("required-stages-completed", "selected-stage-completed", "wait-for-connector"):
        if rule not in text:
            fail(f"staged sdd.md no longer carries the {rule!r} rule")

    missing_vars = [name for name in E.IN_VARIABLES + E.GATE_VARIABLES if name not in text]
    if missing_vars:
        fail(f"staged sdd.md no longer declares case variable(s): {missing_vars}")

    missing_ids = [guid for guid in E.FIXTURE_GUIDS if guid not in text.lower()]
    if missing_ids:
        fail(f"staged sdd.md no longer pins tenant identity/identities: {missing_ids}")

    print(f"OK: staged {path} still carries the full SupplierOnboarding contract")


if __name__ == "__main__":
    main()
