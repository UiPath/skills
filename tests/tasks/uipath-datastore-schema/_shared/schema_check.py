#!/usr/bin/env python3
"""Shared checks for Data Store Schema resource tasks.

`check_resource` applies the grammar Data Service enforces at deploy (the
subset a task can break): the resource shape, scope and order, changeset properties and
numbers, supported changes, the `{ "column": … }` wrapper, column types, and
decimal values written as strings. Task scripts add scenario assertions.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
import uuid
import zipfile

CHANGESET_PROPERTIES = {"changeset", "changes", "preconditions"}
CHANGES = {
    "createtable", "addcolumn", "dropcolumn", "modifydatatype", "createindex", "dropindex",
    "addforeignkeyconstraint", "dropforeignkeyconstraint", "insert", "update", "delete", "setcolumnremarks",
}
COLUMN_PROPERTIES = {
    "name", "type", "constraints", "remarks",
    "defaultvalue", "defaultvaluenumeric", "defaultvalueboolean", "defaultvaluedate",
    "value", "valuenumeric", "valueboolean", "valuedate",
}
TYPE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9]*)\s*(\(\s*(\d{1,5}|MAX)\s*(,\s*\d{1,5}\s*)?\))?\s*$", re.IGNORECASE)
TYPES = {
    "bigint", "int", "smallint", "tinyint", "bit", "money", "smallmoney", "real", "date", "datetime", "smalldatetime",
    "uniqueidentifier", "decimal", "numeric", "float", "time", "datetime2", "datetimeoffset", "char", "binary",
    "varchar", "varbinary", "nchar", "nvarchar", "boolean", "integer", "double", "currency", "uuid", "timestamp",
    "clob", "nclob", "text", "ntext", "blob", "image",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def load_json(text: str, where: str) -> dict:
    # Decimal JSON numbers must not be rounded into floats before they are checked.
    try:
        return json.loads(text, parse_float=lambda raw: ("__FLOAT__", raw))
    except ValueError as error:
        fail(f"{where} is not valid JSON: {error}")


def schema_files(root: str) -> list[str]:
    return sorted(glob.glob(os.path.join(root, "**", "resources", "solution_folder", "schema", "*.json"), recursive=True))


def find_schema(root: str, name: str) -> tuple[str, dict]:
    for path in schema_files(root):
        document = load_json(open(path, encoding="utf-8").read(), path)
        spec = document.get("resource", {}).get("spec", {})
        if str(spec.get("name", "")).lower() == name.lower():
            return path, document
    fail(f"no Schema resource named {name} under {root} (found: {schema_files(root)})")


def lower_keys(value: dict) -> dict:
    return {key.lower(): item for key, item in value.items()}


def walk_floats(value, path: str) -> None:
    if isinstance(value, tuple) and value and value[0] == "__FLOAT__":
        fail(f"{path} is the JSON number {value[1]}; decimal numbers must be strings")
    if isinstance(value, dict):
        for key, item in value.items():
            walk_floats(item, f"{path}.{key}")
    if isinstance(value, list):
        for index, item in enumerate(value):
            walk_floats(item, f"{path}[{index}]")


def check_column(column: dict, path: str) -> None:
    if set(column) != {"column"} or not isinstance(column["column"], dict):
        fail(f"{path} must be {{ \"column\": {{ … }} }}")
    body = lower_keys(column["column"])
    unknown = set(body) - COLUMN_PROPERTIES
    if unknown:
        fail(f"{path}.column has unsupported properties {sorted(unknown)}")
    if "type" in body:
        match = TYPE.match(str(body["type"]))
        if not match or match.group(1).lower() not in TYPES:
            fail(f"{path}.column type '{body['type']}' is not supported")


def check_resource(document: dict) -> dict:
    resource = document.get("resource")
    if not isinstance(resource, dict) or str(resource.get("kind", "")).lower() != "schema":
        fail("the file is not a Schema resource (resource.kind must be schema)")
    try:
        uuid.UUID(str(resource.get("key")))
    except ValueError:
        fail(f"resource.key '{resource.get('key')}' is not a GUID")
    spec = resource.get("spec") or {}
    if str(spec.get("scope", "Folder")).lower() not in {"folder", "tenant"}:
        fail(f"spec.scope '{spec.get('scope')}' must be Folder or Tenant")
    order = spec.get("order")
    if order not in (None, "") and not (
        (type(order) is int and 0 <= order <= 999_999_999) or (isinstance(order, str) and re.fullmatch(r"[0-9]{1,9}", order))
    ):
        shown = order[1] if isinstance(order, tuple) else json.dumps(order)
        fail(f"spec.order {shown} must be a whole number from 0 to 999999999")
    changesets = spec.get("changesets")
    if not isinstance(changesets, list) or not changesets:
        fail("spec.changesets must be a non-empty array")
    walk_floats(changesets, "changesets")
    numbers = []
    for index, changeset in enumerate(changesets):
        path = f"changesets[{index}]"
        if not isinstance(changeset, dict):
            fail(f"{path} must be an object")
        keys = lower_keys(changeset)
        unknown = set(keys) - CHANGESET_PROPERTIES
        if unknown:
            fail(f"{path} has unsupported properties {sorted(unknown)}")
        number = keys.get("changeset")
        if type(number) is not int or not 1 <= number <= 999_999_999:
            fail(f"{path}.changeset must be a whole number from 1 to 999999999, not {number!r}")
        numbers.append(number)
        changes = keys.get("changes")
        if not isinstance(changes, list) or not changes:
            fail(f"{path}.changes must list at least one change")
        for change_index, change in enumerate(changes):
            change_path = f"{path}.changes[{change_index}]"
            if not isinstance(change, dict) or len(change) != 1:
                fail(f"{change_path} must hold exactly one change")
            name, body = next(iter(change.items()))
            if name.lower() not in CHANGES:
                fail(f"{change_path}: '{name}' is not a supported change")
            for column_index, column in enumerate(lower_keys(body).get("columns") or []):
                if name.lower() in {"createtable", "addcolumn", "insert", "update"}:
                    check_column(column, f"{change_path}.{name}.columns[{column_index}]")
    if len(set(numbers)) != len(numbers):
        fail(f"changeset numbers repeat: {numbers}")
    return spec


def changes_of(spec: dict, number: int) -> list[tuple[str, dict]]:
    for changeset in spec["changesets"]:
        if lower_keys(changeset)["changeset"] == number:
            return [(next(iter(change)).lower(), lower_keys(next(iter(change.values())))) for change in lower_keys(changeset)["changes"]]
    fail(f"no changeset {number}")


def all_changes(spec: dict) -> list[tuple[str, dict]]:
    return [change for changeset in spec["changesets"] for change in changes_of(spec, lower_keys(changeset)["changeset"])]


def column_names(body: dict) -> list[str]:
    return [str(lower_keys(column["column"]).get("name", "")).lower() for column in body.get("columns") or []]


def schema_in_zip(root: str, name: str) -> dict:
    archives = [path for path in glob.glob(os.path.join(root, "**", "*.zip"), recursive=True) if os.path.isfile(path)]
    for archive in archives:
        with zipfile.ZipFile(archive) as package:
            for entry in package.namelist():
                if entry.startswith("resources/solution_folder/schema/") and entry.endswith(".json"):
                    document = load_json(package.read(entry).decode("utf-8"), f"{archive}:{entry}")
                    if str(document.get("resource", {}).get("spec", {}).get("name", "")).lower() == name.lower():
                        return document
    fail(f"no packed solution under {root} holds the Schema resource {name} (archives: {archives})")
