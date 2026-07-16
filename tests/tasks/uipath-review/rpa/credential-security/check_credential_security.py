#!/usr/bin/env python3
"""Grade the credential-security review.

Planted (CredentialBot/Main.xaml): a plaintext password literal assigned to a
String and logged (should be a SecureString from a Credential Asset), plus a
credential-type asset fetched with Get Asset instead of Get Credential.

PASS requires the report to flag AT LEAST ONE credential defect AS a problem
(ST-SEC-007/008/009 code, or prose about the hardcoded/plaintext password,
SecureString, or Get Credential vs Get Asset). "No hardcoded credential; uses
SecureString correctly" does not count. The planted secret must still exist.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from grader_common import report_text, asserts_any, fixture_contains  # noqa: E402

# SecureString / Get Credential are the FIX. Count them only when the report
# RECOMMENDS them (implying they are not used now), never when it wrongly claims
# they are already used — "uses SecureString correctly" is a wrong dismissal.
_SECURESTRING_REC = re.compile(
    r"(should|must|missing|instead|convert|store\b|needs?\s+to|use)\s+(?:\w+\s+){0,4}secure\s?string"
    r"|secure\s?string\s+(?:\w+\s+){0,3}(instead|should|must|missing)")

PROJECT = "CredentialBot"
RULE_CODES = ("ST-SEC-007", "ST-SEC-008", "ST-SEC-009")


def main() -> None:
    text = report_text(500)
    lower = text.lower()

    if not fixture_contains(f"{PROJECT}/Main.xaml", "P@ssw0rd_FAKE_DoNotUse"):
        sys.exit(f"FAIL: {PROJECT}/Main.xaml no longer contains the planted (fake) "
                 "hardcoded password (fixture appears mutated).")

    found = []
    if any(c in text for c in RULE_CODES):
        found.append("ST-SEC rule code")
    # hardcoded/plaintext password (presence defect).
    if asserts_any(text, ["hardcod", "plaintext", "plain text", "in clear", "in plaintext"], presence=True) \
            and any(k in lower for k in ("password", "credential", "secret")):
        found.append("hardcoded/plaintext credential")
    if _SECURESTRING_REC.search(lower):
        found.append("SecureString (recommended)")
    if ("get credential" in lower or "getrobotcredential" in lower) and any(
            w in lower for w in ("instead", "should", "get asset", "rather than", "must use")):
        found.append("Get Credential vs Get Asset")

    if not found:
        sys.exit("FAIL: report does not flag any credential-security defect as a problem "
                 "(expected ST-SEC-007/008/009 or prose about a hardcoded credential, "
                 "SecureString, or Get Credential vs Get Asset).")
    print(f"OK: report flags: {', '.join(found)}")
    print("PASS")


if __name__ == "__main__":
    main()
