#!/usr/bin/env python3
"""Grades LeaveRules, authored from two CSV files.

`approval-matrix.csv` is one table: its rows never overlap, so its hit policy is UNIQUE,
it reads the `date` input `startDate`, and it answers with two columns. `required-documents.csv`
answers with every matching row, so its hit policy is COLLECT. The channel reads the approver
as `<approval decision>.approver`, the form Critical Rule 3 gives for a decision with several
outputs. The whole-file entry point must type each argument as `uip rules refresh` does.
"""

from __future__ import annotations

import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import decision_for_output, evaluate_graph, reference_name, required, same_value  # noqa: E402
from rules_check import (  # noqa: E402
    NS,
    fail,
    find_project,
    input_columns,
    load_graph,
    output_properties,
    read_entry_points,
)

PROJECT = "LeaveRules"
NEW_MATRIX = date(2027, 1, 1)
INPUT_TYPES = {"leaveType": {"type": "string"}, "startDate": {"type": "string", "format": "date"}, "days": {"type": "number"}}
OUTPUT_TYPES = {"approver": {"type": "string"}, "noticeDays": {"type": "number"},
                "documents": {"type": "array", "items": {"type": "string"}}, "channel": {"type": "string"}}


def expected(leave_type: str, start: date, days: int) -> dict:
    approver, notice = {"Annual": ("Manager", 14) if start < NEW_MATRIX else ("Team lead", 7),
                        "Sick": ("Team lead", 0), "Unpaid": ("Director", 30)}[leave_type]
    documents = ((["Medical certificate"] if leave_type == "Sick" and days >= 4 else [])
                 + (["Signed request form"] if leave_type == "Unpaid" else [])
                 + (["Coverage plan"] if days >= 11 else []))
    return {"approver": approver, "noticeDays": notice, "documents": documents,
            "channel": "Executive desk" if approver == "Director" else "Team inbox"}


CASES = [({"leaveType": kind, "startDate": start, "days": days}, expected(kind, start, days))
         for kind in ("Annual", "Sick", "Unpaid")
         for start in (date(2026, 12, 31), NEW_MATRIX, date(2027, 6, 30))
         for days in (1, 3, 4, 10, 11)]


def table(decision):
    found = decision.find("dmn:decisionTable", NS)
    if found is None:
        fail(f"decision {decision.get('name')!r} is not a decision table")
    return found


def check_shape(root) -> None:
    approval = decision_for_output(root, "approver")
    if decision_for_output(root, "noticeDays") is not approval:
        fail("approver and noticeDays come from different decisions; approval-matrix.csv is one table")
    if table(approval).get("hitPolicy", "UNIQUE") != "UNIQUE":
        fail(f"the approval table's hit policy is {table(approval).get('hitPolicy')}, expected UNIQUE: its rows never overlap")
    start = next((e for e in root.findall("dmn:inputData", NS) if e.get("name") == "startDate"), None)
    if start is None or start.find("dmn:variable", NS).get("typeRef") != "date":
        fail("input startDate is missing or not typed date")
    if "startDate" not in input_columns(table(approval)):
        fail("the approval table does not read startDate")

    documents = table(decision_for_output(root, "documents"))
    if documents.get("hitPolicy") != "COLLECT" or documents.get("aggregation"):
        fail(f"the documents table's hit policy is {documents.get('hitPolicy')} {documents.get('aggregation') or ''}, "
             f"expected COLLECT with no aggregation: a request needs every matching document")

    routing = decision_for_output(root, "channel")
    if approval.get("id") not in required(routing, "requiredDecision"):
        fail("the channel decision does not require the approval decision")
    read = f"{reference_name(approval)}.approver"
    if read not in input_columns(table(routing)):
        fail(f"the channel table reads {input_columns(table(routing))}, expected {read!r}: approval has two outputs")


def check_contract(project, dmn_file) -> None:
    entry = next((e for e in read_entry_points(project) if e.get("filePath") == f"/{dmn_file.name}"), None)
    if entry is None:
        fail(f"no entry point addresses /{dmn_file.name}; run `uip rules refresh`")
    declared_inputs = (entry.get("input") or {}).get("properties") or {}
    declared_outputs = output_properties(entry.get("output") or {})
    for kind, declared, wanted in (("input", declared_inputs, INPUT_TYPES), ("output", declared_outputs, OUTPUT_TYPES)):
        for name, schema in wanted.items():
            actual = {key: (declared.get(name) or {}).get(key) for key in schema}
            if actual != schema:
                fail(f"entry-points.json types {kind} {name} as {actual}, expected {schema}; run `uip rules refresh`")


def check_values(root) -> None:
    for inputs, want in CASES:
        actual = evaluate_graph(root, inputs)
        for name, value in want.items():
            got = actual.get(name)
            # COLLECT order is the engine's, so a list compares as a multiset.
            if isinstance(got, list) and isinstance(value, list):
                got, value = sorted(got), sorted(value)
            if name not in actual or not same_value(got, value):
                fail(f"{inputs} returned {name}={actual.get(name)!r}, expected {want[name]!r}")


def main() -> None:
    project = find_project(PROJECT)
    dmn_file, root = load_graph(project)
    check_shape(root)
    check_contract(project, dmn_file)
    check_values(root)
    print(f"OK: UNIQUE and COLLECT tables, a name.column read, typed contract, and all {len(CASES)} cases match")


if __name__ == "__main__":
    main()
