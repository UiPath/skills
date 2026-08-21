#!/usr/bin/env python3
"""Locate the Flow project's ``.flow`` file dynamically and assert its content.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $SKILLS_REPO_PATH/tests/tasks/uipath-maestro-flow/_shared/flow_contains.py
    python3 .../flow_contains.py '"uipath.human-in-the-loop.quick-form"' '"end"'
    python3 .../flow_contains.py --flow-name VendorApproval '"boolean"'
    python3 .../flow_contains.py --regex '\\$vars\\.[A-Za-z0-9_-]+\\.output'
    python3 .../flow_contains.py --flow-name ContractReview --absent-regex '\\.output\\.legalNotes'

Arguments:
    plain args           substrings that must ALL appear in ONE discovered
                         ``.flow`` file (not split across files)
    --regex PATTERN      Python regex that must match the same single file as
                         the plain args (repeatable) — the path-agnostic
                         replacement for ``file_matches_regex``
    --flow-name NAME     restrict assertions to files named ``NAME.flow``;
                         fails when no discovered file has that basename.
                         Restores the name enforcement the literal paths had,
                         while staying wrapper-agnostic
    --absent-regex PAT   negative assertion: exits 0 only when discovery
                         succeeded, every target file was read, and NO target
                         file matches PAT (repeatable). Use this (with
                         expected_exit_code: 0) instead of inverting a
                         positive check — a bare exit 1 cannot distinguish
                         "pattern absent" from "no flow found"

With no arguments this asserts only that a ``.flow`` file exists. All positive
assertions (substrings + ``--regex``) must be satisfied by a single file;
``--absent-regex`` must hold for every target file.

Why this exists — the ``file_exists`` / ``file_contains`` criterion types take a
literal ``path`` with no glob support, so tasks hardcode
``<Name>/<Name>/<Name>.flow``. That path is brittle: ``uip maestro flow init``
scaffolds a wrapper solution directory whose name the prompt does not pin, so a
correct flow lands at e.g. ``<Name>Solution/<Name>/<Name>.flow`` and the
criterion scores 0.0 purely on the path while the flow itself validates. This is
the same failure ``validate_flow.py`` was added to fix (#2213); it reuses that
module's discovery so both criteria address the same file.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flow_check import find_flow_files  # noqa: E402


def _parse(argv: list[str]):
    substrings: list[str] = []
    regexes: list[str] = []
    absent: list[str] = []
    flow_name: str | None = None
    it = iter(argv)
    for arg in it:
        try:
            if arg == "--regex":
                regexes.append(next(it))
            elif arg == "--absent-regex":
                absent.append(next(it))
            elif arg == "--flow-name":
                flow_name = next(it)
            else:
                substrings.append(arg)
        except StopIteration:
            print(f"FAIL: {arg} requires a value", file=sys.stderr)
            sys.exit(2)
    return substrings, regexes, absent, flow_name


def main(argv: list[str]) -> int:
    substrings, regexes, absent, flow_name = _parse(argv)

    try:
        flows = find_flow_files()
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return exc.code if isinstance(exc.code, int) else 1
    print(f"Found {len(flows)} .flow file(s): {', '.join(flows)}")

    if flow_name is not None:
        targets = [p for p in flows if os.path.basename(p) == f"{flow_name}.flow"]
        if not targets:
            print(
                f"FAIL: no discovered .flow file is named {flow_name}.flow",
                file=sys.stderr,
            )
            return 1
    else:
        targets = flows

    if not substrings and not regexes and not absent:
        return 0

    bodies = {path: open(path, encoding="utf-8").read() for path in targets}

    failed = False
    if substrings or regexes:
        # All positive assertions must hold within ONE file — a project with
        # subflows must not pass by splitting the assertion set across files.
        def satisfies(body: str) -> bool:
            return all(s in body for s in substrings) and all(
                re.search(p, body) for p in regexes
            )

        winner = next((p for p, b in bodies.items() if satisfies(b)), None)
        if winner:
            print(
                f"OK: all {len(substrings) + len(regexes)} assertion(s) "
                f"satisfied by {winner}"
            )
        else:
            failed = True

            def score(body: str) -> int:
                return sum(s in body for s in substrings) + sum(
                    bool(re.search(p, body)) for p in regexes
                )

            best = max(bodies, key=lambda p: score(bodies[p]))
            for s in substrings:
                print(f"{'OK     ' if s in bodies[best] else 'MISSING'} {s}")
            for p in regexes:
                print(
                    f"{'OK     ' if re.search(p, bodies[best]) else 'MISSING'} regex {p}"
                )
            print(
                "FAIL: no single .flow file satisfies the full assertion set "
                f"(closest: {best})",
                file=sys.stderr,
            )

    for p in absent:
        hits = [path for path, b in bodies.items() if re.search(p, b)]
        if hits:
            failed = True
            print(
                f"FAIL: forbidden pattern {p!r} present in: {', '.join(hits)}",
                file=sys.stderr,
            )
        else:
            print(f"OK      absent {p}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
