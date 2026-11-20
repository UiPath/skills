#!/usr/bin/env python3
"""Grading for the plain-description routing task of the uipath-rules skill.

The agent builds a BusinessRules project named ShippingFee from a prose policy, with no source document. The
point of the task is the route: a request with nothing to extract from must not enter the document-extraction
route, so no extraction artifact may exist. Modes:

  validate  `uip rules validate` passes on the ShippingFee project.
  shipping  authoring profile, entry-point contract, and the fee for every SCENARIO (the answer key; it never
            reaches the sandbox). The ranges must be intervals, never a comma list.
  names     every rule carries an annotation naming its case.
  route     no extraction artifact: no cites.json, no uipdm element in the .dmn.

DMN files are authored by the agent under test and parsed with stdlib ElementTree; helpers come from rules_check.py.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rules_check as rc  # noqa: E402

PROJECT_NAME = "ShippingFee"
INPUTS = {"weightKg": "number", "isPremium": "boolean"}
OUTPUTS = {"shippingFee": "number"}
SCENARIOS = [  # weightKg, isPremium -> fee
    ({"weightKg": 0.5, "isPremium": False}, 5.0),
    ({"weightKg": 1, "isPremium": False}, 8.0),
    ({"weightKg": 4.99, "isPremium": False}, 8.0),
    ({"weightKg": 5, "isPremium": False}, 15.0),
    ({"weightKg": 19.99, "isPremium": False}, 15.0),
    ({"weightKg": 20, "isPremium": False}, 30.0),
    ({"weightKg": 0.5, "isPremium": True}, 0.0),
    ({"weightKg": 4.99, "isPremium": True}, 0.0),
    ({"weightKg": 5, "isPremium": True}, 7.5),
    ({"weightKg": 19.99, "isPremium": True}, 7.5),
    ({"weightKg": 20, "isPremium": True}, 15.0),
    ({"weightKg": 50, "isPremium": True}, 15.0),
]
COMMA_RANGE = re.compile(r"[<>]=?\s*-?\d[\d.]*\s*,\s*[<>]")


def comma_range_cells(table) -> list[str]:
    """Input cells that spell a range as a comma list; in FEEL a comma means 'or', so such a cell matches every number."""
    cells = [(e.findtext("dmn:text", default="", namespaces=rc.NS) or "").strip()
             for rule in table.findall("dmn:rule", rc.NS) for e in rule.findall("dmn:inputEntry", rc.NS)]
    return [cell for cell in cells if COMMA_RANGE.search(cell)]


def extraction_leftovers(root: Path, dmn_text: str) -> list[str]:
    """What only the document-extraction route writes."""
    found = [str(path) for path in sorted(root.rglob("cites.json"))]
    if "uipdm" in dmn_text:
        found.append("a uipdm element or namespace in the .dmn")
    return found


def grade_shipping() -> None:
    project = rc.find_project(PROJECT_NAME)
    dmn_file, root = rc.load_rule(project)
    table = rc.table_of(root)
    rc.check_input_data(root, INPUTS)
    if rc.output_names(table) != list(OUTPUTS):
        rc.fail(f"output columns are {rc.output_names(table)}, expected {list(OUTPUTS)}")
    rc.check_contract(project, dmn_file, root, INPUTS, OUTPUTS)
    commas = comma_range_cells(table)
    if commas:
        rc.fail(f"ranges written as comma lists, which match every number: {commas}")
    rc.check_cases(table, "shippingFee", SCENARIOS)
    print(f"OK: profile holds, the entry point carries the contract, ranges are intervals, and all {len(SCENARIOS)} scenarios match")


def grade_route() -> None:
    project = rc.find_project(PROJECT_NAME)
    dmn_file, _ = rc.load_rule(project)
    found = extraction_leftovers(Path("."), dmn_file.read_text(encoding="utf-8"))
    if found:
        rc.fail("the extraction route ran for a request with no source document: " + "; ".join(found))
    print("OK: no extraction artifact (no cites.json, no uipdm element)")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "shipping"
    if mode == "validate":
        rc.run_validate(rc.find_project(PROJECT_NAME))
        print("OK: uip rules validate passes")
    elif mode == "shipping":
        grade_shipping()
    elif mode == "names":
        rc.check_named_rules(rc.table_of(rc.load_rule(rc.find_project(PROJECT_NAME))[1]))
        print("OK: every rule carries an annotation")
    elif mode == "route":
        grade_route()
    else:
        rc.fail(f"unknown mode {mode!r}")
