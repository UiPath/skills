#!/usr/bin/env python3
"""Deterministically verify ID files produced by pagination walks."""

import argparse
import sys
from pathlib import Path


def load_ids(path: Path) -> list[str]:
    if not path.is_file():
        raise ValueError(f"file not found: {path}")
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def require_unique(ids: list[str], expected: int, label: str) -> None:
    if len(ids) != expected:
        raise ValueError(f"{label} has {len(ids)} IDs; expected {expected}")
    unique = set(ids)
    if len(unique) != expected:
        raise ValueError(
            f"{label} has {expected - len(unique)} duplicate ID occurrence(s)"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=("walk", "offset"))
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--count", type=int)
    parser.add_argument("--against", type=Path)
    parser.add_argument("--start", type=int)
    parser.add_argument("--stop", type=int)
    args = parser.parse_args()

    try:
        ids = load_ids(args.file)
        if args.mode == "walk":
            if args.count is None:
                raise ValueError("--count is required for walk mode")
            require_unique(ids, args.count, str(args.file))
            print(f"OK: {args.file} contains {len(ids)} unique IDs")
            return 0

        if args.against is None or args.start is None or args.stop is None:
            raise ValueError(
                "--against, --start and --stop are required for offset mode"
            )
        reference = load_ids(args.against)
        expected = reference[args.start : args.stop]
        if ids != expected:
            raise ValueError(
                f"{args.file} does not match "
                f"{args.against}[{args.start}:{args.stop}]"
            )
        print(
            f"OK: {args.file} matches "
            f"{args.against}[{args.start}:{args.stop}]"
        )
        return 0
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
