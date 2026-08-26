#!/usr/bin/env python3
"""
Verify that the Maestro BPMN pattern guides have not drifted from the rest of
the skill.

Pattern guides name extension types, link to sibling guides, and are reached
through a router table in SKILL.md. Each of those is a reference that rots
silently: a renamed extension type, a guide added without a router row, a
heading edited out from under an anchor. None of it is caught by
`skills:validate`, which checks composition rather than content.

Checks:
  1. Extension types named in guides (`Orchestrator.X`, `Actions.X`,
     `Maestro.X`, `Intsvc.X`) exist in the skill's bundled validator spec.
  2. The router table in SKILL.md and the guide files agree: every row points
     at a file that exists, and every guide has a row.
  3. Every relative link in SKILL.md and the guides resolves, including its
     `#anchor` when present.

Exit code is 1 when any finding is reported, 0 otherwise.

Usage:
    python3 scripts/check-pattern-refs.py
    python3 scripts/check-pattern-refs.py --skill skills/uipath-maestro-bpmn
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Every prefix the bundled spec uses. Omitting one makes this check silently
# skip the types it names, which is the rot it exists to prevent.
TYPE_RE = re.compile(r"\b(?:Orchestrator|Actions|Maestro|Intsvc|BPMN|A2A)\.[A-Za-z][A-Za-z0-9]*\b")
LINK_RE = re.compile(r"\]\(([^)]+)\)")
ROUTER_ROW_RE = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|[^|]*\|\s*\[[^\]]+\]\(([^)]+)\)\s*\|", re.M)
HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$", re.M)


def anchor_of(heading: str) -> str:
    return re.sub(r"[^\w\s-]", "", heading.lower()).strip().replace(" ", "-")


def anchors_in(path: Path) -> set[str]:
    return {anchor_of(h) for h in HEADING_RE.findall(path.read_text(encoding="utf-8"))}


def check(skill_dir: Path) -> list[str]:
    findings: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    patterns_dir = skill_dir / "references" / "patterns"
    spec_path = skill_dir / "validator" / "bpmn-spec.json"

    if not patterns_dir.is_dir():
        return findings  # skill has no pattern guides; nothing to check

    guides = sorted(patterns_dir.glob("*-guide.md"))
    docs = [skill_md, *guides]

    # 1. Extension types resolve against the bundled spec.
    if spec_path.is_file():
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        known = set(spec.get("extensionTypes", {}))
        for guide in guides:
            for lineno, line in enumerate(guide.read_text(encoding="utf-8").splitlines(), 1):
                for name in TYPE_RE.findall(line):
                    if name not in known:
                        findings.append(
                            f"{guide}:{lineno}: unknown extension type `{name}` "
                            f"(absent from {spec_path.name}; rename it or stop naming it)"
                        )
    else:
        findings.append(f"{spec_path}: missing — cannot verify extension types")

    # 2. Router rows and guide files agree.
    if skill_md.is_file():
        rows = ROUTER_ROW_RE.findall(skill_md.read_text(encoding="utf-8"))
        routed = {}
        for slug, target in rows:
            resolved = (skill_md.parent / target.split("#", 1)[0]).resolve()
            routed[slug] = resolved
            if not resolved.is_file():
                findings.append(f"SKILL.md: router row `{slug}` points at missing {target}")
            elif resolved.stem != f"{slug}-guide":
                findings.append(
                    f"SKILL.md: router row `{slug}` points at {resolved.name}, "
                    f"expected {slug}-guide.md"
                )
        for guide in guides:
            slug = guide.stem[: -len("-guide")]
            if slug == "composing":
                continue  # reached by prose pointer, not a router row
            if slug not in routed:
                findings.append(f"{guide}: no router row in SKILL.md for `{slug}`")
    else:
        findings.append(f"{skill_md}: missing")

    # 3. Relative links and anchors resolve.
    for doc in docs:
        if not doc.is_file():
            continue
        for link in LINK_RE.findall(doc.read_text(encoding="utf-8")):
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            rel, _, frag = link.partition("#")
            target = (doc.parent / rel).resolve() if rel else doc
            if not target.is_file():
                findings.append(f"{doc}: broken link {link}")
            elif frag and frag not in anchors_in(target):
                findings.append(f"{doc}: broken anchor {link}")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skill",
        default="skills/uipath-maestro-bpmn",
        help="Skill directory to check (default: skills/uipath-maestro-bpmn)",
    )
    args = parser.parse_args()

    findings = check(Path(args.skill))
    for finding in findings:
        print(finding)
    if findings:
        print(f"\n{len(findings)} finding(s).")
        return 1
    print(f"{args.skill}: pattern references OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
