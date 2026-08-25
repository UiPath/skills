#!/usr/bin/env python3
"""Shared data-grounded check for TM connector CRUD tasks.

Proves a REAL create->read round-trip through the connector (not just invocation):
the value the agent retrieved by Get must equal the unique seeded value it created.

Reads:
  seed.json   (pre_run) -> {"name": "<unique>", ...}
  result.json (agent)   -> {"created_name", "retrieved_name", "id"}
"""
import json
import sys


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    try:
        seed = json.load(open("seed.json", encoding="utf-8"))
    except OSError:
        fail("seed.json missing (pre_run did not run)")
    try:
        res = json.load(open("result.json", encoding="utf-8"))
    except OSError:
        fail("result.json missing — agent did not record the create/get round-trip")

    name = seed["name"]
    if res.get("created_name") != name:
        fail(f"created_name {res.get('created_name')!r} != seeded {name!r}")
    if res.get("retrieved_name") != name:
        fail(f"retrieved_name {res.get('retrieved_name')!r} != seeded {name!r} — value did not round-trip")
    if not res.get("id"):
        fail("no id captured from the create response")
    print(f"OK: real round-trip verified — created & retrieved {name!r} (id {res['id']})")


if __name__ == "__main__":
    main()
