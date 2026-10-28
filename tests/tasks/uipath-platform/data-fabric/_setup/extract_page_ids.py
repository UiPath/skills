#!/usr/bin/env python3
"""Extract record IDs from a Data Fabric list/query response on stdin."""

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--no-pagination", action="store_true")
    args = parser.parse_args()

    try:
        response = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"FAIL: stdin is not valid JSON: {exc}", file=sys.stderr)
        return 1

    data = response.get("Data") if isinstance(response, dict) else None
    if not isinstance(data, dict):
        print("FAIL: response is missing Data", file=sys.stderr)
        return 1

    records = data.get("Items") or data.get("Records") or data.get("records")
    if not isinstance(records, list):
        print("FAIL: response is missing Data.Items/Records", file=sys.stderr)
        return 1

    ids = [
        str(record.get("Id") or record.get("ID") or record.get("id"))
        for record in records
        if isinstance(record, dict)
        and (record.get("Id") or record.get("ID") or record.get("id"))
    ]
    mode = "a" if args.append else "w"
    with args.out.open(mode, encoding="utf-8") as handle:
        if ids:
            handle.write("\n".join(ids) + "\n")

    summary: dict[str, object] = {
        "Result": response.get("Result"),
        "IdCount": len(ids),
    }
    if not args.no_pagination:
        cursor = data.get("NextCursor")
        if isinstance(cursor, dict):
            cursor = cursor.get("Value") or cursor.get("value")
        summary["HasNextPage"] = data.get("HasNextPage", bool(cursor))
        summary["NextCursor"] = cursor
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
