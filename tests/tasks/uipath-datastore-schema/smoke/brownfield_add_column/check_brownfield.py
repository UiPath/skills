#!/usr/bin/env python3
"""Grades the Catalog edit: changeset 1 and the key untouched, a new changeset with the column and the index."""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "_shared"))

from schema_check import changes_of, check_resource, column_names, fail, find_schema, load_json, lower_keys  # noqa: E402

ORIGINAL = os.path.join(HERE, "fixtures", "Inventory", "resources", "solution_folder", "schema", "Catalog.json")

path, document = find_schema(os.getcwd(), "Catalog")
spec = check_resource(document)
original = json.load(open(ORIGINAL, encoding="utf-8"))
if document["resource"]["key"] != original["resource"]["key"]:
    fail("the resource key changed; upgrades find the deployed schema by it")
installed = original["resource"]["spec"]["changesets"][0]
current = [c for c in spec["changesets"] if lower_keys(c)["changeset"] == 1]
if not current or json.dumps(current[0], sort_keys=True) != json.dumps(installed, sort_keys=True):
    fail("changeset 1 was edited; installed changesets must stay exactly as deployed")
newer = [lower_keys(c)["changeset"] for c in spec["changesets"] if lower_keys(c)["changeset"] > 1]
if not newer:
    fail("no changeset numbered above 1")
changes = [change for number in newer for change in changes_of(spec, number)]
added = [body for name, body in changes if name == "addcolumn" and body.get("tablename", "").lower() == "product" and "description" in column_names(body)]
if not added:
    fail("no addColumn adds Description to Product")
description = next(lower_keys(c["column"]) for c in added[0]["columns"] if lower_keys(c["column"])["name"].lower() == "description")
if lower_keys(description.get("constraints", {})).get("nullable") is False:
    fail("Description must be optional")
indexed = [body for name, body in changes if name == "createindex" and body.get("tablename", "").lower() == "product"
           and "name" in [str(lower_keys(c["column"]).get("name", "")).lower() for c in body.get("columns", [])]]
if not indexed:
    fail("no createIndex on Product(Name)")
print("OK")
