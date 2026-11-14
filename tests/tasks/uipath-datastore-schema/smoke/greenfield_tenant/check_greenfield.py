#!/usr/bin/env python3
"""Grades the Warehouse task: a tenant Schema resource with Product, StockLevel, a foreign key, and a guarded seed."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from schema_check import all_changes, check_resource, column_names, fail, lower_keys, schema_files, load_json  # noqa: E402

files = schema_files(os.getcwd())
if not files:
    fail("no Schema resource file under resources/solution_folder/schema/")
spec = None
for path in files:
    candidate = check_resource(load_json(open(path, encoding="utf-8").read(), path))
    tables = {body.get("tablename", "").lower() for name, body in all_changes(candidate) if name == "createtable"}
    if {"product", "stocklevel"} <= tables:
        spec = candidate
if spec is None:
    fail("no Schema resource creates both Product and StockLevel")
if str(spec.get("scope", "")).lower() != "tenant":
    fail(f"scope is {spec.get('scope')!r}; the tables are shared by the tenant")

changes = all_changes(spec)
product = next(body for name, body in changes if name == "createtable" and body["tablename"].lower() == "product")
if not {"id", "sku", "name", "price"} <= set(column_names(product)):
    fail(f"Product columns are {column_names(product)}")
columns = {lower_keys(c["column"])["name"].lower(): lower_keys(c["column"]) for c in product["columns"]}
if "uniqueidentifier" not in columns["id"]["type"].lower() and "uuid" not in columns["id"]["type"].lower():
    fail(f"Product.Id is {columns['id']['type']}, not a GUID")
if not lower_keys(columns["sku"].get("constraints", {})).get("unique"):
    fail("Product.Sku is not unique")
if not any(k.startswith("defaultvalue") for k in columns["price"]):
    fail("Product.Price has no default")

foreign_key = any(name == "addforeignkeyconstraint" and body.get("referencedtablename", "").lower() == "product" for name, body in changes) or any(
    name == "createtable" and body["tablename"].lower() == "stocklevel"
    and any(lower_keys(lower_keys(c["column"]).get("constraints", {})).get("referencedtablename", "").lower() == "product" for c in body["columns"])
    for name, body in changes)
if not foreign_key:
    fail("StockLevel has no foreign key to Product")

guarded = [
    changeset for changeset in spec["changesets"]
    if any(next(iter(c)).lower() == "insert" for c in lower_keys(changeset)["changes"])
]
if not guarded:
    fail("no insert seeds Product")
for changeset in guarded:
    conditions = lower_keys(changeset).get("preconditions") or []
    if not any("sqlcheck" in lower_keys(c) for c in conditions) or not any(str(lower_keys(c).get("onfail", "")).upper() == "MARK_RAN" for c in conditions):
        fail("the seed changeset is not guarded by a MARK_RAN sqlCheck precondition")
inserts = [body for name, body in changes if name == "insert" and body["tablename"].lower() == "product"]
if len(inserts) < 2:
    fail(f"{len(inserts)} Product rows seeded, not 2")
print("OK")
