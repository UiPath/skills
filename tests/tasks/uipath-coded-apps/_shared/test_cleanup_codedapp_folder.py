#!/usr/bin/env python3
"""Allowlist unit test for cleanup_codedapp_folder.py.

The script uses an ALLOWLIST: it only deletes folders whose name starts with
`codedapp-` (per-run disposable test folders). Everything else — shared
(AdminDashboards / Shared), personal ("<user>'s workspace"), or any real tenant
folder — must be refused (SKIP printed, nothing deleted, exit 0).

No live tenant / uip binary needed: refused names return before any uip call.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

import pytest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "_setup", "cleanup_codedapp_folder.py")


def run_with_folder(folder: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "report.json"), "w") as f:
            json.dump({"folder": folder}, f)
        return subprocess.run(
            [sys.executable, SCRIPT],
            cwd=d, capture_output=True, text=True, timeout=30,
        )


# Not on the allowlist → must be refused with a SKIP and exit 0. Covers the
# shared governance home, the tenant default, a personal workspace, and a
# plausible real folder name — none start with `codedapp-`.
NOT_ALLOWLISTED = [
    "AdminDashboards", "admindashboards", "Shared",
    "nishank.siddharth@uipath.com's workspace", "Finance-Prod",
]


@pytest.mark.parametrize("name", NOT_ALLOWLISTED)
def test_non_allowlisted_folder_is_refused(name: str) -> None:
    r = run_with_folder(name)
    assert r.returncode == 0, f"{name!r}: expected exit 0, got {r.returncode}"
    assert "SKIP" in r.stderr and "codedapp-" in r.stderr, (
        f"{name!r}: expected an allowlist SKIP on stderr, got {r.stderr!r}"
    )


def test_allowlisted_folder_is_not_refused_by_the_guard() -> None:
    # On the allowlist → NOT refused by the prefix guard. (It then falls
    # through to the uip delete call, which errors without a tenant; we only
    # assert the guard did not skip it.)
    r = run_with_folder("codedapp-govtest-1784045382")
    assert "refusing to delete" not in r.stderr, (
        "codedapp-govtest-* wrongly refused by the allowlist guard"
    )
