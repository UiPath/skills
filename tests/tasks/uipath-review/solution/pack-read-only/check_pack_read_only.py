#!/usr/bin/env python3
"""Grade the read-only contract of a solution review by its outcome.

`uip solution pack` without `--dry-run` writes into the solution it packs
(`resources/solution_folder/`, `.local/`, `.objects/`, `.project/`), even when
the pack fails. A review must leave the solution exactly as it found it.

PASS requires:
  * `_review_report.md` exists (>= 500 bytes), AND
  * every file of the fixture is still present and byte-identical, AND
  * no file was added to the solution.

The pristine copy is the fixture next to this script (reached through
$REFERENCE_DIR, invisible to the agent). Managed caches a validation command
may create inside a project are ignored: any path with a `.local` segment.
"""
import hashlib
import os
import sys
from pathlib import Path

SOLUTION = "OrderEnrichSolution"
IGNORED_SEGMENTS = {".local"}
MIN_REPORT_BYTES = 500


def snapshot(root: Path) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if IGNORED_SEGMENTS & set(rel.parts) or rel.name == ".DS_Store":
            continue
        out[rel.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main() -> None:
    cwd = Path(os.getcwd())
    report = cwd / "_review_report.md"
    if not report.is_file():
        sys.exit(f"FAIL: {report} not found")
    if report.stat().st_size < MIN_REPORT_BYTES:
        sys.exit(f"FAIL: {report} is suspiciously short ({report.stat().st_size} bytes).")

    pristine = Path(__file__).resolve().parent / "fixture" / SOLUTION
    actual = cwd / SOLUTION
    if not pristine.is_dir():
        sys.exit(f"FAIL: pristine fixture not found at {pristine} (grader setup error).")
    if not actual.is_dir():
        sys.exit(f"FAIL: {actual} not found — the solution under review was removed.")

    want, got = snapshot(pristine), snapshot(actual)
    added = sorted(set(got) - set(want))
    removed = sorted(set(want) - set(got))
    changed = sorted(k for k in want if k in got and want[k] != got[k])
    if added or removed or changed:
        lines = [f"FAIL: the review modified {SOLUTION}/ (read-only contract, Critical Rule 1)."]
        for label, items in (("added", added), ("removed", removed), ("changed", changed)):
            if items:
                lines.append(f"  {label}: {', '.join(items[:12])}" + (" ..." if len(items) > 12 else ""))
        lines.append("  `uip solution pack` without --dry-run writes into the solution; "
                     "the review must use `uip solution pack <dir> --dry-run`.")
        sys.exit("\n".join(lines))

    print(f"OK: {len(want)} files in {SOLUTION}/ are byte-identical to the fixture; nothing added")
    print("PASS")


if __name__ == "__main__":
    main()
