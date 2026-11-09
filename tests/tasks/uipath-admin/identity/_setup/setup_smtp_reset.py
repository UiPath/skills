#!/usr/bin/env python3
"""Pre-run reset: delete the organization's SMTP settings before the agent runs.

  SMTP_TARGET_HOST   the host the task's prompt asks the agent to configure
                     (required)

`smtp delete` removes the organization's own settings. `smtp get` then reports
the settings the organization inherits, which are not empty: on the eval
environments they read Host=smtp.example.com, Port=587, EnableSsl=true,
FromAddress=admin@mydomain.com (Identity Server's seeded defaults plus a
host-level SMTP config). The task therefore asks for values that differ from
every inherited one, and this reset refuses to start the run while the target
host is still visible: a read-back check would then pass whether or not the
agent wrote anything.

Exits 1 when the delete fails or the target host survives it, so the run ends
as ERROR instead of producing a meaningless verdict.
"""

import logging
import os
import sys

from admin_helpers import poll, run_cli

logging.basicConfig(level=logging.INFO, format="setup_smtp_reset: %(message)s")
logger = logging.getLogger(__name__)


def current_host() -> str | None:
    data = run_cli(["admin", "smtp", "get"])
    if not data or data.get("Result") != "Success":
        return None
    smtp = data.get("Data") or {}
    return smtp.get("Host") or smtp.get("host") or ""


def main():
    target = os.environ.get("SMTP_TARGET_HOST", "").strip()
    if not target:
        logger.error("SMTP_TARGET_HOST is not set")
        sys.exit(1)

    result = run_cli(["admin", "smtp", "delete"])
    if not result or result.get("Result") != "Success":
        logger.error("smtp delete failed: %s", result)
        sys.exit(1)

    def cleared():
        # Wrapped in a list so an empty host still counts as a result for poll().
        host = current_host()
        if host is None or host.lower() == target.lower():
            return None
        return [host]

    # Poll for eventual consistency: the delete can take a moment to show.
    found = poll(cleared)
    if not found:
        logger.error("SMTP host still reads %r after delete; the run would not prove anything", target)
        sys.exit(1)

    logger.info("SMTP reset; inherited host is %r", found[0] or "(empty)")


main()
