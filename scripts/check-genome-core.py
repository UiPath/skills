#!/usr/bin/env python3
"""Check that the genome checker is byte-identical in uipath-planner and uipath-genome-builder.

uipath-planner writes genomes and uipath-genome-builder builds them. Each skill is installed on its own, so
each ships its own copy of scripts/check-genome.py: the planner runs it after every genome write,
the builder before anything is asked. It is the only file the two skills share; the canonical copy
lives in skills/uipath-planner/ (skills/uipath-genome-builder/CLAUDE.md Rule 18). This script names the
copy that is missing or differs.

Usage:
  python3 scripts/check-genome-core.py          # check, exit 1 on any difference
  python3 scripts/check-genome-core.py --fix    # copy the canonical file over uipath-genome-builder's copy

Exit 0 when the copies are identical, 1 otherwise.
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CANONICAL = REPO / "skills" / "uipath-planner"
COPY = REPO / "skills" / "uipath-genome-builder"
SHARED = ("scripts/check-genome.py",)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fix", action="store_true", help="copy the canonical file over uipath-genome-builder's copy")
    args = parser.parse_args(argv)

    failures = []
    for rel in SHARED:
        source, target = CANONICAL / rel, COPY / rel
        if not source.is_file():
            failures.append(f"FAIL: canonical {source.relative_to(REPO)} is missing")
        elif args.fix:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        elif not target.is_file():
            failures.append(f"FAIL: {target.relative_to(REPO)} is missing (copy of {source.relative_to(REPO)})")
        elif source.read_bytes() != target.read_bytes():
            failures.append(f"FAIL: {target.relative_to(REPO)} differs from {source.relative_to(REPO)}")

    for line in failures:
        print(line)
    if failures:
        print("Edit skills/uipath-planner/scripts/check-genome.py, then run: python3 scripts/check-genome-core.py --fix")
        return 1
    print(f"OK - {len(SHARED)} shared file identical in uipath-planner and uipath-genome-builder.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
