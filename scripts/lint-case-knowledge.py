#!/usr/bin/env python3
"""Deterministic lint for the shared case-knowledge layer and its consumers.

Checks (stdlib only, read-only, exit 0 clean / 1 findings):
  1. K-* rule IDs are defined exactly once (md `**[K-XXX-n]**` markers + facts YAML top-level keys).
  2. Every K-* citation across both skills' case surfaces resolves to a defined ID.
  3. Every .md in case-knowledge/ and case-design/ ends with its exact `<!-- END: <basename> -->` marker.
  4. Size budgets: case-knowledge .md <= 100 lines, facts .yaml <= 90, case-design .md <= 230.
  5. The sanctioned maestro-case symlink exists, is a symlink, and resolves to the planner directory.
  6. Relative links inside case-knowledge/ and case-design/ resolve to existing files.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KN = REPO / "skills/uipath-planner/references/case-knowledge"
CD = REPO / "skills/uipath-planner/references/case-design"
SYMLINK = REPO / "skills/uipath-maestro-case/references/case-knowledge"

# Where K-* citations are expected/allowed to appear.
CITATION_ROOTS = [
    REPO / "skills/uipath-planner/references",
    REPO / "skills/uipath-planner/assets/templates",
    REPO / "skills/uipath-planner/SKILL.md",
    REPO / "skills/uipath-maestro-case/references",
    REPO / "skills/uipath-maestro-case/SKILL.md",
]

K_ID = re.compile(r"\bK-[A-Z]+-\d+\b")
MD_DEF = re.compile(r"\*\*\[(K-[A-Z]+-\d+)\]")
YAML_DEF = re.compile(r"^(K-[A-Z]+-\d+):", re.M)
MD_LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)")

BUDGETS = [(KN, "*.md", 100), (KN, "*.yaml", 90), (CD, "*.md", 230)]


def md_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def main() -> None:
    findings: list[str] = []
    rel = lambda p: p.relative_to(REPO).as_posix()

    if not KN.is_dir():
        sys.exit(f"FATAL: {rel(KN)} missing")

    # 5. Symlink integrity (repo checkout; built trees carry real copies instead).
    if SYMLINK.exists() or SYMLINK.is_symlink():
        if not SYMLINK.is_symlink():
            findings.append(
                f"{rel(SYMLINK)}: expected a symlink to the planner case-knowledge directory "
                "(broken checkout? run: git config core.symlinks true, then re-checkout)"
            )
        elif SYMLINK.resolve() != KN.resolve():
            findings.append(f"{rel(SYMLINK)}: must resolve to {rel(KN)}")
    else:
        findings.append(f"{rel(SYMLINK)}: sanctioned symlink missing")

    # 1. Definitions.
    defined: dict[str, str] = {}
    for path in md_files(KN):
        for match in MD_DEF.finditer(path.read_text(encoding="utf-8")):
            rule_id = match.group(1)
            if rule_id in defined:
                findings.append(f"{rel(path)}: {rule_id} already defined in {defined[rule_id]}")
            defined[rule_id] = rel(path)
    for path in sorted(KN.glob("facts/*.yaml")):
        for match in YAML_DEF.finditer(path.read_text(encoding="utf-8")):
            rule_id = match.group(1)
            if rule_id in defined:
                findings.append(f"{rel(path)}: {rule_id} already defined in {defined[rule_id]}")
            defined[rule_id] = rel(path)
    if not defined:
        findings.append(f"{rel(KN)}: no K-* definitions found")

    # 2. Citations resolve. Skip the symlink (same content as KN).
    def cite_files() -> list[Path]:
        out: list[Path] = []
        for root in CITATION_ROOTS:
            if root.is_file():
                out.append(root)
                continue
            for p in sorted(root.rglob("*")):
                if not p.is_file() or p.suffix not in (".md", ".yaml"):
                    continue
                if SYMLINK in p.parents or p == SYMLINK:
                    continue
                out.append(p)
        return out

    for path in cite_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for cited in sorted(set(K_ID.findall(text))):
            if cited not in defined:
                findings.append(f"{rel(path)}: cites undefined {cited}")

    # 3. END markers.
    for root in (KN, CD):
        if not root.is_dir():
            continue
        for path in md_files(root):
            expected = f"<!-- END: {path.name} -->"
            tail = path.read_text(encoding="utf-8").rstrip().splitlines()[-1].strip()
            if tail != expected:
                findings.append(f"{rel(path)}: last line must be {expected!r} (got {tail!r})")

    # 4. Budgets.
    for root, pattern, cap in BUDGETS:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob(pattern)):
            lines = len(path.read_text(encoding="utf-8").splitlines())
            if lines > cap:
                findings.append(f"{rel(path)}: {lines} lines exceeds the {cap}-line budget — split or tighten")

    # 6. Relative links resolve.
    for root in (KN, CD):
        if not root.is_dir():
            continue
        for path in md_files(root):
            for match in MD_LINK.finditer(path.read_text(encoding="utf-8")):
                target = match.group(1)
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                if not (path.parent / target).resolve().exists():
                    findings.append(f"{rel(path)}: broken relative link {target!r}")

    if findings:
        print("CASE-KNOWLEDGE LINT FAIL:", file=sys.stderr)
        for n, finding in enumerate(findings, 1):
            print(f"  {n}. {finding}", file=sys.stderr)
        sys.exit(1)
    print(f"CASE-KNOWLEDGE LINT OK: {len(defined)} K-* rules, single-definition holds")


if __name__ == "__main__":
    main()
