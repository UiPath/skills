#!/usr/bin/env python3
"""Validate a generated ``.flow`` against the Flow schema, resilient to the
`uip` maestro-tool plugin cold-start.

Drop-in ``run_command`` replacement for a raw
``uip maestro flow validate <path> --output json`` criterion. Runs the exact
same CLI verb via the shared harness, but retries past the transient
"unknown command 'maestro'" plugin-load race that fails the FIRST
``uip maestro ...`` call in a fresh grading process (see
``flow_check._COLD_PLUGIN_MARKER``). Exits 0 when the flow validates, nonzero
otherwise.

Usage:
    python3 validate_flow.py [<path-to.flow>]

With no argument, the single ``.flow`` under the located Flow project is used.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flow_check import run_validate  # noqa: E402


def main() -> None:
    flow_file = sys.argv[1] if len(sys.argv) > 1 else None
    run_validate(flow_file)


if __name__ == "__main__":
    main()
