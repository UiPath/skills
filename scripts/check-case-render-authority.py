#!/usr/bin/env python3
"""Fail when the case render contracts and the SDD template disagree about SHAPE.

Authority split (declared in `references/case/principles.md`):

    the TEMPLATE is the shape      — headings, column lists, section numbering
    the references are SEMANTICS   — what belongs in a cell, and why

Both currently describe shape, with no tiebreaker, so an agent that satisfies one
must violate the other. The existing gates cannot see this: the template conformance
gate checks that headings EXIST, never that two documents AGREE, so contradictions
pass every check and ship.

What this catches:

  1. A stage/task heading format asserted in a reference that the template does not use.
  2. A pipe-delimited column list asserted in a reference with no matching table
     header in the template.

Read-only. Exit 0 clean, 1 on findings.

    python3 scripts/check-case-render-authority.py [--json]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "skills/uipath-planner/assets/templates/case-sdd-template.md"
RENDER_DOCS = [
    REPO / "skills/uipath-planner/references/case/render-stages-tasks.md",
    REPO / "skills/uipath-planner/references/case/render-case-definition.md",
]

# A heading shape claim: a backticked `### Stage {N}: {Stage Name}`-ish string.
HEADING_CLAIM = re.compile(r"`(#{3,5}\s+[^`]+)`")
# A column-list claim: a backticked run containing at least two pipes.
COLUMN_CLAIM = re.compile(r"`([^`\n]*\|[^`\n]*\|[^`\n]*)`")
# A rendered markdown table header row in the template.
TABLE_HEADER = re.compile(r"^\|(.+)\|\s*$", re.M)

# Placeholder syntaxes differ between the docs ({N} / <N>) without being a conflict.
PLACEHOLDER = re.compile(r"[<{][^<>{}]*[>}]")


def normalize_heading(s: str) -> str:
    s = s.strip().rstrip(".")
    s = PLACEHOLDER.sub("*", s)
    s = re.sub(r"\\`|`", "", s)
    return re.sub(r"\s+", " ", s).strip()


OPTIONAL_COL = re.compile(r"\(\s*\|[^)]*\)")


def normalize_columns(s: str) -> tuple[str, ...]:
    # `Field | Type | Binding (| Required)` documents an OPTIONAL column; the
    # parenthetical is notation, not a cell. Treating it as one produced a false
    # conflict against a template that defines both variants.
    s = OPTIONAL_COL.sub("", s)
    cells = [c.strip().strip("`").strip() for c in s.strip().strip("|").split("|")]
    cells = [PLACEHOLDER.sub("*", c) for c in cells if c]
    return tuple(c.lower() for c in cells)


def template_facts(text: str) -> tuple[set[str], set[tuple[str, ...]]]:
    headings = {
        normalize_heading(line)
        for line in text.splitlines()
        if re.match(r"^#{3,5}\s+\S", line)
    }
    # The template also pins some heading shapes in HTML comments / inline backticks
    # (secondary-stage task numbering, for one). Those are definitions too — not
    # counting them made the checker report a conflict that does not exist.
    headings |= {normalize_heading(m) for m in HEADING_CLAIM.findall(text)}
    columns: set[tuple[str, ...]] = set()
    for m in TABLE_HEADER.finditer(text):
        row = m.group(1)
        if set(row.replace("|", "").strip()) <= set("-: "):
            continue  # separator row
        cols = normalize_columns(row)
        if len(cols) >= 2:
            columns.add(cols)
    return headings, columns


def scan(doc: pathlib.Path, headings: set[str], columns: set[tuple[str, ...]]) -> list[dict]:
    findings: list[dict] = []
    if not doc.is_file():
        return [{"file": str(doc), "line": 0, "kind": "missing", "claim": "", "detail": "file not found"}]
    text = doc.read_text(encoding="utf-8")

    for m in HEADING_CLAIM.finditer(text):
        claim = normalize_heading(m.group(1))
        if not claim.startswith("#"):
            continue
        if claim in headings:
            continue
        # Only flag stage/task headings — those are the shape the template owns.
        if not re.search(r"\b(Stage|Task)\b", claim):
            continue
        findings.append({
            "file": str(doc.relative_to(REPO)),
            "line": text[: m.start()].count("\n") + 1,
            "kind": "heading",
            "claim": m.group(1).strip(),
            "detail": "asserted in a render contract but not used by the template",
        })

    for m in COLUMN_CLAIM.finditer(text):
        cols = normalize_columns(m.group(1))
        if len(cols) < 3:
            continue
        if cols in columns:
            continue
        findings.append({
            "file": str(doc.relative_to(REPO)),
            "line": text[: m.start()].count("\n") + 1,
            "kind": "columns",
            "claim": m.group(1).strip(),
            "detail": "column list has no matching table header in the template",
        })
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not TEMPLATE.is_file():
        print(f"FAIL: template not found at {TEMPLATE}", file=sys.stderr)
        return 1

    headings, columns = template_facts(TEMPLATE.read_text(encoding="utf-8"))
    findings: list[dict] = []
    for doc in RENDER_DOCS:
        findings.extend(scan(doc, headings, columns))

    if args.json:
        print(json.dumps({"findings": findings}, indent=2))
        return 1 if findings else 0

    print(f"template: {TEMPLATE.relative_to(REPO)} — {len(headings)} headings, {len(columns)} table shapes")
    if not findings:
        print("OK: render contracts assert no shape the template does not define")
        return 0

    print(f"\nFAIL: {len(findings)} shape conflict(s) between the render contracts and the template:\n",
          file=sys.stderr)
    for f in findings:
        print(f"  {f['file']}:{f['line']}  [{f['kind']}]", file=sys.stderr)
        print(f"      {f['claim']}", file=sys.stderr)
        print(f"      {f['detail']}", file=sys.stderr)
    print(
        "\n  The template is the shape; the references are the semantics.\n"
        "  Move the heading/column definition into the template, or replace the\n"
        "  claim with a pointer to it. See references/case/principles.md.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
