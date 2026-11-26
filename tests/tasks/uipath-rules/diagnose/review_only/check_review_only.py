#!/usr/bin/env python3
"""Grades the review of SupplierChecks, a UNIQUE table with one gap and one overlap.

The fixture leaves High-risk suppliers below 20000 matching no row, and Medium-risk
suppliers from 80000 up to 100000 matching two. `review.json` lists example inputs under
`gaps` and `overlaps`. Each example is graded by evaluating the fixture's own table: a gap
example must match no row, an overlap example two or more, and every example must be an input
the caller can send. So the file passes only when it names inputs that really hit each fault.
The `.dmn` must be byte-identical: a review changes nothing.
"""

from __future__ import annotations

import filecmp
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from rules_check import NS, fail, find_project, input_columns, unary_test  # noqa: E402

PROJECT = "SupplierChecks"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / f"{PROJECT}Solution" / PROJECT
RISK_LEVELS = ("Low", "Medium", "High")


def matching_rows(table: ET.Element, inputs: dict) -> int:
    columns = input_columns(table)
    return sum(1 for rule in table.findall("dmn:rule", NS)
               if all(unary_test(e.findtext("dmn:text", default="", namespaces=NS) or "", inputs[column])
                      for e, column in zip(rule.findall("dmn:inputEntry", NS), columns)))


def example(entry: object, kind: str) -> dict:
    if not isinstance(entry, dict):
        fail(f"a {kind} entry is {entry!r}, expected an object with annualSpend and riskLevel")
    spend, risk = entry.get("annualSpend"), entry.get("riskLevel")
    if isinstance(spend, bool) or not isinstance(spend, (int, float)) or spend < 0:
        fail(f"{kind} example {entry} has no annualSpend the caller can send (a number, 0 or more)")
    if risk not in RISK_LEVELS:
        fail(f"{kind} example {entry} has riskLevel {risk!r}; the caller sends one of {list(RISK_LEVELS)}")
    return {"annualSpend": spend, "riskLevel": risk}


def main() -> None:
    project = find_project(PROJECT)
    for file in sorted(p.relative_to(FIXTURE) for p in FIXTURE.rglob("*") if p.is_file()):
        if not (project / file).is_file() or not filecmp.cmp(FIXTURE / file, project / file, shallow=False):
            fail(f"{PROJECT}/{file} changed or is gone; the request was a review, not a fix")
    try:
        review = json.loads(Path("review.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        fail(f"review.json is missing or not JSON: {error}")
    table = ET.parse(FIXTURE / "Business rule.dmn").getroot().find("dmn:decision/dmn:decisionTable", NS)
    for kind, wanted, check in (("gaps", "match no row", lambda n: n == 0), ("overlaps", "match two or more rows", lambda n: n >= 2)):
        entries = review.get(kind) if isinstance(review, dict) else None
        if not isinstance(entries, list) or not entries:
            fail(f"review.json lists no {kind}; the table has one")
        for entry in entries:
            inputs = example(entry, kind)
            if not check(matching_rows(table, inputs)):
                fail(f"{kind} example {inputs} matches {matching_rows(table, inputs)} rows; a {kind[:-1]} must {wanted}")
    print("OK: every gap and overlap example hits the fault it names, and the rule is unchanged")


if __name__ == "__main__":
    main()
