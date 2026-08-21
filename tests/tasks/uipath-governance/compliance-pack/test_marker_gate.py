#!/usr/bin/env python3
"""Marker-gate check for the compliance-pack setup/cleanup pair.

The shared test tenant has one ISO 42001 pack state and tasks run in parallel,
so cleanup must disable the pack ONLY when its own setup enabled it. This asserts
the gate: no ownership marker in the task sandbox -> disable_pack() returns before
touching tenant state.

Runs offline. Needs no `uip` auth: with HOME pointed at a temp dir every CLI call
fails and the scripts log + exit 0 by design, so only the gate branch varies.

    python3 test_marker_gate.py
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
CLEANUP = HERE / "cleanup_compliance_pack.py"
MARKER_NAME = ".iso42001-enabled-by-setup"
GATE_LOG = "No ownership marker"


def run_cleanup(sandbox):
    env = {k: v for k, v in os.environ.items()
           if k not in ("UIPATH_TENANT_ID", "UIPATH_CLI_TENANT_ID")}
    env["HOME"] = str(sandbox)
    proc = subprocess.run([sys.executable, str(CLEANUP)], cwd=sandbox, env=env,
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, f"cleanup must always exit 0, got {proc.returncode}"
    return proc.stderr + proc.stdout


def main():
    with tempfile.TemporaryDirectory() as d:
        sandbox = Path(d)

        out = run_cleanup(sandbox)
        assert GATE_LOG in out, f"no marker: expected gate to skip disable.\n{out}"

        (sandbox / MARKER_NAME).touch()
        out = run_cleanup(sandbox)
        assert GATE_LOG not in out, f"marker present: gate must not skip.\n{out}"

    print("OK: disable_pack() gated on the sandbox ownership marker")


main()
