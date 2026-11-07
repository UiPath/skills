#!/usr/bin/env python3
"""Grades the Helpdesk package: a folder Schema resource with Ticket, TicketComment, and a cascading key, inside the .zip."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from schema_check import all_changes, check_resource, column_names, fail, load_json, lower_keys  # noqa: E402
import glob  # noqa: E402
import zipfile  # noqa: E402

archives = [p for p in glob.glob(os.path.join(os.getcwd(), "**", "*.zip"), recursive=True)]
spec = None
for archive in archives:
    with zipfile.ZipFile(archive) as package:
        for entry in package.namelist():
            if entry.startswith("resources/solution_folder/schema/") and entry.endswith(".json"):
                candidate = check_resource(load_json(package.read(entry).decode("utf-8"), entry))
                tables = {body.get("tablename", "").lower() for name, body in all_changes(candidate) if name == "createtable"}
                if {"ticket", "ticketcomment"} <= tables:
                    spec = candidate
if spec is None:
    fail(f"no packed Schema resource creates Ticket and TicketComment (archives: {archives})")
if str(spec.get("scope", "folder")).lower() != "folder":
    fail(f"scope is {spec.get('scope')!r}; each folder gets its own tables")
changes = all_changes(spec)
ticket = next(body for name, body in changes if name == "createtable" and body["tablename"].lower() == "ticket")
if not {"id", "title", "status", "createdat"} <= set(column_names(ticket)):
    fail(f"Ticket columns are {column_names(ticket)}")
status = next(lower_keys(c["column"]) for c in ticket["columns"] if lower_keys(c["column"])["name"].lower() == "status")
if str(status.get("defaultvalue", "")) != "Open":
    fail("Ticket.Status does not default to Open")
cascade = any(name == "addforeignkeyconstraint" and body.get("referencedtablename", "").lower() == "ticket"
              and str(body.get("ondelete", "")).upper() == "CASCADE" for name, body in changes) or any(
    name == "createtable" and body["tablename"].lower() == "ticketcomment"
    and any(lower_keys(lower_keys(c["column"]).get("constraints", {})).get("referencedtablename", "").lower() == "ticket"
            and lower_keys(lower_keys(c["column"]).get("constraints", {})).get("deletecascade") for c in body["columns"])
    for name, body in changes)
if not cascade:
    fail("TicketComment has no cascading foreign key to Ticket")
print("OK")
