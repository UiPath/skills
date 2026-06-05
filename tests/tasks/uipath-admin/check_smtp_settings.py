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
        fail(f"smtp get did not return Success — raw: {data}")

    smtp_data = data.get("Data", {})
    # CLI returns PascalCase keys (Host, Port, EnableSsl, etc.)
    host = smtp_data.get("Host") or smtp_data.get("host") or ""
    if not host:
        fail(f"SMTP host is empty — settings not configured. Data keys: {list(smtp_data.keys())}")

    ok(f"SMTP configured with host={host}")


main()
