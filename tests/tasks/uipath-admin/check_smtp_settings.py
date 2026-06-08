#!/usr/bin/env python3
"""Verify SMTP settings were configured (host is non-empty)."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="check_smtp: %(message)s")


def main():
    # Poll for eventual consistency
    def find_host():
        data = run_cli(["admin", "smtp", "get"])
        if not data or data.get("Result") != "Success":
            return None
        smtp_data = data.get("Data", {})
        # CLI returns PascalCase keys (Host, Port, EnableSsl, etc.)
        return smtp_data.get("Host") or smtp_data.get("host") or None

    host = poll(find_host)
    if not host:
        fail("SMTP host is empty — settings not configured after retries")

    ok(f"SMTP configured with host={host}")


main()
