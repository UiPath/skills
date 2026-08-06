#!/usr/bin/env python3
"""Verify the fixed file-roundtrip source record is usable.

This is deliberately read-only. The test depends on a pre-existing record
with a populated FILE field and should fail during setup with a clear message
when that tenant fixture is unavailable.
"""
import json
import subprocess
import sys


ENTITY = "FileUploadVerify_20260618"
SOURCE_ID = "ECB05DBE-F76A-F111-AC99-000D3A98AF8F"
FIELD = "document"


def run(*args):
    result = subprocess.run(["uip", *args, "--output", "json"],
                            capture_output=True, text=True)
    if result.returncode:
        print(result.stderr[:1000] or result.stdout[:1000], file=sys.stderr)
        raise SystemExit(result.returncode)
    return json.loads(result.stdout)


def value(obj, *keys):
    for key in keys:
        if obj.get(key) is not None:
            return obj[key]
    return None


def main():
    entities = run("df", "entities", "list", "--include-folders").get("Data") or []
    entity = next((item for item in entities
                   if value(item, "Name", "name", "DisplayName", "displayName") == ENTITY), None)
    if not entity:
        print(f"FAIL: entity {ENTITY!r} is not available", file=sys.stderr)
        return 1

    entity_id = value(entity, "Id", "ID", "id")
    args = ["df", "records", "get", entity_id, SOURCE_ID]
    folder_key = value(entity, "FolderId", "folderId")
    if folder_key:
        args += ["--folder-key", folder_key]
    record = run(*args).get("Data") or {}
    document = value(record, FIELD, FIELD.capitalize())
    if document in (None, "", False):
        print(f"FAIL: {ENTITY}/{SOURCE_ID} exists but its {FIELD!r} field is empty", file=sys.stderr)
        return 1
    print(f"OK: {ENTITY}/{SOURCE_ID} has a populated {FIELD!r} file field")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
