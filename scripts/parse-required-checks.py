#!/usr/bin/env python3
"""
Parse the "Current target set" table in docs/REQUIRED-CHECKS.md.

THE single parser for that table. Both consumers go through here:

  - scripts/apply-required-checks.sh, which PUTs the contexts to the ruleset;
  - tests/scripts/test_required_checks_contract.py, which asserts they match
    the workflows.

They used to parse it independently (awk and a Python regex) with different
tolerances, so a row could be applied to the ruleset while being invisible to
the guard, or mangled into a context GitHub waits for forever. One parser makes
that divergence impossible by construction.

Usage:
    parse-required-checks.py              # one "<context>\\t<workflow>" per line
    parse-required-checks.py --contexts   # contexts only, one per line
    parse-required-checks.py --json       # [{"context": ..., "workflow": ...}]
"""

import argparse
import json
import re
import sys
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs" / "REQUIRED-CHECKS.md"
HEADING = "## Current target set"

# A row is `| `<context>` | `<workflow>` |`, optionally with prose after the
# second cell. Both cells MUST be backticked: a half-backticked row is a typo,
# and silently keeping or dropping it is how the two old parsers diverged.
ROW = re.compile(r"^\|\s*`([^`|]+)`\s*\|\s*`([^`|]+)`")

# Any other table row inside the section — matched so a malformed row is an
# error rather than a silent omission. The header and its `|---|---|` separator
# are the only two legitimately unbackticked rows.
ANY_ROW = re.compile(r"^\|")
SEPARATOR = re.compile(r"^\|[\s:|-]+\|?\s*$")


class TableError(RuntimeError):
    pass


def parse(doc: Path = DOC):
    """Return [(context, workflow), ...]. Raises TableError on a malformed table."""
    text = doc.read_text(encoding="utf-8")
    rows, seen_heading, in_table, in_fence = [], False, False, False

    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\r")

        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        if line.startswith(HEADING):
            if seen_heading:
                raise TableError(f"{doc}:{lineno}: duplicate '{HEADING}' heading")
            seen_heading, in_table = True, True
            continue
        if in_table and line.startswith("## "):
            in_table = False
            continue
        if not in_table or not ANY_ROW.match(line):
            continue

        if SEPARATOR.match(line):
            continue

        m = ROW.match(line)
        if m:
            rows.append((m.group(1).strip(), m.group(2).strip()))
            continue

        # The header row is the one unbackticked row we tolerate.
        if line.lower().replace(" ", "").startswith("|check|workflow|"):
            continue

        raise TableError(
            f"{doc}:{lineno}: table row is not `| \\`context\\` | \\`workflow\\` |` "
            f"and is neither the header nor the separator:\n  {line}\n"
            f"Every row must backtick BOTH cells — an unparsed row would be "
            f"silently dropped from the ruleset or applied as a garbage context."
        )

    if not seen_heading:
        raise TableError(f"{doc}: no '{HEADING}' heading found")
    if not rows:
        raise TableError(f"{doc}: '{HEADING}' section parsed zero rows")

    contexts = [c for c, _ in rows]
    dupes = sorted({c for c in contexts if contexts.count(c) > 1})
    if dupes:
        raise TableError(f"{doc}: duplicate context(s) in the table: {dupes}")

    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--contexts", action="store_true", help="print contexts only")
    g.add_argument("--json", action="store_true", help="print JSON objects")
    ap.add_argument("--doc", type=Path, default=DOC, help="table to parse")
    args = ap.parse_args(argv)

    try:
        rows = parse(args.doc)
    except TableError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps([{"context": c, "workflow": w} for c, w in rows], indent=2))
    elif args.contexts:
        for context, _ in rows:
            print(context)
    else:
        for context, workflow in rows:
            print(f"{context}\t{workflow}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
