#!/usr/bin/env python3
"""Match command regexes against invocations recorded by the offline uip mock."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, default=Path(__file__).with_name("calls.log"))
    bounds = parser.add_mutually_exclusive_group(required=True)
    bounds.add_argument("--min-count", type=int)
    bounds.add_argument("--max-count", type=int)
    args = parser.parse_args()

    log_path = args.log
    if not log_path.exists():
        print(f"missing command log: {log_path}")
        return 1

    patterns = sys.stdin.read().splitlines()
    if not 1 <= len(patterns) <= 2:
        print("expected one pattern line and, optionally, one exclude-pattern line")
        return 1

    pattern_text = patterns[0]
    pattern = re.compile(pattern_text)
    exclude = re.compile(patterns[1]) if len(patterns) == 2 else None
    commands = [
        line
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if not line.startswith("#")
    ]
    matches = [
        command
        for command in commands
        if pattern.search(command) and (exclude is None or not exclude.search(command))
    ]

    count = len(matches)
    if args.min_count is not None:
        passed = count >= args.min_count
        expectation = f">= {args.min_count}"
    else:
        assert args.max_count is not None
        passed = count <= args.max_count
        expectation = f"<= {args.max_count}"

    print(f"pattern: {pattern_text}")
    print(f"matches: {count} (expected {expectation})")
    for match in matches:
        print(f"  {match}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
