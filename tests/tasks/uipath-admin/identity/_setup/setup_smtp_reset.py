#!/usr/bin/env python3
"""Pre-run reset: delete the organization's SMTP settings before the agent runs.

`smtp delete` removes the organization's own settings. `smtp get` then reports
the settings the organization inherits, which are not empty: on the eval
environments they read Host=smtp.example.com, Port=587, EnableSsl=true,
FromAddress=admin@mydomain.com (Identity Server's seeded From defaults; the
host and port come from outside the organization). The task therefore asks for
values that differ from the inherited ones, and this reset refuses to start the
run while the target host is still visible: a read-back check would then pass
whether or not the agent wrote anything.

The delete is unconditional. A target host already in place is either a
leftover or a concurrent run's live write, and the two cannot be told apart;
any other state is not this task's to preserve.

Exits 1 when the delete fails, the settings cannot be read, or the target host
survives the delete, so the run ends as ERROR instead of producing a
meaningless verdict.
"""

import logging
import sys

from admin_helpers import poll, run_cli

logging.basicConfig(level=logging.INFO, format="setup_smtp_reset: %(message)s")
logger = logging.getLogger(__name__)

# The host smtp_configure_e2e.yaml's prompt asks for. Keep in sync with the
# prompt and with EXPECTED in identity/check_smtp_settings.py.
TARGET_HOST = "smtp-e2e.example.com"


def current_host() -> str | None:
    data = run_cli(["admin", "smtp", "get"])
    if not data or data.get("Result") != "Success":
        return None
    smtp = data.get("Data") or {}
    return smtp.get("Host") or smtp.get("host") or ""


def main():
    result = run_cli(["admin", "smtp", "delete"])
    if not result or result.get("Result") != "Success":
        logger.error("smtp delete failed: %s", result)
        sys.exit(1)

    last = {}

    def cleared():
        host = current_host()
        last["host"] = host
        if host is None or host.lower() == TARGET_HOST.lower():
            return None
        # Wrapped in a list so an empty host still counts as a result for poll().
        return [host]

    # Poll for eventual consistency: the delete can take a moment to show.
    found = poll(cleared)
    if not found:
        if last.get("host") is None:
            logger.error("could not read SMTP settings after delete")
        else:
            logger.error("SMTP host still reads %r after delete; the run would not prove anything", TARGET_HOST)
        sys.exit(1)

    logger.info("SMTP reset; inherited host is %r", found[0] or "(empty)")


main()
