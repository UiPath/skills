#!/usr/bin/env python3
"""Check that the genome core is byte-identical in uipath-planner and uipath-genome-builder.

uipath-planner writes genomes (author, extract, edit) and uipath-genome-builder builds them (build). Each
skill is installed on its own and may not read the other's files, so both ship the genome core: the format
guides, the shared source-frameworks guide, the genome templates and the checker. The canonical copies live
in skills/uipath-planner/ (its CLAUDE.md § Genome core); this script names every copy that is missing or
differs, and --fix copies the canonical files over the builder's.

A core file links only to other core files or to SKILL.md (both skills have one); a guide outside the core
is named by its skill and file name, never linked, so every link resolves in both skills.

Usage:
  python3 scripts/check-genome-core.py          # check, exit 1 on any difference
  python3 scripts/check-genome-core.py --fix    # copy the canonical files over uipath-genome-builder's copies

Exit 0 when the copies are identical, 1 otherwise.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CANONICAL = REPO / "skills" / "uipath-planner"
COPY = REPO / "skills" / "uipath-genome-builder"
CORE = (
    "references/genome-format-guide.md",
    "references/extracted-genome-guide.md",
    "references/transactional-shape-guide.md",
    "references/skill-mapping-guide.md",
    "references/uipath-source-guide.md",
    "references/parts-guide.md",
    "references/source-frameworks-guide.md",
    "assets/templates/component-genome-template.md",
    "assets/templates/process-genome-template.md",
    "scripts/check-genome.mjs",
)
LINK = re.compile(r"\]\((?:\./)?([^)#\s]+\.md)(?:#[^)]*)?\)")


def read(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fix", action="store_true", help="copy the canonical files over uipath-genome-builder's copies")
    args = parser.parse_args(argv)

    failures = []
    core_names = {Path(rel).name for rel in CORE}
    for rel in CORE:
        source, target = CANONICAL / rel, COPY / rel
        if not source.is_file():
            failures.append(f"FAIL: canonical {source.relative_to(REPO).as_posix()} is missing")
            continue
        if rel.endswith(".md"):
            for link in LINK.findall(source.read_text(encoding="utf-8")):
                name = Path(link).name
                if name not in core_names and name != "SKILL.md":
                    failures.append(f"FAIL: {rel} links {link}, which only one skill has — name it by skill and file instead")
        if args.fix:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        elif not target.is_file():
            failures.append(f"FAIL: {target.relative_to(REPO).as_posix()} is missing (run with --fix)")
        elif read(source) != read(target):
            failures.append(f"FAIL: {target.relative_to(REPO).as_posix()} differs from the planner's copy (run with --fix)")
    for failure in failures:
        print(failure)
    if not failures:
        print(f"OK - {len(CORE)} genome core files identical in uipath-planner and uipath-genome-builder.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
