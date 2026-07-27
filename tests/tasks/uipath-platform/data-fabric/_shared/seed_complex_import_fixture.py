#!/usr/bin/env python3
"""Create the temporary complex-field entity used by the CSV smoke test."""

import json
import subprocess
import sys


def uip(*args: str) -> dict:
    result = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return json.loads(result.stdout)


def items(payload: dict) -> list[dict]:
    data = payload.get("Data") or {}
    if isinstance(data, list):
        return data
    return data.get("Items") or data.get("Records") or []


def find_by_name(payload: dict, name: str) -> dict:
    for item in items(payload):
        if item.get("Name") == name:
            return item
    raise RuntimeError(f"required fixture {name!r} was not found")


def main() -> None:
    try:
        entities = uip("df", "entities", "list", "--native-only")
        if any(item.get("Name") == "CE_SmokeExpenseImport" for item in items(entities)):
            print("OK: CE_SmokeExpenseImport already exists")
            return

        customer = find_by_name(entities, "CE_SmokeImportCustomers")
        customer_id = customer.get("Id") or customer.get("ID")
        customer_schema = uip("df", "entities", "get", customer_id)
        fields = (customer_schema.get("Data") or {}).get("Fields") or []
        name_field = next(field for field in fields if field.get("Name") == "Name")

        choice_sets = uip("df", "choice-sets", "list")
        categories = find_by_name(choice_sets, "CE_SmokeCategories")
        tags = find_by_name(choice_sets, "CE_SmokeImportTags")

        body = {
            "displayName": "Expense Import Demo",
            "fields": [
                {"fieldName": "Amount", "displayName": "Amount", "type": "DECIMAL", "decimalPrecision": 2},
                {"fieldName": "Description", "displayName": "Description", "type": "STRING"},
                {
                    "fieldName": "Category",
                    "displayName": "Category",
                    "type": "CHOICE_SET_SINGLE",
                    "choiceSetId": categories.get("Id") or categories.get("ID"),
                },
                {
                    "fieldName": "Tags",
                    "displayName": "Tags",
                    "type": "CHOICE_SET_MULTIPLE",
                    "choiceSetId": tags.get("Id") or tags.get("ID"),
                },
                {
                    "fieldName": "Customer",
                    "displayName": "Customer",
                    "type": "RELATIONSHIP",
                    "referenceEntityId": customer_id,
                    "referenceFieldId": name_field.get("Id") or name_field.get("ID"),
                },
            ],
        }
        created = uip(
            "df",
            "entities",
            "create",
            "CE_SmokeExpenseImport",
            "--body",
            json.dumps(body),
        )
        created_id = (created.get("Data") or {}).get("Id") or (created.get("Data") or {}).get("ID")
        print(f"OK: created CE_SmokeExpenseImport ({created_id})")
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
