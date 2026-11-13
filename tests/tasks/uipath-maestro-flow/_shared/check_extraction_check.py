#!/usr/bin/env python3
"""Grade the order of `uip` calls around the Extract document availability check.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_extraction_check.py [--log PATH] <CHECK>

Reads the call log the extraction-check shim writes
(``_setup/extraction_check_shim``): one ``uip <argv>`` line per call, in the
order they ran, quotes stripped. Default ``--log`` is ``.uip-cmdlog``.

Checks:
    ran            ``uip maestro flow extraction check`` ran
    before-node    it ran, an Extract document node was created with
                   ``uip maestro flow nodes create|add``, and the first check
                   came before the first such create
    searched-ixp   a ``uip maestro flow registry search|list`` naming ``ixp``
                   ran, the fallback's look for a published IXP model

Exit 0 and ``OK: ...`` on stdout when the check holds. Otherwise exit 1 and a
``FAIL: ...`` line on stderr naming what was found instead.
"""

from __future__ import annotations

import argparse
import re
import sys

CHECK = re.compile(r"\bmaestro\s+flow\s+extraction\s+check\b")
CREATE_NODE = re.compile(
    r"\bmaestro\s+flow\s+nodes\s+(?:create|add)\b.*\buipath\.ixp\.extract-document-builder\b"
)
IXP_SEARCH = re.compile(r"\bmaestro\s+flow\s+registry\s+(?:search|list)\b.*ixp", re.I)


def _first(lines: list[str], pattern: re.Pattern[str]) -> int | None:
    for index, line in enumerate(lines):
        if pattern.search(line):
            return index
    return None


def run(check: str, lines: list[str]) -> tuple[bool, str]:
    checked = _first(lines, CHECK)
    if check == "ran":
        if checked is None:
            return False, f"no 'maestro flow extraction check' among {len(lines)} uip call(s)"
        return True, f"extraction check ran (call {checked + 1})"
    if check == "before-node":
        created = _first(lines, CREATE_NODE)
        if checked is None:
            return False, "no 'maestro flow extraction check' ran"
        if created is None:
            return False, "no Extract document node was created with 'maestro flow nodes create'"
        if checked > created:
            return False, f"the node was created at call {created + 1}, before the check at call {checked + 1}"
        return True, f"check at call {checked + 1}, node created at call {created + 1}"
    if check == "searched-ixp":
        searched = _first(lines, IXP_SEARCH)
        if searched is None:
            return False, "no 'maestro flow registry search|list' for an IXP model ran"
        return True, f"looked for a published IXP model (call {searched + 1})"
    raise ValueError(f"unknown check {check!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--log", default=".uip-cmdlog")
    parser.add_argument("check", choices=["ran", "before-node", "searched-ixp"])
    args = parser.parse_args(argv)
    try:
        with open(args.log, encoding="utf-8") as handle:
            lines = [line.rstrip("\n") for line in handle if line.strip()]
    except FileNotFoundError:
        lines = []
    ok, detail = run(args.check, lines)
    if ok:
        print(f"OK: {detail}")
        return 0
    print(f"FAIL: {detail}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
