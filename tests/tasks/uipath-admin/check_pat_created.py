#!/usr/bin/env python3
"""Verify a PAT with description containing 'e2e-test-pat' exists."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, fail, ok

logging.basicConfig(level=logging.INFO, format="check_pat: %(message)s")


def main():
    data = run_cli(["admin", "pat", "list"])
    if not data or data.get("Result") != "Success":
        fail("pat list did not return Success")

    found = any(
        "e2e-test-pat" == (t.get("description") or "")
        for t in data.get("Data", [])
    )

    if not found:
        fail("PAT with description 'e2e-test-pat' not found")

    ok("PAT 'e2e-test-pat' exists")


main()
