#!/usr/bin/env python3
"""Validate that a file contains all expected strings.

Usage:
    python validate_file_contains.py <file_path> <string1> [string2 ...]

Exits 0 if all strings are found, 1 otherwise.
"""
import sys


def main():
    if len(sys.argv) < 3:
        print("Usage: validate_file_contains.py <file_path> <string1> [string2 ...]")
        sys.exit(1)

    file_path = sys.argv[1]
    expected = sys.argv[2:]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"FAIL: File not found: {file_path}")
        sys.exit(1)

    missing = [s for s in expected if s not in content]
    if missing:
        print(f"FAIL: Missing strings in {file_path}:")
        for s in missing:
            print(f"  - {s!r}")
        sys.exit(1)

    print(f"PASS: All {len(expected)} string(s) found in {file_path}")


if __name__ == "__main__":
    main()
