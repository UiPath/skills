#!/usr/bin/env python3
"""Verify the SMTP settings read back from the organization match the prompt."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_setup'))
from admin_helpers import run_cli, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="check_smtp: %(message)s")

# The values smtp_configure_e2e.yaml's prompt asks for; the host is also
# TARGET_HOST in identity/_setup/setup_smtp_reset.py. Host, port, sender
# address and display name differ from the inherited defaults, so a match
# shows they were written during this run.
EXPECTED = {
    "host": "smtp-e2e.example.com",
    "port": "2525",
    "enablessl": "true",
    "fromaddress": "noreply@example.com",
    "fromdisplayname": "UiPath E2E Test",
}


def read_settings() -> dict | None:
    data = run_cli(["admin", "smtp", "get"])
    if not data or data.get("Result") != "Success":
        return None
    # CLI returns PascalCase keys (Host, Port, EnableSsl, etc.)
    return {k.lower(): str(v) for k, v in (data.get("Data") or {}).items() if v is not None}


def mismatches(settings: dict) -> dict:
    return {
        k: settings.get(k)
        for k, want in EXPECTED.items()
        if (settings.get(k) or "").lower() != want.lower()
    }


def main():
    last = {}

    # Poll for eventual consistency
    def matched():
        settings = read_settings()
        last["settings"] = settings
        if settings is None:
            return None
        return not mismatches(settings)

    if not poll(matched):
        settings = last.get("settings")
        if settings is None:
            fail("could not read SMTP settings on the last attempt")
        wrong = ", ".join(f"{k}={v!r} (want {EXPECTED[k]!r})" for k, v in mismatches(settings).items())
        fail(f"SMTP settings do not match the prompt: {wrong}")

    ok(f"SMTP configured as requested: host={EXPECTED['host']} port={EXPECTED['port']}")


main()
