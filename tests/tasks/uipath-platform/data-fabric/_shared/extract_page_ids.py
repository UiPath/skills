#!/usr/bin/env python3
"""Extract record IDs from a `uip df records list|query` JSON response on stdin.

Writes one ID per line to ``--out`` and prints a compact JSON summary to
stdout: ``{Result, IdCount, HasNextPage, NextCursor}``. The summary keeps
the per-page Bash response under ~250 bytes so cursor walks across many
pages do not bloat the agent's context.

Usage:
    uip df records list <id> --limit 60 --output json \\
      | extract_page_ids.py --out walk_ids.txt --append

    uip df records list <id> --limit 60 --offset 180 --output json \\
      | extract_page_ids.py --out offset_page_ids.txt --no-pagination

Arguments:
    --out PATH         File to write IDs to (one per line). Required.
    --append           Append to ``--out`` instead of overwriting.
    --no-pagination    Omit ``HasNextPage`` / ``NextCursor`` from stdout
                       (use for offset jumps where pagination is irrelevant).

Exit code:
    0 on success. 1 if stdin is not a valid Data Fabric response (missing
    ``Data.Records``).
"""

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", required=True, help="File to write IDs to (one per line)")
    parser.add_argument("--append", action="store_true", help="Append instead of overwrite")
    parser.add_argument(
        "--no-pagination",
        action="store_true",
        help="Omit HasNextPage/NextCursor from stdout (for offset jumps)",
    )
    args = parser.parse_args()

    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"FAIL: stdin is not valid JSON: {e}", file=sys.stderr)
        return 1

    inner = data.get("Data")
    if not isinstance(inner, dict) or "Records" not in inner:
        print(f"FAIL: response missing Data.Records (Result={data.get('Result')!r})", file=sys.stderr)
        return 1

    ids = [r["Id"] for r in inner["Records"] if "Id" in r]

    mode = "a" if args.append else "w"
    with open(args.out, mode) as f:
        if ids:
            f.write("\n".join(ids) + "\n")

    summary = {"Result": data.get("Result"), "IdCount": len(ids)}
    if not args.no_pagination:
        summary["HasNextPage"] = inner.get("HasNextPage", False)
        summary["NextCursor"] = inner.get("NextCursor")

    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
