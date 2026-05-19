#!/usr/bin/env python3
"""Suite-level teardown: uninstall the shared deploy created by suite_setup.py.

Reads E2E_SUITE_DEPLOY env var to find the deployment name. Best-effort,
always exits 0."""
from __future__ import annotations

import json
import os
import subprocess
import sys


def main() -> int:
    name = os.environ.get("E2E_SUITE_DEPLOY", "e2e-suite-shared-deploy")
    print(f"# suite: uninstalling {name}…", file=sys.stderr)
    r = subprocess.run(
        ["uip", "solution", "deploy", "uninstall", name, "--output", "json"],
        capture_output=True, text=True, timeout=300,
    )
    try:
        env = json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        env = {}
    if env.get("Result") == "Success":
        print(f"# suite: uninstalled {name}", file=sys.stderr)
    else:
        msg = env.get("Message") or r.stderr.strip()
        print(f"# suite: WARN uninstall {name}: {msg[:200]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
