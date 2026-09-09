#!/usr/bin/env python3
"""Seed deterministic records for the FlowCodeEvalEntity query smoke.

The setup is idempotent: if the sentinel record is already present, no rows
are added. The Flow under test remains read-only; this mutation is confined to
the pre_run fixture setup.
"""
import json
import subprocess
import sys


ENTITY = "FlowCodeEvalEntity"
SENTINEL = "FilterFixture-Matrix"
ROWS = [
    {
        "title": SENTINEL,
        "description": "A sci-fi fixture record for filter coverage.",
        "score": 9.2,
        "viewCount": 5000,
        "active": True,
        "releaseDate": "1999-03-31",
        "lastUpdated": "2024-01-01T10:00:00",
        "externalId": "11111111-1111-1111-1111-111111111111",
    },
    {
        "title": "FilterFixture-Arrival",
        "description": "A drama fixture record for filter coverage.",
        "score": 8.5,
        "viewCount": 3000,
        "active": True,
        "releaseDate": "2016-11-11",
        "lastUpdated": "2024-06-15T12:00:00",
        "externalId": "22222222-2222-2222-2222-222222222222",
    },
    {
        "title": "FilterFixture-Solaris",
        "description": "A classic fixture record for filter coverage.",
        "score": 8.0,
        "viewCount": 2000,
        "active": False,
        "releaseDate": "1972-05-13",
        "lastUpdated": "2023-05-13T09:30:00",
        "externalId": "33333333-3333-3333-3333-333333333333",
    },
    {
        "title": "FilterFixture-NullDescription",
        "description": None,
        "score": 6.5,
        "viewCount": 100,
        "active": False,
        "releaseDate": "2020-01-01",
        "lastUpdated": "2022-01-01T00:00:00",
        "externalId": "44444444-4444-4444-4444-444444444444",
    },
]


def run(*args):
    result = subprocess.run(["uip", *args, "--output", "json"],
                            capture_output=True, text=True)
    if result.returncode:
        print(result.stderr[:1000] or result.stdout[:1000], file=sys.stderr)
        raise SystemExit(result.returncode)
    return json.loads(result.stdout)


def first_value(obj, *keys):
    for key in keys:
        if obj.get(key) is not None:
            return obj[key]
    return None


def main():
    entities = run("df", "entities", "list", "--include-folders").get("Data") or []
    entity = next((e for e in entities
                   if first_value(e, "Name", "name", "DisplayName", "displayName") == ENTITY), None)
    if not entity:
        print(f"FAIL: entity {ENTITY!r} was not found after ensure_entity", file=sys.stderr)
        return 1

    entity_id = first_value(entity, "Id", "ID", "id")
    folder_key = first_value(entity, "FolderId", "folderId")
    args = ["df", "records", "list", entity_id, "--limit", "100"]
    if folder_key:
        args += ["--folder-key", folder_key]
    items = (run(*args).get("Data") or {}).get("Items") or []
    if any(first_value(row, "title", "Title") == SENTINEL for row in items):
        print(f"OK: {ENTITY} already contains the query fixture")
        return 0

    insert_args = ["df", "records", "insert", entity_id, "--body", json.dumps(ROWS)]
    if folder_key:
        insert_args += ["--folder-key", folder_key]
    run(*insert_args)
    print(f"OK: seeded {len(ROWS)} deterministic records in {ENTITY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
