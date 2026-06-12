#!/usr/bin/env python3
"""
Guard cross-skill relative links in skill documentation.

Skills must be self-contained (CLAUDE.md: "No cross-skill references").
A small set of architectural dependencies is tolerated (e.g. Integration
Service specs owned by uipath-platform). This script is a ratchet:

  1. Broken-link check — every cross-skill relative link must resolve to an
     existing file.
  2. Edge allowlist — a link from skill A into skill B's folder is legal only
     if the (A, B) edge is in ALLOWED_EDGES below. New edges fail CI; removing
     links lets you shrink the list, never grow it without review.

Usage:
    python3 scripts/check-cross-skill-links.py            # human-readable, exit 1 on findings
    python3 scripts/check-cross-skill-links.py --json     # newline-delimited JSON
    python3 scripts/check-cross-skill-links.py --list     # print current edges (for allowlist maintenance)
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# Tolerated architectural dependencies (source skill -> target skill).
# Shrinking this list is encouraged; growing it requires review — add a
# justification comment per edge.
ALLOWED_EDGES = {
    # Integration Service specs are owned by uipath-platform; orchestration
    # skills bind connectors against them.
    ("uipath-maestro-case", "uipath-platform"),
    ("uipath-maestro-flow", "uipath-platform"),
    ("uipath-agents", "uipath-platform"),
    ("uipath-rpa", "uipath-platform"),
    # Orchestrator deploy semantics owned by uipath-platform.
    ("uipath-solution", "uipath-platform"),
    # IS spec docs point at the flow-side connector plugin for node authoring.
    ("uipath-platform", "uipath-maestro-flow"),
    # Governance policy authoring requires admin identity/group resolution.
    ("uipath-governance", "uipath-admin"),
    # Publish -> pack -> link -> execute chain spans rpa/solution/test.
    ("uipath-rpa", "uipath-solution"),
    ("uipath-rpa", "uipath-test"),
    ("uipath-test", "uipath-rpa"),
    # HITL surfaces Action Center tasks; URL patterns owned by uipath-tasks.
    ("uipath-human-in-the-loop", "uipath-tasks"),
    # agents <-> maestro-flow agent-node docs are split across both skills.
    # Known cycle — scheduled for ownership consolidation; do not add links.
    ("uipath-agents", "uipath-maestro-flow"),
    ("uipath-maestro-flow", "uipath-agents"),
    # HITL node authoring detail owned by uipath-human-in-the-loop; the
    # maestro-flow hitl plugin defers to it.
    ("uipath-maestro-flow", "uipath-human-in-the-loop"),
    ("uipath-human-in-the-loop", "uipath-maestro-flow"),
}

LINK_RE = re.compile(r"\]\(([^)\s]+?\.md)(?:#[^)\s]*)?\)")


def skill_of(path: Path):
    """Return the uipath-* skill folder name containing path, or None."""
    try:
        rel = path.resolve().relative_to(SKILLS_DIR.resolve())
    except ValueError:
        return None
    return rel.parts[0] if rel.parts else None


def find_findings():
    findings = []
    for md in sorted(SKILLS_DIR.rglob("*.md")):
        source_skill = skill_of(md)
        text = md.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for match in LINK_RE.finditer(line):
                target_rel = match.group(1)
                if target_rel.startswith(("http://", "https://")):
                    continue
                target = (md.parent / target_rel).resolve()
                target_skill = skill_of(target)
                if target_skill is None or target_skill == source_skill:
                    continue
                rel_md = md.relative_to(REPO_ROOT).as_posix()
                if not target.exists():
                    findings.append({
                        "kind": "broken",
                        "file": rel_md,
                        "line": lineno,
                        "link": target_rel,
                        "edge": [source_skill, target_skill],
                    })
                elif (source_skill, target_skill) not in ALLOWED_EDGES:
                    findings.append({
                        "kind": "new-edge",
                        "file": rel_md,
                        "line": lineno,
                        "link": target_rel,
                        "edge": [source_skill, target_skill],
                    })
    return findings


def list_edges():
    edges = {}
    for md in sorted(SKILLS_DIR.rglob("*.md")):
        source_skill = skill_of(md)
        text = md.read_text(encoding="utf-8", errors="replace")
        for match in LINK_RE.finditer(text):
            target_rel = match.group(1)
            if target_rel.startswith(("http://", "https://")):
                continue
            target = (md.parent / target_rel).resolve()
            target_skill = skill_of(target)
            if target_skill and target_skill != source_skill:
                edges.setdefault((source_skill, target_skill), 0)
                edges[(source_skill, target_skill)] += 1
    return edges


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="newline-delimited JSON output")
    parser.add_argument("--list", action="store_true", help="print current cross-skill edges with link counts")
    args = parser.parse_args()

    if args.list:
        for (src, dst), count in sorted(list_edges().items()):
            print(f"{src} -> {dst}: {count}")
        return 0

    findings = find_findings()
    if args.json:
        for f in findings:
            print(json.dumps(f))
    else:
        for f in findings:
            edge = f"{f['edge'][0]} -> {f['edge'][1]}"
            if f["kind"] == "broken":
                print(f"BROKEN  {f['file']}:{f['line']} -> {f['link']} ({edge})")
            else:
                print(f"NEW EDGE  {f['file']}:{f['line']} -> {f['link']} ({edge}) — "
                      f"not in ALLOWED_EDGES; skills must be self-contained")
        if findings:
            print(f"\n{len(findings)} finding(s).", file=sys.stderr)
        else:
            print("OK — all cross-skill links resolve and stay within allowed edges.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
