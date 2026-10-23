#!/usr/bin/env python3
"""Check that the genome shared core is byte-identical in uipath-genome and uipath-planner.

uipath-planner writes genomes and uipath-genome builds them; both read the same format rules and
run the same checker. The canonical copy lives in skills/uipath-genome/, the planner holds a copy
at the same relative path (skills/uipath-planner/CLAUDE.md § Shared core). This script names every
copy that is missing or differs, and that no core file links outside the core.

Usage:
  python3 scripts/check-genome-core.py          # check, exit 1 on any difference
  python3 scripts/check-genome-core.py --fix    # copy each canonical file over the planner's copy

Exit 0 when every copy is identical and every core link stays inside the core, 1 otherwise.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CANONICAL = REPO / "skills" / "uipath-genome"
COPY = REPO / "skills" / "uipath-planner"
CORE = (
    "references/genome-format-guide.md",
    "references/extracted-genome-guide.md",
    "references/transactional-shape-guide.md",
    "references/skill-mapping-guide.md",
    "references/parts-guide.md",
    "references/uipath-source-guide.md",
    "scripts/check-genome.py",
)
# A core file may link to another core file and to SKILL.md (its § Read Plans and § Source
# Frameworks, which both skills keep); anything else is named by its subject.
ALLOWED_TARGETS = {Path(p).name for p in CORE if p.endswith(".md")} | {"../SKILL.md"}
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fix", action="store_true", help="copy canonical files over the planner's copies")
    args = parser.parse_args(argv)

    failures = []
    for rel in CORE:
        source, target = CANONICAL / rel, COPY / rel
        if not source.is_file():
            failures.append(f"FAIL: canonical {source.relative_to(REPO)} is missing")
            continue
        if args.fix:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        elif not target.is_file():
            failures.append(f"FAIL: {target.relative_to(REPO)} is missing (copy of {source.relative_to(REPO)})")
        elif source.read_bytes() != target.read_bytes():
            failures.append(f"FAIL: {target.relative_to(REPO)} differs from {source.relative_to(REPO)}")
        if rel.endswith(".md"):
            for link in LINK.findall(source.read_text(encoding="utf-8")):
                if link.startswith(("http://", "https://")) or link in ALLOWED_TARGETS:
                    continue
                failures.append(f"FAIL: {source.relative_to(REPO)} links outside the shared core: {link}")

    for line in failures:
        print(line)
    if failures:
        print("Edit the canonical copy in skills/uipath-genome/, then run: python3 scripts/check-genome-core.py --fix")
        return 1
    print(f"OK - {len(CORE)} shared core files identical in uipath-genome and uipath-planner.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
