#!/usr/bin/env python3
"""Create the temporary complex-field entity used by the CSV smoke test."""

import json
import subprocess
import sys
from pathlib import Path

import seed_choice_set


SEED_DIR = Path(__file__).with_name("seeds")


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


def ensure_choice_set(spec_name: str) -> str:
    """Return the choice-set ID directly, including immediately after create."""
    spec = json.loads((SEED_DIR / spec_name).read_text())
    name = spec["name"]
    choice_set_id = seed_choice_set.find_choice_set(name)
    if not choice_set_id:
        choice_set_id = seed_choice_set.create_choice_set(
            name,
            spec.get("displayName") or name,
            spec.get("description") or "",
        )
    if not choice_set_id:
        raise RuntimeError(f"could not create or resolve choice set {name!r}")

    existing = seed_choice_set.list_value_names(choice_set_id)
    for value in spec["values"]:
        if value.lower() not in existing and not seed_choice_set.create_value(
            choice_set_id, value, value.capitalize()
        ):
            raise RuntimeError(f"could not seed value {value!r} on choice set {name!r}")
    return choice_set_id


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

        category_id = ensure_choice_set("smoke_categories.choice_set.json")
        tags_id = ensure_choice_set("smoke_import_tags.choice_set.json")

        body = {
            "displayName": "Expense Import Demo",
            "fields": [
                {"fieldName": "Amount", "displayName": "Amount", "type": "DECIMAL", "decimalPrecision": 2},
                {"fieldName": "Description", "displayName": "Description", "type": "STRING"},
                {
                    "fieldName": "Category",
                    "displayName": "Category",
                    "type": "CHOICE_SET_SINGLE",
                    "choiceSetId": category_id,
                },
                {
                    "fieldName": "Tags",
                    "displayName": "Tags",
                    "type": "CHOICE_SET_MULTIPLE",
                    "choiceSetId": tags_id,
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
