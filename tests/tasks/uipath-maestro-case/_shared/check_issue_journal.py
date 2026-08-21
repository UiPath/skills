#!/usr/bin/env python3
"""Grade the incremental issue journal — `tasks/build-issues.md`.

Regression guarded
------------------
The issue log used to be accumulated in the agent's reasoning for the whole
build and written once at Step 12.1. On a long build that list is lost to
context pressure before it is ever written, and no Step 12 check reads the log.

Measured on two independent runs of the same task, different models, both of
which produced a caseplan a reviewer would accept:

    claude-sonnet-5   52.4 min   39 placeholder tasks   120 <UNRESOLVED>   NO log
    gpt-5.6-terra      7.2 min   23 placeholder tasks     0 <UNRESOLVED>   NO log

The fix flushes the buffer at every section boundary, so the journal is on disk
from the first section onward. This checker verifies the *incremental* contract,
not merely that some file exists:

  1. When the build carries unresolved work, build-issues.md must exist.
  2. It must carry the `## Journal` section — the append-only audit trail.
  3. The Step 12.1 summary block must be filled, not left at its placeholder.
  4. The journal must carry >= 1 row when there is unresolved work to record.

A reconstructed log (stamped with the NOTE: line) passes 1-3 but is reported,
because it records what the artifacts prove rather than what the build observed.

Exit 0 = pass, 1 = fail. Run from the sandbox root.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SKIP = {".venv", "node_modules", ".npm-prefix", "dist"}

SUMMARY_START = "<!--build-issues:summary:start-->"
SUMMARY_END = "<!--build-issues:summary:end-->"
PLACEHOLDER_SUMMARY = "_Summary written at Step 12.1._"
RECONSTRUCTED = "reconstructed at Step 12.1"


def find_one(root: Path, name: str) -> Path | None:
    for p in root.rglob(name):
        if SKIP.isdisjoint(p.parts):
            return p
    return None


def carries_unresolved(root: Path) -> tuple[bool, str]:
    """Does this build have anything the operator must be told about?"""
    reasons = []

    tasks_md = find_one(root, "tasks.md")
    if tasks_md is not None:
        try:
            n = len(re.findall(r"<UNRESOLVED", tasks_md.read_text()))
            if n:
                reasons.append(f"{n} <UNRESOLVED> marker(s)")
        except OSError:
            pass

    caseplan = find_one(root, "caseplan.json")
    if caseplan is not None:
        try:
            case = json.loads(caseplan.read_text())
        except (OSError, json.JSONDecodeError):
            case = None
        if case:
            ph = 0
            for node in case.get("nodes") or []:
                if node.get("type") != "case-management:Stage":
                    continue
                for lane in (node.get("data") or {}).get("tasks") or []:
                    for task in lane:
                        if not (task.get("data") or {}):
                            ph += 1
            if ph:
                reasons.append(f"{ph} placeholder task(s)")

    return bool(reasons), ", ".join(reasons)


def journal_rows(text: str) -> int:
    """Count data rows in the ## Journal table."""
    m = re.search(r"^##\s+Journal\s*$", text, re.MULTILINE)
    if not m:
        return -1  # section absent
    body = text[m.end():]
    nxt = re.search(r"^##\s+", body, re.MULTILINE)
    if nxt:
        body = body[: nxt.start()]
    rows = 0
    for raw in body.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        if set(line) <= set("|-: "):
            continue
        cells = [c.strip().lower() for c in line.strip("|").split("|")]
        if cells[:1] == ["sev"] or (cells and cells[0] in {"sev", "severity"}):
            continue
        rows += 1
    return rows


def main() -> int:
    root = Path.cwd()
    unresolved, why = carries_unresolved(root)
    print(f"unresolved work: {why or 'none'}")

    issues = find_one(root, "build-issues.md")
    reached_phase2 = find_one(root, "caseplan.json") is not None

    if issues is None:
        if not reached_phase2:
            print("\nPASS: build never reached Phase 2 — no journal expected.")
            return 0
        detail = f" ({why})" if unresolved else " (no unresolved work, but the flush is unconditional)"
        print(
            f"\nFAIL: the build reached Phase 2 but there is NO tasks/build-issues.md{detail}.\n"
            "  The journal is flushed at EVERY section boundary — including sections that\n"
            "  produced zero issues — so the file must exist from the first Phase 2 section\n"
            "  onward, long before Step 12.1. Its absence means the flush never happened.\n"
            "  See plugins/logging/impl-json.md § Flush."
        )
        return 1

    rel = issues.relative_to(root)
    try:
        text = issues.read_text()
    except OSError as exc:
        print(f"\nFAIL: {rel} unreadable: {exc}")
        return 1

    rows = journal_rows(text)
    if rows < 0:
        print(
            f"\nFAIL: {rel} has no '## Journal' section.\n"
            "  The incremental contract requires an append-only journal written at each\n"
            "  section boundary; a single end-of-build dump does not satisfy it."
        )
        return 1

    if rows == 0 and unresolved:
        print(
            f"\nFAIL: {rel} has a Journal section but no rows, while the build carries\n"
            f"  unresolved work ({why}). Every placeholder or unresolved marker is a\n"
            "  SKIPPED entry the operator needs."
        )
        return 1

    if SUMMARY_START in text:
        block = text.split(SUMMARY_START, 1)[1].split(SUMMARY_END, 1)[0]
        if PLACEHOLDER_SUMMARY in block or not block.strip():
            print(
                f"\nFAIL: {rel} still carries the placeholder summary — Step 12.1 did not\n"
                "  fill it from the journal."
            )
            return 1

    print(f"\njournal rows: {rows}")
    if RECONSTRUCTED in text:
        print(
            f"PASS (degraded): {rel} is a RECONSTRUCTED log — the incremental flush was\n"
            "  skipped and the log was rebuilt from artifacts at Step 12.1. Severity and\n"
            "  step attribution are approximate."
        )
        return 0

    print(f"PASS: {rel} carries an incremental journal with {rows} row(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
