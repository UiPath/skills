#!/usr/bin/env python3
"""Assert the ExpenseReimbursement SDD preserves record-created intake.

The expense scenario is not just a manual case with expense-shaped variables.
It starts from a tenant case-entity record-created event on `expense_requests`,
keeps the companion objects named by the user, and maps the intake fields from
that trigger payload into case variables.
"""

from __future__ import annotations

import re
import sys


CORE_FIELDS = {
    "employeeName": "employee_name",
    "employeeEmail": "employee_email",
    "department": "department",
    "expenseType": "expense_type",
    "amount": "amount",
    "currency": "currency",
    "description": "description",
    "receiptUrl": "receipt_url",
    "submittedDate": "submitted_date",
}


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _section(text: str, heading: str) -> str:
    pattern = rf"^### +{re.escape(heading)}\s*$([\s\S]*?)(?=^### +|\Z)"
    match = re.search(pattern, text, re.M)
    if not match:
        _fail(f"missing section: {heading}")
    return match.group(1)


def _rows(section: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        if not cells or cells[0] in {"T#", "Name"} or set(cells[0]) <= {"-", ":"}:
            continue
        rows.append(cells)
    return rows


def _case_variable_rows(text: str) -> dict[str, list[str]]:
    variables = _section(text, "Case Variables")
    by_name: dict[str, list[str]] = {}
    for cells in _rows(variables):
        if len(cells) >= 6 and re.match(r"^[A-Za-z]\w*$", cells[0]):
            by_name[cells[0]] = cells
    if not by_name:
        _fail("no Case Variables rows found")
    return by_name


def main() -> None:
    if len(sys.argv) != 2:
        _fail("usage: check_expense_trigger_sdd.py <sdd.md|sdd.draft.md>")

    path = sys.argv[1]
    text = open(path, encoding="utf-8").read()
    lowered = text.lower()

    for object_name in ("expense_requests", "expense_documents", "expense_comments"):
        if object_name not in lowered:
            _fail(f"missing required expense data object {object_name!r}")

    triggers = _section(text, "Case Triggers")
    trigger_rows = _rows(triggers)
    event_rows = [
        row
        for row in trigger_rows
        if len(row) >= 4
        and row[1].lower() == "intsvc.eventtrigger"
        and "expense_requests" in row[2].lower()
    ]
    if not event_rows:
        _fail(
            "Case Triggers must declare an Intsvc.EventTrigger sourced from "
            "expense_requests"
        )
    if not any("record" in row[3].lower() and "created" in row[3].lower() for row in event_rows):
        _fail("expense_requests trigger configuration must say record created")

    manual_rows = [
        row
        for row in trigger_rows
        if len(row) >= 3 and row[1].lower() == "manual"
    ]
    if manual_rows:
        _fail(f"expense intake must not be downgraded to Manual trigger: {manual_rows}")

    variables = _case_variable_rows(text)
    missing_vars = sorted(set(CORE_FIELDS) - set(variables))
    if missing_vars:
        _fail("missing core trigger-sourced variable(s): " + ", ".join(missing_vars))

    bad_mappings = []
    for var_name, source_field in CORE_FIELDS.items():
        row = variables[var_name]
        category = row[1]
        source_triggers = row[3]
        source_fields = row[4]
        if category != "Variable":
            bad_mappings.append(f"{var_name}: category {category!r}, expected Variable")
        if source_triggers != "T02":
            bad_mappings.append(f"{var_name}: sourceTriggers {source_triggers!r}, expected T02")
        if source_field not in source_fields:
            bad_mappings.append(
                f"{var_name}: sourceFields {source_fields!r}, expected to include {source_field!r}"
            )
    if bad_mappings:
        _fail("bad trigger payload mappings:\n  - " + "\n  - ".join(bad_mappings))

    print(
        "OK: ExpenseReimbursement SDD preserves expense_requests record-created "
        "trigger, companion objects, and trigger-sourced intake field mappings"
    )


if __name__ == "__main__":
    main()
