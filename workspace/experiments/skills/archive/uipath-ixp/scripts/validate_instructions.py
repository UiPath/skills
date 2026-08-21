#!/usr/bin/env python3
"""
Validate field or group instruction updates against the quality rules in the
improve-prompts-guide before sending them to the IXP API.

Usage:
  python validate_instructions.py --updates field_updates.json
  python validate_instructions.py --updates group_updates.json --min-length 80

Inputs:
  --updates     JSON file: array of {"name": "...", "instructions": "..."} objects
  --min-length  Minimum character length for an instruction (default: 120)

Output:
  Per-instruction pass/fail table with specific failure reasons to stdout.
  Exit 0 if all instructions pass hard rules.
  Exit 1 if any instruction fails a hard rule (warnings do not affect exit code).

Hard rules (exit 1):
  - instruction length < --min-length
  - no location-hint keyword present

Warnings (logged but exit 0):
  - no "Example:" in instruction
  - "Format:" pattern present (may conflict with entity_def type)
"""

import argparse
import json
import re
import sys

LOCATION_KEYWORDS = ["section", "header", "table", "top of", "bottom of", "labeled", "label", "near", "found in", "found at", "located"]
FORMAT_PATTERN = re.compile(r"\bFormat\s*:", re.IGNORECASE)
EXAMPLE_PATTERN = re.compile(r"\bExample\s*:", re.IGNORECASE)


def check_instruction(name, instruction, min_length):
    errors = []
    warnings = []

    length = len(instruction)
    if length < min_length:
        errors.append(f"too short ({length} chars, need {min_length}+)")

    text_lower = instruction.lower()
    if not any(kw in text_lower for kw in LOCATION_KEYWORDS):
        errors.append(f"no location-hint keyword ({', '.join(LOCATION_KEYWORDS[:5])}, …)")

    if FORMAT_PATTERN.search(instruction):
        warnings.append('contains "Format:" — may conflict with entity_def type; remove it')

    if not EXAMPLE_PATTERN.search(instruction):
        warnings.append('no "Example:" — consider adding a real value from the documents')

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--updates", required=True, help="JSON array of {name, instructions} objects")
    parser.add_argument("--min-length", type=int, default=120, help="Minimum instruction length (default: 120)")
    args = parser.parse_args()

    with open(args.updates) as f:
        updates = json.load(f)

    if not isinstance(updates, list):
        print("ERROR: --updates file must be a JSON array.", file=sys.stderr)
        sys.exit(2)

    any_errors = False
    print(f"Validating {len(updates)} instruction(s)  (min-length: {args.min_length})\n")

    for entry in updates:
        name = entry.get("name", "<unnamed>")
        instruction = entry.get("instructions", "")
        errors, warnings = check_instruction(name, instruction, args.min_length)
        status = "PASS" if not errors else "FAIL"
        if errors:
            any_errors = True
        print(f"[{status}] {name}")
        print(f"       length: {len(instruction)} chars")
        for e in errors:
            print(f"       ERROR: {e}")
        for w in warnings:
            print(f"       WARN:  {w}")
        print()

    if any_errors:
        print("Validation FAILED — fix the ERRORs above before running `fields update-prompts`.")
        sys.exit(1)
    else:
        print("All instructions passed hard rules.")


if __name__ == "__main__":
    main()
