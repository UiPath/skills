#!/usr/bin/env python3
"""Grades contract.json for FreightRates against the mocked `describe` answer.

The schemas exist only in the mock's `rules describe` body, so a file that matches them
was copied from that call, not written from the prompt. The folder is graded too: the
prompt does not name it, and only `rules list --all-folders` reveals it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

FOLDER = "Operations/Freight"
INPUT = {"type": "object", "properties": {"parcelWeightKg": {"type": "number", "title": "parcelWeightKg"},
                                          "destinationZone": {"type": "string", "title": "destinationZone"}},
         "required": []}
OUTPUT = {"type": "object", "properties": {"freight": {"type": "object", "properties": {
    "rateEur": {"type": "number"}, "carrierCode": {"type": "string"}}}},
          "required": [], "x-uipath-decision-keyed": True}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def as_object(value: object, field: str) -> object:
    """`describe` prints each schema as a JSON string; a file may keep it a string or parse it."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            fail(f"contract.json `{field}` is a string that is not JSON")
    return value


def main() -> None:
    try:
        contract = json.loads(Path("contract.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        fail(f"contract.json is missing or not JSON: {error}")
    if not isinstance(contract, dict):
        fail("contract.json is not a JSON object")
    if contract.get("folderPath") != FOLDER:
        fail(f"folderPath is {contract.get('folderPath')!r}, expected {FOLDER!r}, the folder `list --all-folders` shows")
    for field, wanted in (("input", INPUT), ("output", OUTPUT)):
        if as_object(contract.get(field), field) != wanted:
            fail(f"`{field}` is not the {field} argument schema `rules describe` returned")
    print("OK: contract.json names the folder and holds the described input and output schemas")


if __name__ == "__main__":
    main()
