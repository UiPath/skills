#!/usr/bin/env python3
"""Smoke check for the CLI-first review contract (coded): confirm a
non-trivial review report was produced. The delegation behavior (ran
`uip codedagent review`, read-only, read catalogs) is asserted in the task
YAML. Exit 0 on PASS; sys.exit on failure.
"""
import os
import sys
from pathlib import Path

REPORT = Path(os.getcwd()) / "_review_report.md"
MIN_REPORT_BYTES = 500


def main() -> None:
    if not REPORT.is_file():
        sys.exit(f"FAIL: {REPORT} not found")
    text = REPORT.read_text(encoding="utf-8", errors="replace")
    if len(text) < MIN_REPORT_BYTES:
        sys.exit(f"FAIL: {REPORT} is suspiciously short ({len(text)} bytes).")
    print(f"OK: review report present ({len(text)} bytes)")


if __name__ == "__main__":
    main()
