#!/usr/bin/env python3
"""Guardrail unit test for cleanup_codedapp_folder.py.

Runs the cleanup script in a temp dir with a crafted report.json and asserts
it refuses protected folder names (prints SKIP, deletes nothing, exits 0).
No live tenant / uip binary needed: the guardrail returns before any uip call.
"""
import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(__file__), "cleanup_codedapp_folder.py")


def run_with_folder(folder: str):
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "report.json"), "w") as f:
            json.dump({"folder": folder}, f)
        return subprocess.run(
            [sys.executable, SCRIPT],
            cwd=d, capture_output=True, text=True, timeout=30,
        )


def main() -> int:
    failures = []

    # Protected names must be refused with a "protected" SKIP and exit 0.
    for name in ["AdminDashboards", "admindashboards", "Shared",
                 "nishank.siddharth@uipath.com's workspace"]:
        r = run_with_folder(name)
        if r.returncode != 0:
            failures.append(f"{name!r}: expected exit 0, got {r.returncode}")
        if "protected" not in r.stderr.lower():
            failures.append(f"{name!r}: expected 'protected' SKIP on stderr, got {r.stderr!r}")

    # A legit codedapp-* name is NOT caught by the protected guard.
    r = run_with_folder("codedapp-workspace-abc123")
    if "protected" in r.stderr.lower():
        failures.append("codedapp-workspace-* wrongly caught by protected guard")

    if failures:
        print("FAIL:\n  " + "\n  ".join(failures), file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
