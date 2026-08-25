#!/usr/bin/env python3
"""Seed for the Outlook multipart e2e.

Env vars (required):
  OUTLOOK_TEST_TO   — recipient mailbox the test connection can reach
                      AND can poll (typically the same address as the
                      connection's bound mailbox, so we can verify
                      delivery without a second connection).

Writes `seed.json` with a unique `subject` token so the check script
can locate the email regardless of inbox noise.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path


def main() -> None:
    to_address = os.environ.get("OUTLOOK_TEST_TO", "").strip()
    if not to_address:
        sys.exit(
            "FAIL (seed): OUTLOOK_TEST_TO env var is required for the "
            "Outlook multipart e2e. Set it to an inbox the test connection "
            "can both send to and read from."
        )

    uuid8 = secrets.token_hex(4)
    subject = f"uipath-agents eval {uuid8}"
    seed = {
        "uuid8": uuid8,
        "subject": subject,
        "to_address": to_address,
        "connection_name": "outlook-coded-eval",
        "folder_path": "Shared/uipath-agents",
    }
    Path.cwd().joinpath("seed.json").write_text(json.dumps(seed, indent=2))
    print(f"OK: wrote seed.json with subject={subject!r}, to={to_address}")


if __name__ == "__main__":
    main()
