#!/usr/bin/env python3
"""Verify SMTP settings were configured (host is non-empty)."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, fail, ok

logging.basicConfig(level=logging.INFO, format="check_smtp: %(message)s")


def main():
    data = run_cli(["admin", "smtp", "get"])
    if not data or data.get("Result") != "Success":
        fail("smtp get did not return Success")

    smtp_data = data.get("Data", {})
    host = smtp_data.get("host") or ""
    if not host:
        fail("SMTP host is empty — settings not configured")

    ok(f"SMTP configured with host={host}")


main()
