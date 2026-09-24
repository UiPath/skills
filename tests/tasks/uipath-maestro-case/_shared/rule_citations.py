#!/usr/bin/env python3
"""Resolve every `Rule N` citation in the case skill to the TITLE it lands on.

Numbers are the fragile part: inserting a rule mid-list shifts every citation
at or above it onto a DIFFERENT EXISTING rule, silently (measured: an insertion
at Rule 4 moved 205 of 224 citations). The number still resolves, so a
dangling-number check stays green. Titles are stable under renumbering, so a
title-keyed snapshot is invisible to a correct renumber and loud about an
incorrect one.

Regenerate the snapshot after deliberately changing what a document cites:

    python3 tests/tasks/uipath-maestro-case/_shared/rule_citations.py \
        > tests/tasks/uipath-maestro-case/_shared/rule_citations.json

The diff is the review: every line is a claim about what a doc points at.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL = "uipath-maestro-case"
SKILL_DIR = REPO_ROOT / "skills" / SKILL
FLAVOR_ROOT = REPO_ROOT / "skill-flavors"
SNAPSHOT = Path(__file__).with_name("rule_citations.json")

# `Rule N` preceded by a condition-name word (`Entry Rule 1`, `SLA Rule 1`) is a
# NAME, not a citation. Code spans can't be excluded wholesale:
# `…placeholder task per Rule 9` sits in one and is a real citation.
CITATION_RE = re.compile(r"(?<!\bEntry )(?<!\bExit )(?<!\bComplete )(?<!\bCompletion )"
                         r"(?<!\bSLA )(?<!\bCase )(?<!\bStage )\bRule (\d+)\b")
RULES_SECTION_RE = re.compile(r"^## Critical Rules\s*$(.*?)(?=^## )", re.M | re.S)
RULE_RE = re.compile(r"^(\d+)\. \*\*(.+?)\*\*", re.M)
# Same contract as scripts/compose-skill-flavor.mjs MARKER_LINE_RE: column 1,
# whole line, no whitespace.
MARKER_RE = re.compile(r"^<!--skill-flavor:([a-z0-9]+(?:-[a-z0-9]+)*):(start|end)-->\r?\n?$")


def rule_titles(skill_md: str) -> dict[int, str]:
    section = RULES_SECTION_RE.search(skill_md)
    if not section:
        raise ValueError("no `## Critical Rules` section")
    return {int(n): title.rstrip(".") for n, title in RULE_RE.findall(section.group(1))}


def citations(text: str) -> list[int]:
    return [int(n) for n in CITATION_RE.findall(text)]


def citation_map(tree: dict[str, str]) -> dict[str, dict[str, int]]:
    """{relative path: {cited title: count}} for one skill tree."""
    titles = rule_titles(tree["SKILL.md"])
    out: dict[str, dict[str, int]] = {}
    for rel in sorted(tree):
        counts: dict[str, int] = {}
        for n in citations(tree[rel]):
            title = titles.get(n, f"<<UNRESOLVED Rule {n}>>")
            counts[title] = counts.get(title, 0) + 1
        if counts:
            out[rel] = dict(sorted(counts.items()))
    return out


def _blocks(text: str) -> list[tuple[str, int, int]]:
    """(name, start, end) character spans of complete marker blocks."""
    blocks, opened, offset, start = [], None, 0, 0
    for line in text.splitlines(keepends=True):
        m = MARKER_RE.match(line)
        if m:
            name, edge = m.groups()
            if edge == "start":
                opened, start = name, offset
            elif opened == name:
                blocks.append((name, start, offset + len(line)))
                opened = None
        offset += len(line)
    return blocks


def _strip_markers(text: str) -> str:
    return "".join(l for l in text.splitlines(keepends=True) if not MARKER_RE.match(l))


def compose(canonical: str, override: str | None) -> str:
    """Mirror of composeText + stripMarkerBoundaries: replace each named
    canonical block with the override's block of the same name, then drop the
    marker lines."""
    if override is None:
        return _strip_markers(canonical)
    repl = {name: override[s:e] for name, s, e in _blocks(override)}
    pieces, cursor = [], 0
    for name, s, e in _blocks(canonical):
        pieces += [canonical[cursor:s], repl.get(name, canonical[s:e])]
        cursor = e
    pieces.append(canonical[cursor:])
    return _strip_markers("".join(pieces))


def built_trees() -> dict[str, dict[str, str]]:
    """{variant: {relative .md path: composed text}} for default and every flavor."""
    canonical = {p.relative_to(SKILL_DIR).as_posix(): p.read_text(encoding="utf-8")
                 for p in SKILL_DIR.rglob("*.md")}
    trees = {"default": {rel: compose(text, None) for rel, text in canonical.items()}}
    flavors = sorted(d for d in FLAVOR_ROOT.iterdir() if d.is_dir()) if FLAVOR_ROOT.is_dir() else []
    for flavor in flavors:
        root = flavor / SKILL
        tree = {}
        for rel, text in canonical.items():
            o = root / rel
            tree[rel] = compose(text, o.read_text(encoding="utf-8") if o.is_file() else None)
        trees[flavor.name] = tree
    return trees


def canonical_citation_map() -> dict[str, dict[str, int]]:
    return citation_map({p.relative_to(SKILL_DIR).as_posix(): p.read_text(encoding="utf-8")
                         for p in SKILL_DIR.rglob("*.md")})


if __name__ == "__main__":
    json.dump(canonical_citation_map(), sys.stdout, indent=2)
    sys.stdout.write("\n")
