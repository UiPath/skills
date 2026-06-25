#!/usr/bin/env python3
"""Verify ID files produced by ``extract_page_ids.py``.

Three modes — pick one per invocation:

    --mode walk    ``--file`` has exactly ``--count`` IDs and no duplicates.
    --mode offset  ``--file`` equals ``--against[--start:--stop]``.
    --mode count   ``--file`` has exactly ``--count`` IDs (no uniqueness check).

Usage:
    verify_pagination.py --mode walk   --file walk_ids.txt        --count 500
    verify_pagination.py --mode offset --file offset_page_ids.txt --against walk_ids.txt --start 180 --stop 240
    verify_pagination.py --mode count  --file active_ids.txt      --count 300

Exit code:
    0 on success (prints ``OK: ...`` to stdout).
    1 on assertion failure (prints ``FAIL: ...`` to stderr).
"""

import argparse
import sys
from pathlib import Path


def load_ids(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        print(f"FAIL: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return [line.strip() for line in p.read_text().splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--mode", required=True, choices=("walk", "offset", "count"))
    parser.add_argument("--file", required=True, help="ID file to verify")
    parser.add_argument("--count", type=int, help="Expected count (walk / count modes)")
    parser.add_argument("--against", help="Reference ID file (offset mode)")
    parser.add_argument("--start", type=int, help="Start index in reference (offset mode)")
    parser.add_argument("--stop", type=int, help="Stop index in reference (offset mode)")
    args = parser.parse_args()

    ids = load_ids(args.file)

    if args.mode == "walk":
        if args.count is None:
            print("FAIL: --count required for walk mode", file=sys.stderr)
            return 1
        if len(ids) != args.count:
            print(f"FAIL: {args.file} has {len(ids)} IDs, expected {args.count}", file=sys.stderr)
            return 1
        if len(set(ids)) != args.count:
            print(f"FAIL: duplicate IDs in {args.file}", file=sys.stderr)
            return 1
        print(f"OK: {len(ids)} unique IDs")
        return 0

    if args.mode == "offset":
        if not args.against or args.start is None or args.stop is None:
            print("FAIL: --against, --start, --stop required for offset mode", file=sys.stderr)
            return 1
        ref = load_ids(args.against)
        expected = ref[args.start : args.stop]
        if len(ids) != (args.stop - args.start):
            print(
                f"FAIL: {args.file} has {len(ids)} IDs, expected {args.stop - args.start}",
                file=sys.stderr,
            )
            return 1
        if ids != expected:
            print(
                f"FAIL: {args.file} does not equal {args.against}[{args.start}:{args.stop}]",
                file=sys.stderr,
            )
            return 1
        print(f"OK: {args.file} matches {args.against}[{args.start}:{args.stop}]")
        return 0

    # count
    if args.count is None:
        print("FAIL: --count required for count mode", file=sys.stderr)
        return 1
    if len(ids) != args.count:
        print(f"FAIL: {args.file} has {len(ids)} IDs, expected {args.count}", file=sys.stderr)
        return 1
    print(f"OK: {len(ids)} IDs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
