#!/usr/bin/env python3
"""Verify Download -> typed file variable -> Create -> Upload wiring."""
import glob
import json
import re
import sys

ENTITY = "FileUploadVerify_20260618"
FIELD = "document"
SOURCE_ID = "ECB05DBE-F76A-F111-AC99-000D3A98AF8F"


def main():
    for path in glob.glob("**/*.flow", recursive=True):
        with open(path) as f:
            doc = json.load(f)
        nodes = doc.get("nodes", [])
        typed_files = {
            g.get("id") for g in (doc.get("variables", {}).get("globals") or [])
            if g.get("type") == "file"
        }
        updates = doc.get("variables", {}).get("variableUpdates", {}) or {}
        download = next((n for n in nodes if n.get("type", "").endswith(".download-file-from-record-field")), None)
        create = next((n for n in nodes if n.get("type", "").endswith(".create-entity-record")), None)
        upload = next((n for n in nodes if n.get("type", "").endswith(".upload-file-to-record-field")), None)
        if not download or not create or not upload:
            continue

        def detail(n):
            return n.get("inputs", {}).get("detail", {}) or {}

        for n, label in ((download, "download"), (create, "create"), (upload, "upload")):
            d = detail(n)
            if (d.get("pathParameters") or {}).get("entityName") != ENTITY:
                print(f"FAIL: {label} entity binding is not {ENTITY}", file=sys.stderr)
                return 1

        dd = detail(download)
        if (dd.get("bodyParameters") or {}).get("_fieldName") != FIELD:
            print(f"FAIL: download does not target {FIELD}", file=sys.stderr)
            return 1
        if (dd.get("queryParameters") or {}).get("recordId") != SOURCE_ID:
            print("FAIL: download source recordId is incorrect", file=sys.stderr)
            return 1

        download_id = download.get("id", "")
        assigned = [expr for values in updates.values() for item in values for expr in [item.get("expression")]
                    if download_id in str(expr)]
        if not assigned:
            print("FAIL: download output is not assigned to a workflow variable", file=sys.stderr)
            return 1
        assigned_ids = {item.get("variableId") for values in updates.values() for item in values
                        if download_id in str(item.get("expression"))}
        if not assigned_ids & typed_files:
            print(f"FAIL: download output variables {assigned_ids} are not typed file globals {typed_files}", file=sys.stderr)
            return 1

        ud = detail(upload)
        if (ud.get("bodyParameters") or {}).get("_fieldName") != FIELD:
            print(f"FAIL: upload does not target {FIELD}", file=sys.stderr)
            return 1
        record_id = (ud.get("queryParameters") or {}).get("recordId", "")
        create_id = create.get("id", "")
        if create_id not in str(record_id) and "create" not in str(record_id).lower():
            print(f"FAIL: upload recordId is not bound to create output: {record_id!r}", file=sys.stderr)
            return 1
        multipart = detail(upload).get("multipartParameters") or []
        file_values = [p.get("value") for p in multipart if p.get("name") == "file"]
        if not file_values or not any(any(var in str(v) for var in assigned_ids & typed_files) for v in file_values):
            print(f"FAIL: upload multipart file is not bound to downloaded file variable: {file_values}", file=sys.stderr)
            return 1
        print(f"OK: {path} — download output assigned to typed file variable and reused by upload")
        return 0
    print("FAIL: no complete Data Fabric file round-trip found", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
