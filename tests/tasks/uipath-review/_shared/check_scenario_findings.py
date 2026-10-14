#!/usr/bin/env python3
"""Grade a multi-defect low-code review scenario from the saved report.

Reads `scenario.json` and the report's finding rows. Prints one HIT/MISS line
per planted rule and one DECOY line per fired decoy. Exit 0 on PASS;
sys.exit(str) on failure.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from report_evidence import run_review_cli

TABLE_ROW = re.compile(r"^\s*\|\s*([CWI])-(?:D-)?\d+\s*\|(.*)$", re.MULTILINE)
VALIDATION_ROW = re.compile(r"^\s*-\s*\[V-([EW])-\d+\](.*)$", re.MULTILINE)
RULE_ID = re.compile(r"(?<![A-Za-z0-9_])[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+(?![A-Za-z0-9_])")
FINAL_GRADE = re.compile(r"\*\*Final grade: ([ABCDF])\*\*\s*\Z")
GRADES = "ABCDF"
MIN_REPORT_BYTES = 1500


def finding_rows(text: str) -> list[tuple[str, str, bool]]:
    rows = [(m.group(1), m.group(2), True) for m in TABLE_ROW.finditer(text)]
    rows += [("C" if m.group(1) == "E" else "W", m.group(2), False) for m in VALIDATION_ROW.finditer(text)]
    return rows


def _row_hits(item: dict, rows: list[tuple[str, str, bool]]) -> bool:
    pattern = re.compile(item["pattern"], re.IGNORECASE) if item.get("pattern") else None
    for _, body, _ in rows:
        if set(item["ids"]) & set(RULE_ID.findall(body)) and (pattern is None or pattern.search(body)):
            return True
    return False


def _decoy_fired(decoy: dict, rows: list[tuple[str, str, bool]]) -> bool:
    for _, body, _ in rows:
        if decoy["id"] in RULE_ID.findall(body) and decoy.get("element", "") in body:
            return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--report", default="_review_report.md")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    report = Path(os.getcwd()) / args.report
    if not report.is_file():
        sys.exit(f"FAIL: {report} not found")
    text = report.read_text(encoding="utf-8", errors="replace")
    if len(text) < MIN_REPORT_BYTES:
        sys.exit(f"FAIL: report is suspiciously short ({len(text)} bytes)")

    rows = finding_rows(text)
    failures: list[str] = []

    expected = spec.get("expected", [])
    hits = []
    for item in expected:
        hit = _row_hits(item, rows)
        print(f"{'HIT ' if hit else 'MISS'} {'|'.join(item['ids'])} [{item['category']}]")
        if hit:
            hits.append(item)
    recall = len(hits) / len(expected) if expected else 1.0
    if recall < spec.get("min_recall", 1.0):
        failures.append(f"recall {recall:.2f} < {spec['min_recall']:.2f}")

    for decoy in spec.get("decoys", []):
        if _decoy_fired(decoy, rows):
            print(f"DECOY {decoy['id']} fired ({decoy['reason']})")
            failures.append(f"decoy {decoy['id']} cited in a finding row")

    categories = {item["category"] for item in hits}
    if len(categories) < spec.get("min_categories", 0):
        failures.append(f"categories {len(categories)} < {spec['min_categories']}")

    bands = {band for band, _, _ in rows}
    if len(bands) < spec.get("min_severity_bands", 0):
        failures.append(f"severity bands {sorted(bands)} < {spec['min_severity_bands']}")

    table_rows = [r for r in rows if r[2]]
    if spec.get("max_findings") is not None and len(table_rows) > spec["max_findings"]:
        failures.append(f"findings {len(table_rows)} > {spec['max_findings']}")
    for band in spec.get("forbidden_bands", []):
        if any(r[0] == band for r in table_rows):
            failures.append(f"forbidden band {band} present")

    m = FINAL_GRADE.search(text)
    if not m:
        failures.append("no `**Final grade: X**` footer as the last line")
    else:
        final = m.group(1)
        print(f"Final grade {final}")
        allowed = spec.get("allowed_grades", list(GRADES))
        if final not in allowed:
            failures.append(f"final grade {final} not in {allowed}")
        if spec.get("grade_not_above_cli", True):
            uip = os.environ.get("UIP", "uip")
            ok, data, why = run_review_cli(uip, ["agent", "review"], spec["project"])
            cli_grade = (data.get("Grade") or "")[:1] if ok else ""
            if cli_grade in GRADES and cli_grade:
                if GRADES.index(final) < GRADES.index(cli_grade):
                    failures.append(f"final grade {final} is better than CLI Data.Grade {cli_grade}")
            else:
                print(f"WARN: grade ceiling not checked ({why or 'no Data.Grade'})")

    if failures:
        sys.exit("FAIL: " + "; ".join(failures))
    print("PASS")


if __name__ == "__main__":
    main()
