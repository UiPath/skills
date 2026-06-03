#!/usr/bin/env python3
"""Validate that every Markdown link in skill files resolves to an existing file.

Usage:
    python3 tests/scripts/check_skill_links.py [--root <repo-root>]

Exit codes:
    0  All links valid
    1  One or more broken links found
    2  Usage error

Scope:
    Walks all *.md files under skills/ (relative to the repo root).
    Checks only relative links that look like file paths.
    Skips:
      - Absolute URLs (http://, https://)
      - Anchor-only links (#section)
      - Skill namespace refs (/uipath:...)
      - Absolute filesystem paths (/tmp/, /Users/, /private/, /)
      - Links containing template placeholders (<...>)
      - Multi-line link targets (code false-positives)
      - mailto: links

Section anchors (#fragment) in the link target are stripped before
checking file existence — they are not validated individually.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Only match single-line [text](href) — avoids false-positives from
# multiline Python constructor calls like Agent(\n    name="x",\n...)
_LINK_RE = re.compile(r"\[(?:[^\]\n]*)\]\(([^)\n]+)\)")


def _should_skip(href: str) -> bool:
    """Return True for hrefs that are not local file references."""
    # URL schemes
    if href.startswith(("http://", "https://", "mailto:")):
        return True
    # Anchor-only
    if href.startswith("#"):
        return True
    # Skill namespace cross-references (/uipath:skill-name)
    if href.startswith("/uipath:"):
        return True
    # Absolute filesystem paths — these appear in docs as examples, not real links
    if href.startswith("/"):
        return True
    # Template placeholders like <ABSOLUTE_PATH> or <slug>
    if "<" in href or ">" in href:
        return True
    # Paths that are clearly code/example content (contain spaces or newlines)
    if " " in href or "\n" in href:
        return True
    # Regex-style hrefs used as illustrative examples (e.g. "error|errorCode")
    if "|" in href:
        return True
    # Generic placeholder segments used in template READMEs (e.g. "path", "...")
    path_part = href.split("#")[0]
    if path_part in ("path", "..."):
        return True
    return False


def _resolve(href: str, source_file: Path) -> Path:
    """Resolve href relative to the source file's directory, stripping fragments."""
    path_part = href.split("#")[0]
    return (source_file.parent / path_part).resolve()


def check(root: Path) -> list[tuple[Path, str, Path]]:
    """Return list of (source_file, raw_href, resolved_path) for broken links."""
    broken: list[tuple[Path, str, Path]] = []
    for md_file in sorted(root.glob("skills/**/*.md")):
        if ".maintenance" in md_file.parts:
            continue
        text = md_file.read_text(encoding="utf-8")
        for match in _LINK_RE.finditer(text):
            href = match.group(1).strip()
            if _should_skip(href):
                continue
            resolved = _resolve(href, md_file)
            if not resolved.exists():
                broken.append((md_file, href, resolved))
    return broken


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=".",
        help="Repo root (default: current directory)",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()

    if not (root / "skills").is_dir():
        print(f"ERROR: skills/ directory not found under {root}", file=sys.stderr)
        sys.exit(2)

    broken = check(root)
    if not broken:
        md_count = sum(1 for _ in root.glob("skills/**/*.md"))
        print(f"OK: all relative links valid across {md_count} skill .md files")
        sys.exit(0)

    print(f"BROKEN LINKS ({len(broken)} found):", file=sys.stderr)
    for source, href, resolved in broken:
        rel_source = source.relative_to(root)
        print(f"  {rel_source}  →  {href!r}", file=sys.stderr)
        print(f"         resolved to: {resolved}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
