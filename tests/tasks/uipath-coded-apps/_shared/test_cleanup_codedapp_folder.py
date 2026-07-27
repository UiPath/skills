#!/usr/bin/env python3
"""Allowlist unit test for cleanup_codedapp_folder.py.

The script uses an ALLOWLIST: it only deletes folders whose name starts with
`codedapp-` (per-run disposable test folders). Everything else — shared
(AdminDashboards / Shared), personal ("<user>'s workspace"), or any real tenant
folder — must be refused (SKIP printed, nothing deleted, exit 0).

No live tenant / uip binary needed: refused names return before any uip call.
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

    # Not on the allowlist → must be refused with a SKIP and exit 0. Covers the
    # shared governance home, the tenant default, a personal workspace, and a
    # plausible real folder name — none start with `codedapp-`.
    for name in ["AdminDashboards", "admindashboards", "Shared",
                 "nishank.siddharth@uipath.com's workspace", "Finance-Prod"]:
        r = run_with_folder(name)
        if r.returncode != 0:
            failures.append(f"{name!r}: expected exit 0, got {r.returncode}")
        if "SKIP" not in r.stderr or "codedapp-" not in r.stderr:
            failures.append(f"{name!r}: expected an allowlist SKIP on stderr, got {r.stderr!r}")

    # On the allowlist → NOT refused by the prefix guard. (It then falls through
    # to the uip delete call, which errors without a tenant; we only assert the
    # guard did not skip it.)
    r = run_with_folder("codedapp-govtest-1784045382")
    if "refusing to delete" in r.stderr:
        failures.append("codedapp-govtest-* wrongly refused by the allowlist guard")

    if failures:
        print("FAIL:\n  " + "\n  ".join(failures), file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
